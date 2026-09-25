"""Middleware: runs the stages, carries raw data forward, logs reasoning, reports to the user.

It is strictly one-directional toward the user. The user's accept/reject is recorded
only to decide what enters the follow-up watch list; it is never fed back into any
stage or review as if it were the system's own judgment.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from datetime import datetime, timedelta
from typing import TypeVar

from .agents.company_deep_dive import CompanyDeepDive
from .agents.follow_up import FollowUpLoop, FullReviewer
from .agents.market_scanner import MarketScanner
from .agents.outcomes import compute_outcome
from .agents.process_review import ProcessReviewer
from .agents.sector_deep_dive import SectorDeepDive
from .agents.technical_analysis import TechnicalAnalyst
from .config import PipelineConfig
from .data.base import DataProviders, DataSnapshot, RawDataBundle
from .llm import LLMClient
from .rules import check_earnings, check_plan, check_stale_entry
from .schemas import (
    Candidate,
    CompanyDeepDiveOutput,
    Conflict,
    ImprovementNote,
    OutcomeReport,
    PipelineReport,
    Position,
    ProcessReviewOutput,
    Recommendation,
    Rejection,
    RuleResult,
    SectorCall,
    ShortlistEntry,
    Stage,
    StageReasoning,
    StageRecord,
    TechnicalOutput,
    UserDecision,
    new_id,
    utcnow,
)
from .store import Store

log = logging.getLogger(__name__)

T = TypeVar("T")

class Middleware:
    def __init__(self, config: PipelineConfig, llm: LLMClient, data: DataProviders, store: Store) -> None:
        self.config = config
        self._llm = llm
        self._data = data
        self._store = store
        self._sem = asyncio.Semaphore(config.max_parallel)

    def _lessons(self, stage: Stage) -> list[str]:
        return [n.text for n in self._store.improvements(stage=stage, approved_only=True)]

    async def _limited(self, coro: Awaitable[T]) -> T:
        async with self._sem:
            return await coro

    # ----------------------------------------------------------------------------------
    # Pipeline run
    # ----------------------------------------------------------------------------------

    async def run(self, as_of: datetime, *, live: bool = True) -> PipelineReport:
        """Run Agent 0 → Agent 1 → Company Deep Dive → Technical. ``live=False`` for backtests
        (skips live quotes, which cannot be point-in-time)."""
        run_id = new_id()
        cfg = self.config
        show_conf = cfg.show_upstream_confidence
        scanner = MarketScanner(self._llm, self._lessons(Stage.MARKET_SCAN))
        sector_agent = SectorDeepDive(self._llm, self._lessons(Stage.SECTOR_DEEP_DIVE))
        company_agent = CompanyDeepDive(self._llm, self._lessons(Stage.COMPANY_DEEP_DIVE))
        tech_agent = TechnicalAnalyst(self._llm, self._lessons(Stage.TECHNICAL))
        rejections: list[Rejection] = []

        # -- Agent 0 ---------------------------------------------------------------------
        market_bundle = RawDataBundle(as_of=as_of)
        market_bundle.extend(await self._data.sectors.market_overview(as_of))
        # Macro data is market-level, so it reaches every stage (foreseeable-risk checks).
        market_bundle.extend(await self._data.macro.macro(as_of))
        self._store.save_snapshots(market_bundle.snapshots)
        scan = await scanner.run(market_bundle)
        for call in scan.sectors:
            self._log(run_id, Stage.MARKET_SCAN, call.sector, call.direction, call.reasoning, call,
                      market_bundle, as_of)
        pursued = scan.sectors
        if cfg.max_sectors is not None and len(pursued) > cfg.max_sectors:
            ranked = sorted(pursued, key=lambda c: c.reasoning.confidence, reverse=True)
            pursued = ranked[: cfg.max_sectors]
            for call in ranked[cfg.max_sectors:]:
                rejections.append(Rejection(ticker=call.sector, stage=Stage.MARKET_SCAN,
                                            summary=f"not pursued: run limited to {cfg.max_sectors} sector(s)"))

        # -- Agent 1: one independent pass per sector ---------------------------------------
        async def sector_pass(call: SectorCall):
            bundle = RawDataBundle(as_of=as_of, snapshots=list(market_bundle.snapshots))
            # Bulk screen for every company in the sector; deep per-company data comes later,
            # only for the shortlist (design decision: bulk screen at Agent 1, deep later).
            bundle.extend(await self._data.sectors.sector_screen(call.sector, as_of))
            bundle.extend([
                await self._data.sectors.sector_breadth(call.sector, as_of),
                await self._data.news.events(call.sector, as_of - timedelta(days=90), as_of),
            ])
            self._store.save_snapshots(bundle.snapshots)
            out = await self._limited(sector_agent.run(call, bundle, show_confidence=show_conf))
            return self._select_shortlist(out.shortlist), bundle

        candidates: list[tuple[Candidate, SectorCall, RawDataBundle]] = []
        conflicts: list[Conflict] = []
        surfaced: dict[str, tuple[str, str]] = {}  # ticker -> first (sector, direction)
        advanced: set[str] = set()
        results = await asyncio.gather(*(sector_pass(c) for c in pursued), return_exceptions=True)
        for call, result in zip(pursued, results):
            if isinstance(result, BaseException):
                log.exception("sector deep dive failed for %s", call.sector, exc_info=result)
                rejections.append(Rejection(ticker=call.sector, stage=Stage.SECTOR_DEEP_DIVE, summary=f"error: {result}"))
                continue
            (forward, dropped), bundle = result
            for entry in dropped:
                self._log(run_id, Stage.SECTOR_DEEP_DIVE, entry.ticker, "not_forwarded", entry.reasoning,
                          entry, bundle, as_of)
            for entry in forward:
                direction = "long" if call.direction == "upside" else "short"
                # Same ticker from several sector calls: always record it; opposite
                # directions are a conflict, same direction a duplicate. First one advances.
                first = surfaced.setdefault(entry.ticker, (call.sector, direction))
                if first != (call.sector, direction):
                    conflict = Conflict(
                        run_id=run_id, ticker=entry.ticker,
                        kind="direction_conflict" if first[1] != direction else "duplicate",
                        first_sector=first[0], first_direction=first[1],
                        other_sector=call.sector, other_direction=direction)
                    conflicts.append(conflict)
                    self._store.save_conflict(conflict)
                if direction == "short" and not cfg.profile.allow_short:
                    rule = RuleResult(rule="profile_short", outcome="reject",
                                      message="investor profile does not allow short positions")
                    self._log(run_id, Stage.SECTOR_DEEP_DIVE, entry.ticker, "rejected_by_rule", entry.reasoning,
                              entry, bundle, as_of, rules=[rule])
                    rejections.append(Rejection(ticker=entry.ticker, stage=Stage.SECTOR_DEEP_DIVE,
                                                summary=f"rule {rule.rule}: {rule.message}"))
                    continue
                if entry.ticker in advanced:
                    continue
                advanced.add(entry.ticker)
                cand = Candidate(run_id=run_id, ticker=entry.ticker, company_name=entry.company_name,
                                 sector=call.sector, direction=direction, shortlist=entry)
                cand.record_confidence(Stage.SECTOR_DEEP_DIVE, entry.reasoning.confidence)
                self._log(run_id, Stage.SECTOR_DEEP_DIVE, entry.ticker, "forwarded", entry.reasoning, entry,
                          bundle, as_of, candidate_id=cand.id)
                candidates.append((cand, call, bundle))

        # -- Company deep dive: one independent pass per company -----------------------------
        async def company_pass(cand: Candidate, call: SectorCall, upstream: RawDataBundle):
            # Relevant-subset pass-through: market-level data plus everything about this
            # company and its sector, but not other companies' screen rows.
            bundle = upstream.filter(subjects={cand.sector, cand.ticker})
            bundle.extend([
                await self._data.fundamentals.fundamentals(cand.ticker, as_of),
                await self._data.filings.recent_filings(cand.ticker, as_of - timedelta(days=365), as_of),
                await self._data.news.events(cand.ticker, as_of - timedelta(days=180), as_of),
            ])
            self._store.save_snapshots(bundle.snapshots)
            out = await self._limited(company_agent.run(cand.shortlist, call, bundle, show_confidence=show_conf))
            return out, bundle

        survivors: list[tuple[Candidate, CompanyDeepDiveOutput, RawDataBundle]] = []
        results = await asyncio.gather(*(company_pass(*c) for c in candidates), return_exceptions=True)
        for (cand, _, _), result in zip(candidates, results):
            if isinstance(result, BaseException):
                self._fail(cand, Stage.COMPANY_DEEP_DIVE, result, rejections)
                continue
            out, bundle = result
            self._log(run_id, Stage.COMPANY_DEEP_DIVE, cand.ticker, out.verdict, out.reasoning, out, bundle,
                      as_of, candidate_id=cand.id)
            if self._advance(cand, Stage.COMPANY_DEEP_DIVE, out.verdict, out.reasoning, rejections):
                survivors.append((cand, out, bundle))

        # -- Technical analysis: independent per company, no cross-comparison ---------------
        async def technical_pass(cand: Candidate, company: CompanyDeepDiveOutput, upstream: RawDataBundle):
            bundle = RawDataBundle(as_of=as_of, snapshots=list(upstream.snapshots))
            # One chart per timeframe the investor's horizons need (e.g. swing: 1d + 1w).
            for chart in cfg.profile.charts():
                bundle.extend([
                    await self._data.prices.ohlcv(cand.ticker, (as_of - chart.lookback).date(), as_of, chart.interval),
                    await self._data.prices.indicators(cand.ticker, as_of, chart.interval),
                    await self._data.prices.pivots(cand.ticker, as_of, chart.interval),
                ])
            earnings = await self._data.news.upcoming_earnings(cand.ticker, as_of)
            bundle.add(earnings)
            self._store.save_snapshots(bundle.snapshots)
            out = await self._limited(tech_agent.run(cand, company, bundle, profile=cfg.profile,
                                                     show_confidence=show_conf))
            return out, bundle, earnings

        recommendations: list[Recommendation] = []
        results = await asyncio.gather(*(technical_pass(*s) for s in survivors), return_exceptions=True)
        for (cand, company, _), result in zip(survivors, results):
            if isinstance(result, BaseException):
                self._fail(cand, Stage.TECHNICAL, result, rejections)
                continue
            out, bundle, earnings = result
            verdict = out.verdict
            if verdict == "pass" and out.plan is None:
                log.warning("technical pass without a plan for %s; treating as reject", cand.ticker)
                verdict = "reject"

            rules: list[RuleResult] = []
            quote = None
            if verdict == "pass":
                quote = await self._live_quote(cand.ticker) if live else None
                price, source = (quote, "live") if quote is not None else (await self._last_close(cand.ticker, as_of), "last close")
                rules = [*check_plan(out.plan, cfg.profile),
                         check_stale_entry(out.plan, price, cfg.stale_entry_max_drift_pct, source=source),
                         check_earnings(out.plan, earnings, as_of)]
                if any(r.outcome == "reject" for r in rules):
                    verdict = "rejected_by_rule"

            self._log(run_id, Stage.TECHNICAL, cand.ticker, verdict, out.reasoning, out, bundle, as_of,
                      candidate_id=cand.id, rules=rules)
            if verdict == "rejected_by_rule":
                cand.record_confidence(Stage.TECHNICAL, out.reasoning.confidence)
                cand.reject(Stage.TECHNICAL)
                msgs = "; ".join(f"rule {r.rule}: {r.message}" for r in rules if r.outcome == "reject")
                rejections.append(Rejection(ticker=cand.ticker, stage=Stage.TECHNICAL, summary=msgs))
                continue
            if self._advance(cand, Stage.TECHNICAL, verdict, out.reasoning, rejections):
                cand.status = "recommended"
                recommendations.append(Recommendation(
                    candidate=cand, company=company, technical=out, live_quote=quote,
                    flags=[r for r in rules if r.outcome == "flag"]))

        for cand, _, _ in candidates:
            self._store.save_candidate(cand)

        return PipelineReport(run_id=run_id, as_of=as_of, market=scan, recommendations=recommendations,
                              rejections=rejections, conflicts=conflicts)

    def _select_shortlist(self, shortlist: list[ShortlistEntry]) -> tuple[list[ShortlistEntry], list[ShortlistEntry]]:
        """Apply the Agent 1 format decision (ranked by default). Returns (forwarded, not forwarded)."""
        cfg = self.config
        passed = [e for e in shortlist if e.passed]
        if cfg.confidence_gate is not None:
            passed = [e for e in passed if e.reasoning.confidence >= cfg.confidence_gate]
        if cfg.shortlist_mode == "ranked":
            passed.sort(key=lambda e: e.potential_score, reverse=True)
        forward = passed[: cfg.shortlist_max_per_sector]
        forwarded_ids = {id(e) for e in forward}
        return forward, [e for e in shortlist if id(e) not in forwarded_ids]

    def _advance(self, cand: Candidate, stage: Stage, verdict: str, reasoning: StageReasoning,
                 rejections: list[Rejection]) -> bool:
        cand.record_confidence(stage, reasoning.confidence)
        gate = self.config.confidence_gate
        if verdict != "pass" or (gate is not None and reasoning.confidence < gate):
            cand.reject(stage)
            rejections.append(Rejection(ticker=cand.ticker, stage=stage, summary=reasoning.summary))
            return False
        return True

    def _fail(self, cand: Candidate, stage: Stage, err: BaseException, rejections: list[Rejection]) -> None:
        log.error("%s failed for %s: %r", stage.value, cand.ticker, err)
        cand.reject(stage)
        rejections.append(Rejection(ticker=cand.ticker, stage=stage, summary=f"error: {err}"))

    def _log(self, run_id: str, stage: Stage, subject: str, verdict: str, reasoning: StageReasoning, output,
             bundle: RawDataBundle, as_of: datetime, *, candidate_id: str | None = None,
             rules: list[RuleResult] | None = None) -> None:
        self._store.save_stage_record(StageRecord(
            run_id=run_id, stage=stage, subject=subject, candidate_id=candidate_id, verdict=verdict,
            reasoning=reasoning, output=output.model_dump(mode="json"), raw_data_ids=bundle.ids,
            rules=rules or [], as_of=as_of,
        ))

    async def _last_close(self, ticker: str, as_of: datetime) -> float | None:
        bars = await self._data.prices.bars(ticker, (as_of - timedelta(days=10)).date(), as_of, "1d")
        return bars[-1].close if bars else None

    async def _live_quote(self, ticker: str) -> float | None:
        try:
            snap = await self._data.quotes.quote(ticker)
        except Exception:  # visibility only; never block a report on it
            log.warning("live quote unavailable for %s", ticker, exc_info=True)
            return None
        payload = snap.payload
        if isinstance(payload, dict):
            price = payload.get("price") or payload.get("last_trade_price")
            return float(price) if price is not None else None
        return float(payload) if isinstance(payload, (int, float)) else None

    # ----------------------------------------------------------------------------------
    # Human decision boundary
    # ----------------------------------------------------------------------------------

    def record_decision(self, candidate_id: str, accepted: bool, note: str = "",
                        opened_at: datetime | None = None) -> Position | None:
        """Record the user's go/no-go. Accepted candidates enter the Agent 5 watch list.
        The decision itself is stored in isolation and never reaches any agent."""
        cand = self._store.candidate(candidate_id)
        if cand is None or cand.status != "recommended":
            raise ValueError(f"{candidate_id} is not a recommended candidate")
        if self._store.user_decision_for(candidate_id) is not None:
            raise ValueError(f"a decision was already recorded for {candidate_id}")
        self._store.save_user_decision(UserDecision(candidate_id=candidate_id, accepted=accepted, note=note))
        if not accepted:
            return None
        tech = next(r for r in self._store.stage_records(candidate_id=candidate_id) if r.stage == Stage.TECHNICAL)
        plan = TechnicalOutput.model_validate(tech.output).plan
        assert plan is not None
        position = Position(run_id=cand.run_id, candidate_id=cand.id, ticker=cand.ticker, sector=cand.sector,
                            plan=plan, opened_at=opened_at or utcnow())
        self._store.save_position(position)
        return position

    def close_position(self, position_id: str, exit_price: float, closed_at: datetime) -> Position:
        position = self._store.position(position_id)
        if position is None:
            raise KeyError(position_id)
        position.status, position.exit_price, position.closed_at = "closed", exit_price, closed_at
        self._store.save_position(position)
        return position

    # ----------------------------------------------------------------------------------
    # Follow-up and retrospective review
    # ----------------------------------------------------------------------------------

    def follow_up_loop(self) -> FollowUpLoop:
        reviewer = FullReviewer(self._llm, self._lessons(Stage.FOLLOW_UP_FULL_REVIEW))
        return FollowUpLoop(reviewer, self._data, self._store, self.config)

    async def review_position(self, position_id: str, now: datetime) -> tuple[OutcomeReport, ProcessReviewOutput]:
        """Outcomes agent (facts) then process agent (reasoning quality). Improvement
        suggestions are stored unapproved; a human approves them before they reach prompts."""
        position = self._store.position(position_id)
        if position is None:
            raise KeyError(position_id)
        if self._store.process_review(position_id) is not None:
            raise ValueError(f"position {position_id} was already reviewed")
        end = position.closed_at or now
        bars = await self._data.prices.bars(position.ticker, position.opened_at.date(), end)
        outcome = compute_outcome(position, bars, now, self.config.profile.level_trigger)
        self._store.save_outcome(outcome)

        trail = self._store.review_trail(position)
        raw_ids = dict.fromkeys(i for r in trail for i in r.raw_data_ids)
        raw = [s for s in (self._store.snapshot(i) for i in raw_ids) if isinstance(s, DataSnapshot)]
        review = await ProcessReviewer(self._llm).run(position.ticker, trail, raw, outcome)
        self._store.save_process_review(position.id, review)
        for s in review.improvements:
            self._store.save_improvement(ImprovementNote(source_position_id=position.id,
                                                         target_stage=s.target_stage, text=s.suggestion))
        return outcome, review


def render_report(report: PipelineReport) -> str:
    """Plain-text report for the user."""
    lines = [f"Pipeline run {report.run_id} — as of {report.as_of.isoformat()}", "",
             f"Market: {report.market.market_summary}", ""]
    for s in report.market.sectors:
        lines.append(f"  [{s.direction}] {s.sector}: {s.thesis}")
    lines += ["", f"Recommendations ({len(report.recommendations)}):"]
    for r in report.recommendations:
        p = r.technical.plan
        traj = " → ".join(f"{c.stage.value}:{c.confidence:.2f}" for c in r.candidate.confidence_trajectory)
        lines += [
            f"- {r.candidate.ticker} ({r.candidate.sector}, {r.candidate.direction})  candidate_id={r.candidate.id}",
            f"    thesis: {r.company.thesis}",
            f"    setup:  {r.technical.setup}",
        ]
        if p:
            lines.append(f"    plan:   entry {p.entry_price} ({p.entry_condition}), target {p.target_price}, "
                         f"stop {p.stop_loss}, {p.horizon} ({p.chart_timeframe} chart)")
        if r.live_quote is not None:
            lines.append(f"    live quote: {r.live_quote}")
        for f in r.flags:
            lines.append(f"    ⚠ {f.rule}: {f.message}")
        lines.append(f"    confidence trajectory: {traj}")
    lines += ["", f"Rejected ({len(report.rejections)}):"]
    lines += [f"- {x.ticker} at {x.stage.value}: {x.summary}" for x in report.rejections]
    if report.conflicts:
        lines += ["", f"Conflicts ({len(report.conflicts)}):"]
        lines += [f"- {c.ticker}: {c.kind} — {c.first_sector} ({c.first_direction}) vs "
                  f"{c.other_sector} ({c.other_direction})" for c in report.conflicts]
    lines += ["", "You make the call. Record it with: trading-pipeline decide CANDIDATE_ID accept|reject [--note TEXT]"]
    return "\n".join(lines)
