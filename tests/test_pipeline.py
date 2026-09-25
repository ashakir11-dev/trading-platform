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
    for kind in ("sector_breadth", "sector_performance", "fundamentals", "ohlcv"):
        assert f'"kind": "{kind}"' in tech_prompt
    assert "UNAVAILABLE" in tech_prompt  # gaps are explicit, not silently empty


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
