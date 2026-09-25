"""Replay real hosted-Equibles responses (tests/fixtures/equibles_live) through every adapter.

The adapters were written from Equibles' open-source code; these fixtures were captured
from the hosted server, so a format change on either side fails here instead of silently
producing empty data in a run.
"""

from datetime import date, datetime, timezone
from pathlib import Path

from trading_pipeline.data.equibles import EquiblesFundamentals
from trading_pipeline.data.equibles_events import EquiblesFilings, EquiblesNews
from trading_pipeline.data.equibles_macro import EquiblesMacro
from trading_pipeline.data.equibles_prices import EquiblesPrices, EquiblesQuotes
from trading_pipeline.data.equibles_sectors import EquiblesSectorData

FIX = Path(__file__).parent / "fixtures" / "equibles_live"
AS_OF = datetime(2026, 9, 25, 21, tzinfo=timezone.utc)
SINCE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def now():
    return AS_OF


class Replay:
    async def call_tool(self, name, arguments):
        return (FIX / f"{name}.md").read_text()


async def test_fundamentals():
    snap = await EquiblesFundamentals(Replay(), aliases=["net-income"], include_restatements=False,
                                      now=now).fundamentals("AAPL", AS_OF)
    facts = snap.payload["facts"]
    assert not snap.is_gap and len(facts) == 3 and snap.payload["company"] == "Apple Inc."
    assert {f["value"] for f in facts} >= {42097000000.0}


async def test_prices_indicators_quotes():
    prices = EquiblesPrices(Replay(), now=now)
    bars = await prices.bars("AAPL", date(2026, 9, 1), AS_OF)
    assert len(bars) == 5 and bars[-1].close == 335.92
    assert not (await prices.indicators("AAPL", AS_OF)).is_gap
    quote = await EquiblesQuotes(Replay(), now=now).quote("AAPL")
    assert quote.payload["price"] == 335.92 and "not live" in quote.payload["basis"]


async def test_filings_events_earnings_fda():
    filings = await EquiblesFilings(Replay()).recent_filings("AAPL", SINCE, AS_OF)
    assert filings.payload and filings.payload[0]["sec_items"] == ["2.02", "9.01"]
    news = EquiblesNews(Replay())
    events = await news.events("AAPL", SINCE, AS_OF)
    assert any(e["category"] == "earnings" for e in events.payload)
    earnings = await news.upcoming_earnings("AAPL", AS_OF)
    assert not earnings.is_gap and earnings.payload["confirmed"] is False
    fda = await news.events("Health Care", datetime(2026, 9, 1, tzinfo=timezone.utc), AS_OF)
    assert not fda.is_gap


async def test_macro():
    snaps = {s.kind: s for s in await EquiblesMacro(Replay(), now=now).macro(AS_OF)}
    assert set(snaps) == {"macro:indicators", "macro:volatility", "macro:calendar"}
    assert not any(s.is_gap for s in snaps.values())
    assert snaps["macro:volatility"].payload["vix"]["value"] == 15.67


async def test_sectors_parse():
    sectors = EquiblesSectorData(Replay(), now=now)
    overview = await sectors.market_overview(AS_OF)
    assert overview[0].kind == "sector_performance" and overview[0].payload["benchmark"]["last_close"] == 335.92
    screen = await sectors.sector_screen("Health Care", AS_OF)
    coverage = next(s for s in screen if s.kind == "screen_coverage")
    assert coverage.payload["holdings_report_date"] == "2026-06-30"
