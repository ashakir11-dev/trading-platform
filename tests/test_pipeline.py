from datetime import timedelta

import pytest

from trading_pipeline import Middleware, PipelineConfig, Store, render_report
from trading_pipeline.data.base import DataSnapshot, LookaheadError, RawDataBundle
from trading_pipeline.schemas import (
    CompanyDeepDiveOutput,
    ImprovementNote,
    MarketScanOutput,
    ProcessReviewOutput,
    SectorDeepDiveOutput,
    Stage,
    TechnicalOutput,
)

from .fakes import AS_OF, FixturePrices, FixtureSectors, ScriptedLLM, make_bars, providers


def build(config: PipelineConfig | None = None, **data):
    llm = ScriptedLLM()
    store = Store()
    mw = Middleware(config or PipelineConfig(), llm, providers(**data), store)
    return mw, llm, store


async def test_end_to_end_flow_and_technical_rejection():
    mw, llm, store = build()
    report = await mw.run(AS_OF)

    # CCC failed at Agent 1; AAA and BBB pass company dive; BBB rejected on the chart.
    assert [r.candidate.ticker for r in report.recommendations] == ["AAA"]
    assert {(x.ticker, x.stage) for x in report.rejections} == {("BBB", Stage.TECHNICAL)}
    assert len(llm.prompts(CompanyDeepDiveOutput)) == 2
    assert len(llm.prompts(TechnicalOutput)) == 2

    rec = report.recommendations[0]
    assert [p.stage for p in rec.candidate.confidence_trajectory] == [
        Stage.SECTOR_DEEP_DIVE, Stage.COMPANY_DEEP_DIVE, Stage.TECHNICAL]
    assert rec.live_quote == 101.5

    # Every stage's reasoning is logged, including the entry Agent 1 filtered out.
    stages = {(r.stage, r.subject, r.verdict) for r in store.stage_records(run_id=report.run_id)}
    assert (Stage.SECTOR_DEEP_DIVE, "CCC", "not_forwarded") in stages
    assert (Stage.MARKET_SCAN, "Biotech", "upside") in stages
    assert "AAA" in render_report(report)


async def test_backtest_mode_skips_live_quotes():
    mw, _, _ = build()
    report = await mw.run(AS_OF, live=False)
    assert report.recommendations[0].live_quote is None


async def test_raw_data_passes_through_to_later_stages():
    mw, llm, _ = build()
    await mw.run(AS_OF)
    tech_prompt = next(p for p in llm.prompts(TechnicalOutput) if "Company: AAA" in p)
    # Upstream raw data (sector breadth from Agent 1's inputs, market data from Agent 0,
    # the fundamentals gap from the company stage) reaches the technical agent.
    for kind in ("sector_breadth", "sector_performance", "fundamentals", "ohlcv:1d", "ohlcv:1w", "earnings_calendar"):
        assert f'"kind": "{kind}"' in tech_prompt
    assert "UNAVAILABLE" in tech_prompt  # gaps are explicit, not silently empty


async def test_company_prompts_carry_only_relevant_raw_data():
    mw, llm, _ = build()
    await mw.run(AS_OF)
    # Agent 1 screens the whole sector.
    sector_prompt = llm.prompts(SectorDeepDiveOutput)[0]
    assert all(f"SCREEN-{t}" in sector_prompt for t in ("AAA", "BBB", "CCC"))
    # Company and technical prompts keep market + sector data and their own row only.
    for output in (CompanyDeepDiveOutput, TechnicalOutput):
        prompt = next(p for p in llm.prompts(output) if "Company: AAA" in p)
        assert "SCREEN-AAA" in prompt and "SCREEN-BBB" not in prompt
        assert '"kind": "sector_breadth"' in prompt and '"kind": "sector_performance"' in prompt


async def test_upstream_confidence_hidden_by_default():
    mw, llm, _ = build()
    await mw.run(AS_OF)
    assert '"confidence"' not in llm.prompts(CompanyDeepDiveOutput)[0]

    mw, llm, _ = build(PipelineConfig(show_upstream_confidence=True))
    await mw.run(AS_OF)
    assert '"confidence"' in llm.prompts(CompanyDeepDiveOutput)[0]


