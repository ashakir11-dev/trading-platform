from datetime import timedelta

import pytest

from trading_pipeline import Middleware, PipelineConfig, Store
from trading_pipeline.agents import check_tripwires, compute_outcome
from trading_pipeline.data.gaps import UnavailableNews
from trading_pipeline.schemas import FullReviewOutput, Position, Stage

from .fakes import AS_OF, FixtureNews, FixturePrices, ScriptedLLM, make_bars, plan, providers

OPEN = AS_OF + timedelta(hours=1)


def position(direction="long", **kw) -> Position:
    p = plan(direction=direction) if direction == "long" else plan(entry=100, target=80, stop=110, direction="short")
    return Position(run_id="r", candidate_id="c", ticker="AAA", sector="Biotech", plan=p, opened_at=OPEN, **kw)


def test_outcome_long():
    bars = make_bars([100, 95, 112], OPEN)
    o = compute_outcome(position(), bars, now=bars[-1].ts)
    assert o.return_pct == pytest.approx(12.0)
    assert o.max_adverse_excursion_pct == pytest.approx(-6.0)  # low of 94
    assert o.max_favorable_excursion_pct == pytest.approx(13.0)  # high of 113
    assert not o.hit_stop and not o.hit_target and o.holding_days == 2


def test_outcome_short_hits_target():
    bars = make_bars([100, 90, 79], OPEN)
    o = compute_outcome(position("short"), bars, now=bars[-1].ts)
    assert o.return_pct == pytest.approx(21.0)
    assert o.hit_target and not o.hit_stop


def test_outcome_uses_exit_price_when_closed():
    bars = make_bars([100, 105, 130], OPEN)
    p = position(status="closed", exit_price=104.0, closed_at=bars[1].ts)
    o = compute_outcome(p, bars, now=bars[-1].ts)
    assert o.return_pct == pytest.approx(4.0) and o.closed
    assert not o.hit_target  # the 130 bar is after close


def test_tripwires():
    p = position()
    assert not check_tripwires(p, make_bars([100, 101], OPEN), None, OPEN).tripped
    t = check_tripwires(p, make_bars([100, 89], OPEN), None, OPEN)
    assert t.tripped and "stop" in t.reasons[0]
    # A data gap never trips the fundamental wire by itself.
    import asyncio
    gap = asyncio.run(UnavailableNews().events("AAA", OPEN, OPEN))
    assert not check_tripwires(p, make_bars([100], OPEN), gap, OPEN).tripped


async def _setup(closes, news=None):
    bars = make_bars(closes, OPEN)
    llm, store = ScriptedLLM(), Store()
    mw = Middleware(PipelineConfig(full_review_interval=timedelta(days=14)), llm,
                    providers(prices=FixturePrices({"AAA": bars}), news=news or FixtureNews()), store)
    report = await mw.run(AS_OF)
    pos = mw.record_decision(report.recommendations[0].candidate.id, True, opened_at=OPEN)
    return mw, llm, store, pos, bars


async def test_follow_up_quiet_tick_skips_full_review():
    mw, llm, store, pos, bars = await _setup([100, 101, 102])
    events = await mw.follow_up_loop().tick(bars[-1].ts)
    assert len(events) == 1 and not events[0].tripwire.tripped and events[0].review is None
    assert llm.prompts(FullReviewOutput) == []


async def test_follow_up_tripwire_triggers_full_review():
    mw, llm, store, pos, bars = await _setup([100, 95, 88])
    events = await mw.follow_up_loop().tick(bars[-1].ts)
    assert events[0].tripwire.tripped and events[0].review.action == "hold"
    recs = store.stage_records(position_id=pos.id)
    assert [r.stage for r in recs] == [Stage.FOLLOW_UP_FULL_REVIEW]
    assert store.position(pos.id).last_full_review_at == bars[-1].ts


async def test_follow_up_interval_triggers_full_review():
    mw, llm, store, pos, bars = await _setup([100] * 20)
    loop = mw.follow_up_loop()
    assert (await loop.tick(bars[5].ts))[0].review is None
    assert (await loop.tick(bars[15].ts))[0].review is not None


async def test_follow_up_news_only_counts_new_events():
    news = FixtureNews()
    mw, llm, store, pos, bars = await _setup([100] * 5, news)
    loop = mw.follow_up_loop()
    news.events_by_subject["AAA"] = [{"ts": bars[1].ts, "headline": "FDA delay"}]
    assert (await loop.tick(bars[2].ts))[0].tripwire.tripped
    assert not (await loop.tick(bars[3].ts))[0].tripwire.tripped  # already seen
