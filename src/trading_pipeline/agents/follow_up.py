"""Agent 5 — follow-up loop over accepted positions.

Each ``tick`` runs cheap tripwire checks (deterministic: price vs stop/target, new
*material* news) on every open position. A tripwire raises an alert, and an alert
triggers a deep LLM full re-review; so does ``full_review_interval`` elapsing.

Alerts have a cooldown (``alert_cooldown``, 12h by default): after an alert, anything
that trips for the same position is recorded but held, then delivered together with
the next alert once the cooldown expires, so nothing material is lost.

An external scheduler calls ``tick``. It flags; it never closes or trades.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ..config import PipelineConfig
from ..data.base import DataProviders, DataSnapshot, PriceBar, RawDataBundle
from ..profile import HORIZONS, InvestorProfile
from ..rules import is_material, levels_hit
from ..schemas import FullReviewOutput, Position, Stage, StageRecord, TripwireResult
from ..store import Store
from .base import StageAgent


def check_tripwires(position: Position, bars: list[PriceBar], news: DataSnapshot | None,
                    now: datetime, trigger: str = "close") -> TripwireResult:
    plan = position.plan
    reasons: list[str] = []
    last = bars[-1].close if bars else None
    if bars:
        stop_hit, target_hit = levels_hit(plan, bars[-1], trigger)
        basis = "closed" if trigger == "close" else "traded"
        if stop_hit:
            reasons.append(f"price {basis} through stop {plan.stop_loss} (last close {last})")
        if target_hit:
            reasons.append(f"price {basis} at/through target {plan.target_price} (last close {last})")
    # Only material news trips the wire; routine headlines and price chatter are noise.
    if news is not None and not news.is_gap and isinstance(news.payload, list):
        for e in news.payload:
            material, why = is_material(e)
            if material:
                reasons.append(f"material news ({why}): {str(e.get('headline', ''))[:120]}")
    return TripwireResult(position_id=position.id, checked_at=now, tripped=bool(reasons),
                          reasons=reasons, last_price=last)


class FullReviewer(StageAgent):
    stage = Stage.FOLLOW_UP_FULL_REVIEW
    role = """\