async def test_shortlist_modes():
    mw, llm, _ = build(PipelineConfig(shortlist_mode="ranked", shortlist_max_per_sector=1))
    await mw.run(AS_OF)
    # Ranked: only the top-scoring passing entry (BBB, 90) is forwarded.
    assert ["Company: BBB" in p for p in llm.prompts(CompanyDeepDiveOutput)] == [True]

    mw, llm, _ = build(PipelineConfig(shortlist_mode="pass_fail"))
    await mw.run(AS_OF)
    assert len(llm.prompts(CompanyDeepDiveOutput)) == 2


async def test_confidence_gate_is_optional():
    mw, _, _ = build(PipelineConfig(confidence_gate=0.6))
    report = await mw.run(AS_OF)
    # Technical confidence 0.55 < 0.6, so AAA is gated out when the gate is on.
    assert report.recommendations == []


async def test_lookahead_is_rejected():
    bundle = RawDataBundle(as_of=AS_OF)
    with pytest.raises(LookaheadError):
        bundle.add(DataSnapshot(kind="x", source="t", subject="m", as_of=AS_OF + timedelta(seconds=1)))

    mw, _, _ = build(sectors=FixtureSectors(future_leak=True))
    with pytest.raises(LookaheadError):
        await mw.run(AS_OF)


async def test_single_candidate_failure_does_not_abort_run():
    mw, llm, _ = build()
    original = llm.handlers[TechnicalOutput]

    def flaky(prompt):
        if "Company: BBB" in prompt:
            raise RuntimeError("boom")
        return original(prompt)

    llm.handlers[TechnicalOutput] = flaky
    report = await mw.run(AS_OF)
    assert [r.candidate.ticker for r in report.recommendations] == ["AAA"]
    assert any(x.ticker == "BBB" and x.summary.startswith("error") for x in report.rejections)


async def test_user_decision_never_reaches_process_review():
    bars = make_bars([100, 104, 110, 118], AS_OF + timedelta(hours=1))
    mw, llm, store = build(prices=FixturePrices({"AAA": bars}))
    report = await mw.run(AS_OF)
    cand_id = report.recommendations[0].candidate.id

    secret = "USER-GUT-FEELING-7f3a"
    position = mw.record_decision(cand_id, accepted=True, note=secret, opened_at=AS_OF + timedelta(hours=1))
    assert position is not None and position.plan.stop_loss == 90.0

    outcome, review = await mw.review_position(position.id, now=bars[-1].ts)
    assert outcome.return_pct == pytest.approx(18.0)
    prompt = llm.prompts(ProcessReviewOutput)[0]
    assert secret not in prompt and "accepted" not in prompt
    # The trail includes Agent 0's call for this sector and every candidate stage.
    stages = {r.stage for r in store.review_trail(position)}
    assert stages == {Stage.MARKET_SCAN, Stage.SECTOR_DEEP_DIVE, Stage.COMPANY_DEEP_DIVE, Stage.TECHNICAL}


async def test_rejected_decision_creates_no_position():
    mw, _, store = build()
    report = await mw.run(AS_OF)
    assert mw.record_decision(report.recommendations[0].candidate.id, accepted=False) is None
    assert store.open_positions() == []
    assert len(store.user_decisions()) == 1


async def test_improvements_reach_prompts_only_after_approval():
    bars = make_bars([100, 101], AS_OF + timedelta(hours=1))
    mw, llm, store = build(prices=FixturePrices({"AAA": bars}))
    report = await mw.run(AS_OF)
    pos = mw.record_decision(report.recommendations[0].candidate.id, True, opened_at=AS_OF + timedelta(hours=1))
    await mw.review_position(pos.id, now=bars[-1].ts)

    notes = store.improvements(approved_only=False)
    assert [n.text for n in notes] == ["check rate sensitivity"]

    await mw.run(AS_OF)
    assert "check rate sensitivity" not in llm.systems(MarketScanOutput)[-1]

    store.approve_improvement(notes[0].id)
    await mw.run(AS_OF)
    assert "check rate sensitivity" in llm.systems(MarketScanOutput)[-1]
    assert "check rate sensitivity" not in llm.systems(SectorDeepDiveOutput)[-1]


