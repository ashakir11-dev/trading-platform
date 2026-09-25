"""Equibles prices/quotes adapters against a fake MCP emitting Equibles' exact text formats."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from trading_pipeline.data import technicals as ta
from trading_pipeline.data.base import RawDataBundle
from trading_pipeline.data.equibles_prices import (
    BACKTEST_SPLIT_NOTE,
    LATEST_CLOSE_TOOL,
    PRICES_TOOL,
    EquiblesPrices,
    EquiblesQuotes,
    parse_latest_closes,
    parse_price_table,
)

ET = ZoneInfo("America/New_York")


def et(y, m, d, hh=17, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=ET)


def price(v: float) -> str:
    # McpFormat.Price: "F2" at or above $1 (invariant culture)
    return f"{v:.2f}"


def whole(v: float) -> str:
    # McpFormat.WholeNumber: "N0" -> thousands separators
    return f"{int(v):,}"


def trading_days(start: date, end: date) -> list[date]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


class FakeEquiblesPrices:
    """Mimics StockPriceTools.GetStockPrices and GetLatestClosingPrices text output.

    Based on src/Equibles.Yahoo.Mcp/Tools/StockPriceTools.cs:
    - GetStockPrices: title "Daily prices for {TICKER} ({Name}):", blank line, header with an
      "Adj Close" column only when some row's AdjustedClose != Close, rows oldest->newest
      after keeping the NEWEST maxResults, AppendNewestKeptTruncationNote, then the
      italic Adj Close footnote. Unknown range -> "No price data found for X in the
      specified date range."
    - GetLatestClosingPrices: "Latest prices:" table with Ticker/Date/Close/Change/Change %/
      Volume/52W High/52W Low/Off High/Above Low, PlaceholderRow for unknown tickers.

    ``leak_future`` makes the fake ignore endDate, so tests prove the adapter filters the
    parsed rows by as_of itself.
    """

    def __init__(self, days: list[date], *, leak_future=False, adj=False, name="Acme | Co"):
        self.series = {d: self.bar_for(i) for i, d in enumerate(days)}
        self.leak_future = leak_future
        self.adj = adj
        self.name = name
        self.calls: list[tuple[str, dict]] = []

    @staticmethod
    def bar_for(i: int):
        c = 100 + (i % 10) - (i % 3) + i * 0.1
        return (c - 0.5, c + 1.25, c - 1.5, c, 1_000_000 + 1000 * i)

    async def call_tool(self, name, arguments):
        assert name in EquiblesPrices.TOOLS | EquiblesQuotes.TOOLS
        self.calls.append((name, arguments))
        if name == LATEST_CLOSE_TOOL:
            return self.latest(arguments["tickers"])
        if name == "GetLiveQuote":  # the real hosted answer on the Free plan
            return (Path(__file__).parent / "fixtures" / "equibles_live" / "GetLiveQuote.free_plan.md").read_text()
        if arguments["ticker"] != "ACME":
            return f"Stock '{arguments['ticker']}' not found."
        start = date.fromisoformat(arguments["startDate"])
        end = date.fromisoformat(arguments["endDate"])
        rows = sorted(d for d in self.series if start <= d <= end)
        total = len(rows)
        rows = rows[-arguments.get("maxResults", 260):]
        if self.leak_future:  # a misbehaving server: a week of bars after endDate
            rows += sorted(d for d in self.series if end < d <= end + timedelta(days=7))
        if not rows:
            return "No price data found for ACME in the specified date range."
        title = f"Daily prices for ACME ({self.name.replace('|', chr(92) + '|')}):"
        if self.adj:
            head = "| Date | Open | High | Low | Close | Adj Close | Volume |\n|------|------|------|-----|-------|-----------|--------|"
        else:
            head = "| Date | Open | High | Low | Close | Volume |\n|------|------|------|-----|-------|--------|"
        lines = [title, "", *head.split("\n")]
        for d in rows:
            o, h, lo, c, v = self.series[d]
            adj = f" {price(c * 0.98)} |" if self.adj else ""
            lines.append(f"| {d:%Y-%m-%d} | {price(o)} | {price(h)} | {price(lo)} | {price(c)} |{adj} {whole(v)} |")
        if len(rows) < total:
            lines += ["", f"_Showing the newest {len(rows)} of {total} records in the range - "
                          "raise maxResults or narrow the date range to see older rows._"]
        lines += ["", "_Adj Close is the provider-adjusted close. Captured splits and cash dividends trigger a "
                      "full-history refresh, but stored rows do not certify which split basis the provider returned. "
                      "Do not infer a consistent total-return window from reconciliation status alone._"]
        return "\n".join(lines) + "\n"

    def latest(self, tickers):
        lines = ["Latest prices:", "",
                 "| Ticker | Date | Close | Change | Change % | Volume | 52W High | 52W Low | Off High | Above Low |",
                 "|--------|------|-------|--------|----------|--------|----------|---------|----------|-----------|"]
        for t in tickers:
            if t != "ACME":
                lines.append(f"| {t} | — | Not found | — | — | — | — | — | — | — |")
                continue
            d = max(self.series)
            c = self.series[d][3]
            lines.append(f"| ACME | {d:%Y-%m-%d} | {price(c)} | +1.20 | +1.05% | 1,234,567 | 150.00\\* | "
                         f"90.00\\* | -10.00% | +20.00% |")
        return "\n".join(lines) + "\n"


DAYS = trading_days(date(2024, 1, 2), date(2026, 9, 25))
NOW = et(2026, 9, 25, 18)


def prices(fake, now=NOW, **kw):
    return EquiblesPrices(fake, now=lambda: now, **kw)


def test_parse_price_table_exact_format():
    fake = FakeEquiblesPrices(DAYS[:3], adj=True)
    import asyncio
    text = asyncio.run(fake.call_tool(PRICES_TOOL, {"ticker": "ACME", "startDate": "2024-01-01",
                                                    "endDate": "2024-01-31", "maxResults": 500}))
    bars, meta = parse_price_table(text)
    assert meta["title"] == "ACME (Acme \\| Co)" and meta["adj_close"] and not meta["truncated"]
    assert len(bars) == 3
    o, h, lo, c, v = FakeEquiblesPrices.bar_for(0)
    assert (bars[0].open, bars[0].high, bars[0].low, bars[0].close, bars[0].volume) == pytest.approx(
        (round(o, 2), round(h, 2), round(lo, 2), round(c, 2), v))
    # a daily bar is stamped at its session close, 16:00 ET
    assert bars[0].ts == datetime(2024, 1, 2, 16, tzinfo=ET)
    empty, meta = parse_price_table("No price data found for ACME in the specified date range.")
    assert empty == [] and "No price data" in meta["message"]


async def test_daily_bars_never_after_as_of_even_if_server_leaks():
    fake = FakeEquiblesPrices(DAYS, leak_future=True)
    as_of = et(2026, 3, 11, 12)  # Wednesday midday: that day's bar isn't closed yet
    bars = await prices(fake).bars("ACME", date(2026, 1, 1), as_of)
    assert bars and max(b.ts for b in bars) <= as_of
    assert bars[-1].ts.astimezone(ET).date() == date(2026, 3, 10)
    assert bars[0].ts.astimezone(ET).date() == date(2026, 1, 1)  # fixture has no holidays
    after_close = await prices(fake).bars("ACME", date(2026, 1, 1), et(2026, 3, 11, 16))
    assert after_close[-1].ts.astimezone(ET).date() == date(2026, 3, 11)
    # the request itself is bounded too
    assert all(a["endDate"] <= "2026-03-11" for _, a in fake.calls)


async def test_long_ranges_are_chunked_under_the_row_cap_and_cached():
    fake = FakeEquiblesPrices(DAYS)
    p = prices(fake)
    as_of = et(2026, 9, 24)
    bars = await p.bars("ACME", date(2024, 1, 1), as_of)
    assert len(bars) == len([d for d in DAYS if d <= date(2026, 9, 24)])
    assert len(fake.calls) == 2  # ~1000 calendar days / 600-day chunks
    for _, a in fake.calls:
        span = date.fromisoformat(a["endDate"]) - date.fromisoformat(a["startDate"])
        assert span.days < 600 and a["maxResults"] == 500
    n = len(fake.calls)
    await p.indicators("ACME", as_of, "1d")
    await p.pivots("ACME", as_of, "1d")
    await p.ohlcv("ACME", date(2026, 1, 1), as_of, "1w")
    assert len(fake.calls) == n  # all served from the cached daily history


async def test_weekly_bars_from_daily_with_partial_current_week():
    fake = FakeEquiblesPrices(DAYS, leak_future=True)
    as_of = et(2026, 9, 23, 17)  # Wednesday after the close
    weeks = await prices(fake).bars("ACME", date(2026, 9, 9), as_of, "1w")  # start mid-week
    daily = await prices(fake).bars("ACME", date(2026, 9, 7), as_of)
    assert [w.ts.astimezone(ET).date() for w in weeks] == [date(2026, 9, 11), date(2026, 9, 18), date(2026, 9, 23)]
    first = [b for b in daily if b.ts.astimezone(ET).date() <= date(2026, 9, 11)]
    assert weeks[0].open == first[0].open and weeks[0].close == first[-1].close
    assert weeks[0].volume == sum(b.volume for b in first)
    last = [b for b in daily if b.ts.astimezone(ET).date() >= date(2026, 9, 21)]
    assert len(last) == 3 and weeks[-1].high == max(b.high for b in last) and weeks[-1].ts <= as_of

    snap = await prices(fake).ohlcv("ACME", date(2026, 9, 9), as_of, "1w")
    assert snap.kind == "ohlcv:1w" and snap.payload["rows"][-1][0] == "2026-09-23"
    assert any("partial" in n for n in snap.payload["notes"])


async def test_ohlcv_payload_is_compact_and_point_in_time():
    fake = FakeEquiblesPrices(DAYS, leak_future=True)
    as_of = et(2025, 6, 13, 17)
    snap = await prices(fake).ohlcv("ACME", date(2025, 6, 1), as_of)
    assert snap.kind == "ohlcv:1d" and not snap.is_gap and snap.as_of == as_of
    assert snap.payload["columns"] == ["date", "o", "h", "l", "c", "v"]
    assert snap.payload["rows"][-1][0] == "2025-06-13" and len(snap.payload["rows"]) == 10
    assert snap.payload["listing"] == "ACME (Acme \\| Co)"
    assert "Adj" not in str(snap.payload["rows"])
    RawDataBundle(as_of=as_of).add(snap)  # look-ahead guard accepts it


async def test_backtest_split_caveat_only_for_past_as_of():
    fake = FakeEquiblesPrices(DAYS)
    past = await prices(fake).ohlcv("ACME", date(2025, 6, 1), et(2025, 6, 13))
    live = await prices(fake).ohlcv("ACME", date(2026, 9, 1), NOW)
    assert BACKTEST_SPLIT_NOTE in past.payload["notes"]
    assert BACKTEST_SPLIT_NOTE not in live.payload["notes"]
    ind = await prices(fake).indicators("ACME", et(2025, 6, 13), "1w")
    assert BACKTEST_SPLIT_NOTE in ind.payload["notes"]


async def test_indicators_use_only_bars_up_to_as_of():
    as_of = et(2025, 12, 31, 17)
    leaky = await prices(FakeEquiblesPrices(DAYS, leak_future=True)).indicators("ACME", as_of)
    trimmed = FakeEquiblesPrices([d for d in DAYS if d <= date(2025, 12, 31)])
    clean = await prices(trimmed).indicators("ACME", as_of)
    assert leaky.payload == clean.payload
    p = leaky.payload
    assert p["date"] == "2025-12-31" and leaky.kind == "indicators:1d"
    # matches the pure functions run on the same filtered bars
    bars = await prices(trimmed).bars("ACME", date(2025, 12, 31) - timedelta(days=450), as_of)
    expected = ta.indicator_summary(bars)
    assert p["sma"] == expected["sma"] and p["rsi14"] == expected["rsi14"] and p["atr14"] == expected["atr14"]
    assert p["sma"]["200"] is not None and p["range_52w"]["full_year"]
    assert all(r["date"] <= "2025-12-31" for r in p["recent"])

    weekly = await prices(FakeEquiblesPrices(DAYS, leak_future=True)).indicators("ACME", as_of, "1w")
    assert weekly.kind == "indicators:1w" and weekly.payload["date"] == "2025-12-31"
    assert weekly.payload["sma"]["200"] is None  # fixture history starts 2024: too short for SMA 200 weeks


async def test_pivots_from_prior_periods_and_swings():
    fake = FakeEquiblesPrices(DAYS, leak_future=True)
    as_of = et(2026, 9, 23, 17)  # Wednesday
    snap = await prices(fake).pivots("ACME", as_of)
    p = snap.payload
    assert snap.kind == "pivots:1d" and set(p["floor_pivots"]) == {"prior_day", "prior_week", "prior_month"}
    wk = p["floor_pivots"]["prior_week"]
    assert (wk["from"]["start"], wk["from"]["end"]) == ("2026-09-14", "2026-09-18")
    assert wk["p"] == pytest.approx((wk["from"]["high"] + wk["from"]["low"] + wk["from"]["close"]) / 3, abs=1e-4)
    assert p["floor_pivots"]["prior_day"]["from"]["end"] == "2026-09-23"
    assert p["floor_pivots"]["prior_month"]["from"]["end"] == "2026-08-31"
    assert all(s["date"] <= "2026-09-23" for s in p["swing_highs"] + p["swing_lows"])
    assert p["swing_highs"] and p["swing_lows"]
    n = p["nearest"]
    assert n["support"] is None or n["support"] < p["close"]
    assert n["resistance"] is None or n["resistance"] > p["close"]

    weekly = await prices(fake).pivots("ACME", as_of, "1w")
    assert set(weekly.payload["floor_pivots"]) == {"prior_week", "prior_month", "prior_year"}
    assert weekly.payload["floor_pivots"]["prior_year"]["from"]["end"] == "2025-12-31"


async def test_hourly_is_an_explicit_gap():
    fake = FakeEquiblesPrices(DAYS)
    p = prices(fake)
    assert await p.bars("ACME", date(2026, 9, 1), NOW, "1h") == []
    for snap in [await p.ohlcv("ACME", date(2026, 9, 1), NOW, "1h"), await p.indicators("ACME", NOW, "1h"),
                 await p.pivots("ACME", NOW, "1h")]:
        assert snap.is_gap and snap.kind.endswith(":1h") and "Equibles Cloud" in snap.note
    assert fake.calls == []
    with pytest.raises(ValueError):
        await p.bars("ACME", date(2026, 9, 1), NOW, "5m")


async def test_unknown_ticker_and_empty_range_are_gaps():
    fake = FakeEquiblesPrices(DAYS)
    snap = await prices(fake).ohlcv("NOPE", date(2026, 9, 1), NOW)
    assert snap.is_gap and "not found" in snap.note
    early = await prices(fake).indicators("ACME", et(2023, 6, 1))
    assert early.is_gap and "No price data" in early.note
    assert await prices(fake).bars("NOPE", date(2026, 9, 1), NOW) == []


def test_parse_latest_closes_exact_format():
    fake = FakeEquiblesPrices(DAYS)
    rows = parse_latest_closes(fake.latest(["ACME", "ZZZ"]))
    assert rows["ACME"]["date"] == date(2026, 9, 25) and rows["ACME"]["high_52w"] == 150.0
    assert rows["ACME"]["change_pct"] == pytest.approx(1.05)
    assert rows["ZZZ"]["price"] is None and rows["ZZZ"]["status"] == "Not found"


async def test_quote_is_last_close_not_live():
    fake = FakeEquiblesPrices(DAYS)
    q = EquiblesQuotes(fake, now=lambda: NOW)
    snap = await q.quote("ACME")
    assert fake.calls == [("GetLiveQuote", {"tickers": ["ACME"]}), (LATEST_CLOSE_TOOL, {"tickers": ["ACME"]})]
    assert "not included in this plan" in snap.payload["why_not_live"]
    assert snap.kind == "quote" and not snap.is_gap
    assert snap.payload["price"] == round(fake.series[date(2026, 9, 25)][3], 2)
    assert snap.payload["as_of_date"] == "2026-09-25" and snap.payload["basis"] == "last close (EOD), not live"
    assert snap.as_of == datetime(2026, 9, 25, 16, tzinfo=ET)
    missing = await q.quote("ZZZ")
    assert missing.is_gap and "Not found" in missing.note


async def test_positions_is_a_gap_and_no_order_methods():
    q = EquiblesQuotes(FakeEquiblesPrices(DAYS), now=lambda: NOW)
    snap = await q.positions()
    assert snap.is_gap and snap.kind == "positions"
    public = {n for n in dir(q) if not n.startswith("_")}
    assert public == {"TOOLS", "quote", "positions"}
    assert EquiblesQuotes.TOOLS == {"GetLiveQuote", LATEST_CLOSE_TOOL} and EquiblesPrices.TOOLS == {PRICES_TOOL}


def test_as_of_must_be_timezone_aware():
    import asyncio
    with pytest.raises(ValueError):
        asyncio.run(prices(FakeEquiblesPrices(DAYS)).bars("ACME", date(2026, 1, 1), datetime(2026, 3, 1)))


def test_utc_as_of_is_handled():
    import asyncio
    as_of = datetime(2026, 3, 11, 19, 59, tzinfo=timezone.utc)  # 15:59 ET (EDT from Mar 8)
    bars = asyncio.run(prices(FakeEquiblesPrices(DAYS, leak_future=True)).bars("ACME", date(2026, 3, 1), as_of))
    assert bars[-1].ts.astimezone(ET).date() == date(2026, 3, 10)



def test_parse_live_quotes_requires_a_quote_table():
    from trading_pipeline.data.equibles_prices import parse_live_quotes

    free = (Path(__file__).parent / "fixtures" / "equibles_live" / "GetLiveQuote.free_plan.md").read_text()
    assert parse_live_quotes(free) == {}
    assert parse_live_quotes("| Name | Value |\n|---|---|\n| a | 1 |\n") == {}