Follow-Up Full Re-Review. A position the user accepted is open. Re-examine it from
scratch with fresh data: is the original thesis still intact, does the technical plan
still hold? Recommend hold, adjust_plan (with an updated plan), or exit. Any updated
plan must still fit the investor profile (horizon, max loss, reward:risk, direction).
You advise; the user decides and executes."""

    async def run(self, position: Position, original: list[StageRecord], tripwire: TripwireResult,
                  bundle: RawDataBundle, profile: InvestorProfile) -> FullReviewOutput:
        trail = "\n".join(r.model_dump_json(exclude={"output"}) for r in original)
        prompt = (
            f"As of {bundle.as_of.isoformat()}. Position: {position.ticker}, opened "
            f"{position.opened_at.isoformat()}.\n\n"
            f"<investor_profile>\n{profile.prompt_view()}\n</investor_profile>\n\n"
            f"<current_plan>\n{position.plan.model_dump_json(indent=1)}\n</current_plan>\n\n"
            f"<original_reasoning>\n{trail}\n</original_reasoning>\n\n"
            f"<tripwire_check>\n{tripwire.model_dump_json(indent=1)}\n</tripwire_check>\n\n"
            f"<raw_data>\n{bundle.to_prompt()}\n</raw_data>"
        )
        return await self._ask(prompt, FullReviewOutput)


class FollowUpEvent(BaseModel):
    position_id: str
    ticker: str
    tripwire: TripwireResult
    review: FullReviewOutput | None = None
    # Set when the user should act, e.g. close the position and run review_position.
    action_needed: str | None = None


class FollowUpLoop:
    def __init__(self, reviewer: FullReviewer, data: DataProviders, store: Store, config: PipelineConfig) -> None:
        self._reviewer = reviewer
        self._data = data
        self._store = store
        self._config = config

    async def tick(self, now: datetime) -> list[FollowUpEvent]:
        events = []
        for position in self._store.open_positions():
            events.append(await self._check(position, now))
        return events

    async def _check(self, position: Position, now: datetime) -> FollowUpEvent:
        prev = self._store.last_tripwire(position.id)
        since = prev.checked_at if prev else position.opened_at
        bars = await self._data.prices.bars(position.ticker, position.opened_at.date(), now)
        news = await self._data.news.events(position.ticker, since, now)

        tripwire = check_tripwires(position, bars, news, now, self._config.profile.level_trigger)
        self._apply_cooldown(position, tripwire, now)
        self._store.save_tripwire(tripwire)
        event = FollowUpEvent(position_id=position.id, ticker=position.ticker, tripwire=tripwire)

        last_full = position.last_full_review_at or position.opened_at
        if tripwire.alerted or now - last_full >= self._config.full_review_interval:
            event.review = await self._full_review(position, tripwire, news, now)
        if tripwire.alerted and bars:
            stop_hit, target_hit = levels_hit(position.plan, bars[-1], self._config.profile.level_trigger)
            if stop_hit or target_hit:
                level = "stop" if stop_hit else "target"
                event.action_needed = (f"{position.ticker} hit its {level}. If you exited, record it with "
                                       f"close_position and then run review_position.")
            elif event.review is not None and event.review.action == "exit":
                event.action_needed = (f"Re-review recommends exiting {position.ticker}. If you exit, record it "
                                       f"with close_position and then run review_position.")
        return event

    def _apply_cooldown(self, position: Position, tripwire: TripwireResult, now: datetime) -> None:
        history = self._store.tripwires(position.id)
        last_alert = max((t.checked_at for t in history if t.alerted), default=None)
        held = [t for t in history if t.tripped and not t.alerted
                and (last_alert is None or t.checked_at > last_alert)]
        if not (tripwire.tripped or held):
            return
        if last_alert is not None and now - last_alert < self._config.alert_cooldown:
            return  # within cooldown: recorded, not alerted
        tripwire.alerted = True
        for t in held:
            for reason in t.reasons:
                note = f"(held during cooldown, {t.checked_at.isoformat()}) {reason}"
                if reason not in tripwire.reasons and note not in tripwire.reasons:
                    tripwire.reasons.append(note)

    async def _full_review(self, position: Position, tripwire: TripwireResult, news: DataSnapshot,
                           now: datetime) -> FullReviewOutput:
        bundle = RawDataBundle(as_of=now)
        bundle.extend(await self._data.macro.macro(now))
        for chart in HORIZONS[position.plan.horizon].charts:
            bundle.extend([
                await self._data.prices.ohlcv(position.ticker, (now - chart.lookback).date(), now, chart.interval),
                await self._data.prices.indicators(position.ticker, now, chart.interval),
                await self._data.prices.pivots(position.ticker, now, chart.interval),
            ])
        bundle.extend([
            await self._data.fundamentals.fundamentals(position.ticker, now),
            await self._data.filings.recent_filings(position.ticker, position.opened_at, now),
            await self._data.news.upcoming_earnings(position.ticker, now),
            news,
        ])
        self._store.save_snapshots(bundle.snapshots)

        original = self._store.stage_records(candidate_id=position.candidate_id)
        review = await self._reviewer.run(position, original, tripwire, bundle, self._config.profile)
        self._store.save_stage_record(StageRecord(
            run_id=position.run_id, stage=Stage.FOLLOW_UP_FULL_REVIEW, subject=position.ticker,
            position_id=position.id, verdict=review.action, reasoning=review.reasoning,
            output=review.model_dump(mode="json"), raw_data_ids=bundle.ids, as_of=now,
        ))
        position.last_full_review_at = now
        self._store.save_position(position)
        return review