def test_improvement_note_defaults_unapproved():
    assert ImprovementNote(source_position_id="p", target_stage=Stage.TECHNICAL, text="t").approved is False


# ------------------------------------------------------------------------------------
# Investor profile, rules and conflicts
# ------------------------------------------------------------------------------------

from trading_pipeline.profile import InvestorProfile  # noqa: E402
from trading_pipeline.schemas import SectorCall  # noqa: E402

from .fakes import FixtureNews, FixtureQuotes, plan, reasoning  # noqa: E402


async def test_technical_agent_gets_profile_and_horizon_charts():
    prices = FixturePrices()
    mw, llm, _ = build(PipelineConfig(profile=InvestorProfile(horizons=["short_term", "swing"])), prices=prices)
    await mw.run(AS_OF)
    prompt = next(p for p in llm.prompts(TechnicalOutput) if "Company: AAA" in p)
    assert "<investor_profile>" in prompt and '"min_reward_to_risk": 2.0' in prompt
    assert {"1h", "1d", "1w"} <= set(prices.intervals)


async def test_rule_rejections_are_logged():
    mw, llm, store = build()
    llm.handlers[TechnicalOutput] = lambda p: TechnicalOutput(
        ticker="AAA", verdict="pass", setup="s", plan=plan(target=115), reasoning=reasoning())  # 1.5:1
    report = await mw.run(AS_OF)
    assert report.recommendations == []
    rej = next(x for x in report.rejections if x.ticker == "AAA")
    assert rej.stage == Stage.TECHNICAL and "reward_to_risk" in rej.summary
    rec = next(r for r in store.stage_records(run_id=report.run_id)
               if r.stage == Stage.TECHNICAL and r.subject == "AAA")
    assert rec.verdict == "rejected_by_rule"
    assert {r.rule: r.outcome for r in rec.rules}["reward_to_risk"] == "reject"


async def test_stale_entry_rejected():
    mw, _, _ = build(quotes=FixtureQuotes(price=106.0))  # entry 100, limit 3%
    report = await mw.run(AS_OF)
    assert report.recommendations == []
    assert any("stale_entry" in x.summary for x in report.rejections)


async def test_backtest_stale_check_uses_last_close():
    bars = make_bars([101.0], AS_OF - timedelta(days=1))
    mw, _, _ = build(prices=FixturePrices({"AAA": bars}))
    report = await mw.run(AS_OF, live=False)
    assert [r.candidate.ticker for r in report.recommendations] == ["AAA"]


async def test_upcoming_earnings_flagged():
    mw, _, _ = build(news=FixtureNews(earnings={"AAA": "2026-06-20"}))
    report = await mw.run(AS_OF)
    flags = {f.rule: f.message for f in report.recommendations[0].flags}
    assert "upcoming_earnings" in flags and "2026-06-20" in flags["upcoming_earnings"]
    assert "⚠ upcoming_earnings" in render_report(report)


async def test_conflicts_always_recorded_and_short_blocked_by_profile():
    mw, llm, store = build()
    llm.handlers[MarketScanOutput] = lambda p: MarketScanOutput(market_summary="mixed", sectors=[
        SectorCall(sector="Biotech", direction="upside", thesis="t", reasoning=reasoning()),
        SectorCall(sector="Pharma", direction="downside", thesis="t", reasoning=reasoning()),
    ])
    report = await mw.run(AS_OF)
    conflicts = {(c.ticker, c.kind) for c in report.conflicts}
    assert ("AAA", "direction_conflict") in conflicts and ("BBB", "direction_conflict") in conflicts
    assert len(store.conflicts(report.run_id)) == len(report.conflicts)
    # The downside (short) entries are rejected by the long-only default profile.
    assert any(x.stage == Stage.SECTOR_DEEP_DIVE and "profile_short" in x.summary for x in report.rejections)
    assert "Conflicts (" in render_report(report)


async def test_second_decision_for_same_candidate_is_blocked():
    mw, _, store = build()
    report = await mw.run(AS_OF)
    cid = report.recommendations[0].candidate.id
    mw.record_decision(cid, accepted=True)
    with pytest.raises(ValueError, match="already recorded"):
        mw.record_decision(cid, accepted=False)
    assert len(store.user_decisions()) == 1 and len(store.open_positions()) == 1
