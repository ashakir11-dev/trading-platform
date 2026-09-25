"""EquiblesMacro against a fake MCP server emitting Equibles' exact FRED/CBOE markdown."""

from datetime import date, datetime, timedelta, timezone

import pytest

from trading_pipeline.data.base import RawDataBundle
from trading_pipeline.data.equibles_macro import (
    CALENDAR_TOOL, DEFAULT_SERIES, INDICATOR_TOOL, PUT_CALL_TOOL, VIX_TOOL, EquiblesMacro, MacroSeries,
    available_on, parse_calendar, parse_indicator)
from trading_pipeline.data.mcp import HttpMcpClient


def weekdays(start, end):
    d = start
    while d <= end:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)


def month_starts(start, end):
    d = start
    while d <= end:
        yield d
        d = date(d.year + d.month // 12, d.month % 12 + 1, 1)


FIRST, LAST = date(2024, 1, 1), date(2026, 12, 31)
# Every series runs past any as_of used below: the fake ignores endDate, so only the
# provider's own filtering can keep later rows out.
SERIES = {
    "DGS10": ("Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity", "Percent", "Daily",
              [(d, round(4 + (d - FIRST).days / 1000, 3)) for d in weekdays(FIRST, LAST)]),
    "DFF": ("Federal Funds Effective Rate", "Percent", "Daily, 7-Day",
            [(d, 4.33) for d in weekdays(FIRST, LAST)]),
    "CPIAUCSL": ("Consumer Price Index for All Urban Consumers: All Items in U.S. City Average",
                 "Index 1982-1984=100", "Monthly",
                 [(d, round(300 * 1.0025 ** i, 4)) for i, d in enumerate(month_starts(FIRST, LAST))]),
    "PAYEMS": ("All Employees, Total Nonfarm", "Thousands of Persons", "Monthly",
               [(d, 158000 + 150 * i) for i, d in enumerate(month_starts(FIRST, LAST))]),
    "ICSA": ("Initial Claims", "Number", "Weekly, Ending Saturday",
             [(d, 220000) for d in (FIRST + timedelta(days=5 + 7 * k) for k in range(156))]),
    "A191RL1Q225SBEA": ("Real Gross Domestic Product", "Percent Change from Preceding Period", "Quarterly",
                        [(d, 2.0 + i / 10) for i, d in enumerate(month_starts(FIRST, LAST)) if d.month in (1, 4, 7, 10)]),
}


def indicator_text(series_id, start, max_results=100):
    """FredTools.GetEconomicIndicator: MarkdownTable.Render with title + subtitle, rows ascending,
    newest maxResults kept, values via McpFormat.Invariant(v, "G") or "N/A"."""
    if series_id not in SERIES:
        return (f"No match for '{series_id}' in the tracked economic-indicator set. "
                "Use SearchEconomicIndicators to list or search that curated set.")
    title, units, freq, obs = SERIES[series_id]
    rows = [(d, v) for d, v in obs if d >= start]
    kept = rows[-max_results:]
    text = (f"{title} ({series_id})\nUnits: {units} | Frequency: {freq} | Seasonal Adj: Seasonally Adjusted\n\n"
            "| Date | Value |\n|------|-------|\n" + "".join(f"| {d:%Y-%m-%d} | {v:g} |\n" for d, v in kept))
    if len(kept) < len(rows):
        text += (f"\n_Showing the newest {len(kept)} of {len(rows)} observations in the range - raise "
                 "maxResults (max 500) or narrow the date range for earlier data._\n")
    return text


def vix_text(start):
    """CboeTools.GetVixHistory: 'CBOE Volatility Index (VIX):' + OHLC table, F2 values."""
    rows = [(d, 15 + d.day / 10) for d in weekdays(start, LAST)]
    return ("CBOE Volatility Index (VIX):\n\n| Date | Open | High | Low | Close |\n"
            "|------|------|------|-----|-------|\n"
            + "".join(f"| {d:%Y-%m-%d} | {v:.2f} | {v + 1:.2f} | {v - 1:.2f} | {v:.2f} |\n" for d, v in rows))


def put_call_text(kind, start):
    """CboeTools.GetPutCallRatios: N0 volumes, F2 ratio, McpFormat.OrDash -> '—' when null."""
    lines = []
    for d in weekdays(start, LAST):
        ratio = "—" if d.day == 13 else f"{0.5 + d.day / 100:.2f}"
        lines.append(f"| {d:%Y-%m-%d} | 1,200,000 | 800,000 | 2,000,000 | {ratio} |\n")
    return (f"CBOE {kind} Put/Call Ratios:\n\n| Date | Call Volume | Put Volume | Total | P/C Ratio |\n"
            "|------|-----------|----------|-------|-----------|\n" + "".join(lines))


CALENDAR_ROWS = [  # (date, release, importance, series)
    ("2026-03-06", "Employment Situation", "High", "PAYEMS, UNRATE"),
    ("2026-03-11", "Consumer Price Index", "High", "CPIAUCSL, CPILFESL"),
    ("2026-03-12", "Unemployment Insurance Weekly Claims Report", "Medium", "CCSA, ICSA"),
    ("2026-03-26", "Gross Domestic Product", "High", "A191RL1Q225SBEA, GDP, GDPC1"),
]


def calendar_text(start, end):
    """FredTools.GetEconomicCalendar. The fake ignores the requested window on purpose."""
    return (f"Economic release calendar ({start} to {end}):\n\n| Date | Release | Importance | Series Updated |\n"
            "|------|---------|------------|----------------|\n"
            + "".join(f"| {d} | {r} | {i} | {s} |\n" for d, r, i, s in CALENDAR_ROWS))


class FakeEquibles:
    def __init__(self, fail=()):
        self.calls = []
        self.fail = set(fail)

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name in self.fail or arguments.get("seriesId") in self.fail:
            raise RuntimeError(f"MCP tool {name} failed: An error occurred while executing {name}.")
        start = date.fromisoformat(arguments.get("startDate", "2024-01-01"))
        if name == INDICATOR_TOOL:
            return indicator_text(arguments["seriesId"], start, arguments.get("maxResults", 100))
        if name == VIX_TOOL:
            return vix_text(start)
        if name == PUT_CALL_TOOL:
            return put_call_text(arguments["type"], start)
        if name == CALENDAR_TOOL:
            return calendar_text(arguments["startDate"], arguments["endDate"])
        raise AssertionError(name)


AS_OF = datetime(2026, 3, 10, 21, 0, tzinfo=timezone.utc)  # Tue 17:00 US/Eastern


def provider(fake, now=datetime(2026, 9, 25, tzinfo=timezone.utc), **kw):
    return EquiblesMacro(fake, now=lambda: now, **kw)


def by_kind(snaps):
    return {s.kind: s for s in snaps}


def all_dates(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "date":
                yield v
            else:
                yield from all_dates(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from all_dates(v)


def test_parse_indicator_exact_format():
    text = indicator_text("CPIAUCSL", date(2025, 10, 1), max_results=3)
    text = text.replace(f"{SERIES['CPIAUCSL'][3][-2][1]:g}", "N/A")  # a null value renders as N/A
    obs, meta = parse_indicator(text)
    assert meta["units"] == "Index 1982-1984=100" and meta["fred_frequency"] == "Monthly"
    assert meta["title"].startswith("Consumer Price Index")
    assert [d for d, _ in obs] == [date(2026, 10, 1), date(2026, 12, 1)]  # N/A row dropped
    empty, meta = parse_indicator(indicator_text("NOPE", date(2025, 1, 1)))
    assert empty == [] and meta["message"].startswith("No match for 'NOPE'")


def test_publication_lag():
    # CPI for Feb 2026 (dated 02-01): period ends 02-28, released ~3 weeks later.
    assert available_on(date(2026, 2, 1), "monthly", 15) == date(2026, 3, 20)
    # Claims for the week ending Sat 03-07 are released Thursday 03-12.
    assert available_on(date(2026, 3, 7), "weekly", 4) == date(2026, 3, 12)
    # Q4 2025 GDP (dated 10-01) ends 12-31.
    assert available_on(date(2025, 10, 1), "quarterly", 0) == date(2025, 12, 31)


async def test_indicators_point_in_time_and_trend():
    fake = FakeEquibles()
    snaps = await provider(fake).macro(AS_OF)
    ind = by_kind(snaps)["macro:indicators"]
    s = {i["series"]: i for i in ind.payload["series"]}

    # Daily: the latest close is the previous day; the fake served rows through 2026-12-31.
    assert s["DGS10"]["date"] == "2026-03-09"
    assert s["DGS10"]["1m_ago"]["date"] == "2026-02-09" and s["DGS10"]["3m_ago"]["date"] == "2025-12-09"
    # DFF is published the next business day: Monday's value appears only on Wednesday.
    assert s["DFF"]["date"] == "2026-03-06"
    # CPI: Feb (dated 02-01) is not out by 03-10, so January is the latest; YoY from the index.
    assert s["CPIAUCSL"]["date"] == "2026-01-01"
    assert s["CPIAUCSL"]["value"] == pytest.approx((1.0025 ** 12 - 1) * 100, abs=0.01)
    assert s["CPIAUCSL"]["units"] == "Percent change from a year earlier"
    assert s["CPIAUCSL"]["1m_ago"]["date"] == "2025-12-01"
    assert s["CPIAUCSL"]["level"]["date"] == "2026-01-01"
    # Payrolls as the monthly change.
    assert s["PAYEMS"]["value"] == 150 and s["PAYEMS"]["date"] == "2026-01-01"
    # Claims: week ending 03-07 is released 03-12, so 02-28 is the latest.
    assert s["ICSA"]["date"] == "2026-02-28"
    # GDP: Q4 2025 is out, Q1 2026 is not; trend is by quarter.
    assert s["A191RL1Q225SBEA"]["date"] == "2025-10-01"
    assert s["A191RL1Q225SBEA"]["prior_quarter"]["date"] == "2025-07-01"
    # Nothing dated on or after as_of anywhere in any snapshot's data (calendar aside).
    for snap in snaps:
        if snap.kind != "macro:calendar":
            assert all(d < "2026-03-10" for d in all_dates(snap.payload)), snap.kind
    # Untracked-in-fake series are reported, not silently missing.
    assert any(n.startswith("T10Y2Y:") and "No match" in n for n in ind.payload["notes"])
    # And every request was capped at the as_of day.
    assert all(a.get("endDate", "") <= "2026-03-24" for _, a in fake.calls)
    assert all(a["endDate"] <= "2026-03-10" for n, a in fake.calls if n != CALENDAR_TOOL)


async def test_later_as_of_sees_later_data():
    snaps = await provider(FakeEquibles()).macro(datetime(2026, 3, 21, 14, tzinfo=timezone.utc))
    s = {i["series"]: i for i in by_kind(snaps)["macro:indicators"].payload["series"]}
    assert s["CPIAUCSL"]["date"] == "2026-02-01"  # released 03-20, visible 03-21
    assert s["ICSA"]["date"] == "2026-03-14"


async def test_revision_caveat_only_in_backtests():
    backtest = by_kind(await provider(FakeEquibles()).macro(AS_OF))["macro:indicators"]
    assert "LATEST REVISED" in backtest.note and backtest.payload["latest_revised_values"]
    revised, unrevised = backtest.note.split("Market-priced")
    assert "CPIAUCSL" in revised and "PAYEMS" in revised and "A191RL1Q225SBEA" in revised
    assert "DGS10" in unrevised and "DGS10" not in revised

    live = by_kind(await provider(FakeEquibles(), now=AS_OF).macro(AS_OF))["macro:indicators"]
    assert live.note == "" and not live.payload["latest_revised_values"]


async def test_volatility():
    vol = by_kind(await provider(FakeEquibles()).macro(AS_OF))["macro:volatility"]
    assert vol.payload["vix"]["date"] == "2026-03-09" and vol.payload["vix"]["value"] == pytest.approx(15.9)
    pc = vol.payload["put_call_equity"]
    assert pc["date"] == "2026-03-09" and pc["value"] == pytest.approx(0.59)
    assert 0.5 < pc["avg_last_20"] < 0.82
    assert pc["1m_ago"]["date"] == "2026-02-09"


async def test_calendar_window():
    fake = FakeEquibles()
    cal = by_kind(await provider(fake).macro(AS_OF))["macro:calendar"]
    args = next(a for n, a in fake.calls if n == CALENDAR_TOOL)
    assert (args["startDate"], args["endDate"], args["minImportance"]) == ("2026-03-10", "2026-03-24", "medium")
    # The fake ignored the window; the provider drops the past release and the one after 14 days.
    assert [r["release"] for r in cal.payload["releases"]] == [
        "Consumer Price Index", "Unemployment Insurance Weekly Claims Report"]
    assert cal.payload["releases"][0]["series"] == ["CPIAUCSL", "CPILFESL"]
    assert parse_calendar("No economic releases between 2026-03-10 and 2026-03-24.") == (
        [], "No economic releases between 2026-03-10 and 2026-03-24.")


async def test_empty_calendar_is_not_a_gap():
    class NoReleases(FakeEquibles):
        async def call_tool(self, name, arguments):
            if name == CALENDAR_TOOL:
                return "No economic releases between 2026-03-10 and 2026-03-24."
            return await super().call_tool(name, arguments)

    cal = by_kind(await provider(NoReleases()).macro(AS_OF))["macro:calendar"]
    assert not cal.is_gap and cal.payload["releases"] == []


async def test_call_budget_and_tools():
    fake = FakeEquibles()
    snaps = await provider(fake).macro(AS_OF)
    assert len(fake.calls) == len(DEFAULT_SERIES) + 3 == 16
    assert {n for n, _ in fake.calls} == EquiblesMacro.TOOLS
    bundle = RawDataBundle(as_of=AS_OF)
    bundle.extend(snaps)  # no LookaheadError
    assert all(s.subject == "market" and s.kind.startswith("macro") for s in snaps)

    fake = FakeEquibles()
    await provider(fake, series=[MacroSeries("DGS10", "10y", "daily", 0)], put_call_types=["Equity", "Total"]).macro(AS_OF)
    assert len(fake.calls) == 1 + 1 + 2 + 1


async def test_failures_are_notes_or_gaps():
    snaps = by_kind(await provider(FakeEquibles(fail={"DGS10"})).macro(AS_OF))
    assert any(n.startswith("DGS10:") and "failed" in n for n in snaps["macro:indicators"].payload["notes"])
    assert not snaps["macro:indicators"].is_gap

    snaps = by_kind(await provider(FakeEquibles(fail=EquiblesMacro.TOOLS)).macro(AS_OF))
    assert all(s.is_gap and s.note for s in snaps.values())


async def test_http_client_allowlist():
    client = HttpMcpClient("https://example.invalid/mcp", allowed_tools=set(EquiblesMacro.TOOLS))
    with pytest.raises(PermissionError):
        await client.call_tool("GetLatestEconomicIndicators", {})
