"""Point-in-time macro data from the hosted Equibles MCP server (FRED + CBOE tools).

``EquiblesMacro`` implements ``MacroProvider``. Per ``macro(as_of)`` it returns three
market-level snapshots:

* ``macro:indicators``: a curated FRED series list (``DEFAULT_SERIES``), each with its
  latest value visible at ``as_of``, the observation date, and the value 1 and 3
  months earlier (1 and 2 quarters for quarterly series).
* ``macro:volatility``: VIX (CBOE ``GetVixHistory``) and the CBOE put/call ratio(s)
  (``GetPutCallRatios``), with the same trend fields.
* ``macro:calendar``: scheduled US economic releases in the ``calendar_days`` after
  ``as_of`` (``GetEconomicCalendar``). Release dates are announced in advance.

Tools (checked against Equibles' ``FredTools.cs`` and ``CboeTools.cs``):
``GetEconomicIndicator(seriesId, startDate, endDate, maxResults)``,
``GetEconomicCalendar(startDate, endDate, minImportance, maxResults)``,
``GetVixHistory(startDate, endDate, maxResults)`` and
``GetPutCallRatios(type, startDate, endDate, maxResults)``. We do not ask for the
compact "GCF" format, so answers are the default markdown tables.

Call budget per ``macro()``: one ``GetEconomicIndicator`` per FRED series (13 by
default; the tool takes one series per call, and ``GetLatestEconomicIndicators``
only knows today's value, so it can't serve backtests or trends), one
``GetVixHistory``, one ``GetPutCallRatios`` per ratio type (1 by default) and one
``GetEconomicCalendar``: **16 calls** with the defaults.

Point-in-time rules:

* FRED dates an observation by the start of its period (CPI for August is dated
  08-01 but published mid-September). So a row is visible only once its period has
  ended **and** its typical publication lag has passed: ``available_on = period_end
  + release_lag_bdays`` (business days, holidays ignored), and the row is kept only
  if ``available_on`` is an earlier US/Eastern day than ``as_of`` (the same
  same-day rule as ``EquiblesFundamentals``). Lags are conservative. A release
  delayed beyond its lag (e.g. a government shutdown) can still leak in a backtest.
* Every tool is also asked for ``endDate`` = the as_of day, but rows are filtered
  after parsing too, so a server that ignores ``endDate`` can't leak.
* FRED values are the **latest revised** values, not what was published at
  ``as_of`` (ALFRED vintages are not available through Equibles). In backtests the
  snapshot note says so and lists which series are commonly revised.
"""

from __future__ import annotations

import asyncio
import calendar
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from .base import DataSnapshot
from .equibles import visible_before
from .equibles_md import find_table, number
from .mcp import McpToolCaller

INDICATOR_TOOL = "GetEconomicIndicator"
CALENDAR_TOOL = "GetEconomicCalendar"
VIX_TOOL = "GetVixHistory"
PUT_CALL_TOOL = "GetPutCallRatios"

Frequency = Literal["daily", "weekly", "monthly", "quarterly"]
Transform = Literal["level", "yoy", "change"]


@dataclass(frozen=True)
class MacroSeries:
    """One FRED series in the macro snapshot.

    ``release_lag_bdays``: business days after the period ends until the value is
    public (the release day). ``transform``: "level" as stored, "yoy" percent change
    versus 12 months earlier (for index series like CPI), "change" difference from the
    previous observation (e.g. monthly payroll gains). ``revised``: whether the source
    revises published values (so the latest-revised value differs from what was known).
    """

    series_id: str
    label: str
    frequency: Frequency
    release_lag_bdays: int
    transform: Transform = "level"
    revised: bool = False


# Equity-risk relevant, all in Equibles' curated FRED set (CuratedSeriesRegistry.cs).
DEFAULT_SERIES: tuple[MacroSeries, ...] = (
    MacroSeries("DFF", "Effective federal funds rate (policy rate)", "daily", 1),
    MacroSeries("DGS2", "2-year Treasury yield", "daily", 0),
    MacroSeries("DGS10", "10-year Treasury yield", "daily", 0),
    MacroSeries("T10Y2Y", "10y minus 2y Treasury spread", "daily", 0),
    MacroSeries("CPIAUCSL", "CPI, all items, YoY %", "monthly", 15, "yoy", revised=True),
    MacroSeries("CPILFESL", "Core CPI (ex food & energy), YoY %", "monthly", 15, "yoy", revised=True),
    MacroSeries("UNRATE", "Unemployment rate", "monthly", 7, revised=True),
    MacroSeries("PAYEMS", "Nonfarm payrolls, monthly change (thousands)", "monthly", 7, "change", revised=True),
    MacroSeries("ICSA", "Initial jobless claims (weekly)", "weekly", 4, revised=True),
    MacroSeries("A191RL1Q225SBEA", "Real GDP growth, q/q annualized %", "quarterly", 23, revised=True),
    MacroSeries("BAMLH0A0HYM2", "High-yield corporate OAS", "daily", 1),
    MacroSeries("DTWEXBGS", "Broad trade-weighted US dollar index", "daily", 5),
    MacroSeries("DCOILWTICO", "WTI crude oil spot price", "daily", 7),
)

DEFAULT_PUT_CALL_TYPES: tuple[str, ...] = ("Equity",)

_TITLE = re.compile(r"^(?P<title>.+) \((?P<id>[^()]+)\)\s*$")
_SUBTITLE = re.compile(r"^Units: (?P<units>.*) \| Frequency: (?P<freq>.*) \| Seasonal Adj: (?P<sa>.*)$")


# --------------------------------------------------------------------------------------
# Date helpers
# --------------------------------------------------------------------------------------


def minus_months(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 - months, 12)
    m += 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def add_business_days(d: date, n: int) -> date:
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def period_end(d: date, frequency: Frequency) -> date:
    """FRED dates monthly/quarterly observations by period start; daily/weekly by the day itself."""
    if frequency == "monthly":
        return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
    if frequency == "quarterly":
        return minus_months(date(d.year, d.month, 1), -3) - timedelta(days=1)
    return d


def available_on(d: date, frequency: Frequency, lag_bdays: int) -> date:
    return add_business_days(period_end(d, frequency), lag_bdays)


# --------------------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------------------


def parse_indicator(text: str) -> tuple[list[tuple[date, float]], dict[str, Any]]:
    """Parse a ``GetEconomicIndicator`` answer (FredTools.GetEconomicIndicator).

    Shape: ``{Title} ({SeriesId})`` / ``Units: .. | Frequency: .. | Seasonal Adj: ..`` /
    blank / ``| Date | Value |`` table, ascending, "N/A" for missing values.
    Any other text (unknown series, empty range) comes back as ``meta["message"]``.
    """
    meta: dict[str, Any] = {}
    lines = text.strip().splitlines()
    if lines and (m := _TITLE.match(lines[0].strip())):
        meta["title"] = m.group("title")
    if len(lines) > 1 and (m := _SUBTITLE.match(lines[1].strip())):
        meta["units"], meta["fred_frequency"], meta["seasonal_adjustment"] = m.group("units", "freq", "sa")
    rows = find_table(text, {"Date", "Value"})
    if rows is None:
        meta["message"] = text.strip()[:300]
        return [], meta
    obs = []
    for r in rows:
        v = number(r["Value"])
        try:
            d = date.fromisoformat(r["Date"])
        except ValueError:
            continue
        if v is not None:
            obs.append((d, float(v)))
    return sorted(obs), meta


def parse_dated_column(text: str, column: str) -> tuple[list[tuple[date, float]], str | None]:
    """Parse a CBOE table (Date + ``column``), returning (rows, message-if-no-table)."""
    rows = find_table(text, {"Date", column})
    if rows is None:
        return [], text.strip()[:300]
    out = []
    for r in rows:
        v = number(r[column])
        try:
            d = date.fromisoformat(r["Date"])
        except ValueError:
            continue
        if v is not None:
            out.append((d, float(v)))
    return sorted(out), None


def parse_calendar(text: str) -> tuple[list[dict[str, Any]], str | None]:
    """Parse ``GetEconomicCalendar`` (FredTools.GetEconomicCalendar): Date | Release | Importance | Series Updated."""
    rows = find_table(text, {"Date", "Release", "Importance", "Series Updated"})
    if rows is None:
        return [], text.strip()[:300]
    out = []
    for r in rows:
        try:
            d = date.fromisoformat(r["Date"])
        except ValueError:
            continue
        out.append({"date": d.isoformat(), "release": r["Release"], "importance": r["Importance"],
                    "series": [s.strip() for s in r["Series Updated"].split(",") if s.strip()]})
    note = None
    if "truncated at" in text:
        note = "Calendar truncated by the tool's row cap; later dates may be missing."
    return out, note


# --------------------------------------------------------------------------------------
# Transforms and trend
# --------------------------------------------------------------------------------------


def transform(obs: list[tuple[date, float]], how: Transform) -> list[tuple[date, float]]:
    if how == "level":
        return obs
    if how == "change":
        return [(d, round(v - pv, 6)) for (_, pv), (d, v) in zip(obs, obs[1:])]
    by_date = dict(obs)
    out = []
    for d, v in obs:
        base = by_date.get(minus_months(d, 12))
        if base:
            out.append((d, round((v / base - 1) * 100, 2)))
    return out


def value_at(obs: list[tuple[date, float]], on_or_before: date) -> tuple[date, float] | None:
    best = None
    for d, v in obs:
        if d <= on_or_before:
            best = (d, v)
        else:
            break
    return best


def summarize(obs: list[tuple[date, float]], frequency: Frequency) -> dict[str, Any] | None:
    """Latest value plus the value 1 and 3 months earlier (1 and 2 quarters for quarterly)."""
    if not obs:
        return None
    last_d, last_v = obs[-1]
    out: dict[str, Any] = {"date": last_d.isoformat(), "value": last_v}
    offsets = ((3, "prior_quarter"), (6, "two_quarters_ago")) if frequency == "quarterly" \
        else ((1, "1m_ago"), (3, "3m_ago"))
    for months, key in offsets:
        if hit := value_at(obs, minus_months(last_d, months)):
            out[key] = {"date": hit[0].isoformat(), "value": hit[1]}
    return out


# --------------------------------------------------------------------------------------
# Provider
# --------------------------------------------------------------------------------------


REVISION_NOTE = (
    "Backtest: FRED values are the LATEST REVISED values, not what was published at this "
    "date (ALFRED vintages are not available). Revised series in this snapshot: {revised}. "
    "Market-priced series that are not revised: {unrevised}. Visibility uses each series' "
    "typical publication lag; releases delayed beyond it could still leak."
)


class EquiblesMacro:
    """``MacroProvider`` over Equibles' hosted MCP (FRED and CBOE tools).

    ``mcp`` is any McpToolCaller, e.g. ``HttpMcpClient(EQUIBLES_MCP_URL,
    allowed_tools=EquiblesMacro.TOOLS, headers={"Authorization": f"Bearer {key}"})``.
    Calls per ``macro()``: ``len(series) + 1 (VIX) + len(put_call_types) + 1 (calendar)``,
    16 with the defaults.
    """

    TOOLS: frozenset[str] = frozenset({INDICATOR_TOOL, CALENDAR_TOOL, VIX_TOOL, PUT_CALL_TOOL})

    def __init__(self, mcp: McpToolCaller, *, series: Sequence[MacroSeries] = DEFAULT_SERIES,
                 put_call_types: Sequence[str] = DEFAULT_PUT_CALL_TYPES, calendar_days: int = 14,
                 calendar_min_importance: str = "medium", max_parallel: int = 4,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self._mcp = mcp
        self._series = list(series)
        self._put_call_types = list(put_call_types)
        self._calendar_days = calendar_days
        self._min_importance = calendar_min_importance
        self._sem = asyncio.Semaphore(max_parallel)
        self._now = now

    async def _call(self, tool: str, args: dict[str, Any]) -> tuple[str | None, str | None]:
        """(text, error). Tool faults surface as exceptions from HttpMcpClient; keep them per-item."""
        try:
            async with self._sem:
                return await self._mcp.call_tool(tool, args), None
        except Exception as e:  # noqa: BLE001 - one failing series must not sink the snapshot
            return None, f"{tool} failed: {e}"[:300]

    async def macro(self, as_of: datetime) -> list[DataSnapshot]:
        cutoff = visible_before(as_of)  # rows must become public on an earlier Eastern day
        backtest = as_of < self._now() - timedelta(days=1)
        indicators, volatility, cal = await asyncio.gather(
            self._indicators(as_of, cutoff, backtest), self._volatility(as_of, cutoff),
            self._calendar(as_of, cutoff))
        return [indicators, volatility, cal]

    # -- FRED ---------------------------------------------------------------------------

    async def _series_item(self, s: MacroSeries, cutoff: date) -> tuple[dict[str, Any] | None, str | None]:
        # Enough history for the 3-month (or 2-quarter) trend, plus 12 months for YoY.
        months = (6 if s.frequency == "quarterly" else 3) + (12 if s.transform == "yoy" else 0) + 3
        args = {"seriesId": s.series_id, "startDate": minus_months(cutoff, months).isoformat(),
                "endDate": cutoff.isoformat(), "maxResults": 500}
        text, err = await self._call(INDICATOR_TOOL, args)
        if err:
            return None, f"{s.series_id}: {err}"
        raw, meta = parse_indicator(text)
        visible = [(d, v) for d, v in raw
                   if available_on(d, s.frequency, s.release_lag_bdays) < cutoff]
        summary = summarize(transform(visible, s.transform), s.frequency)
        if summary is None:
            return None, f"{s.series_id}: {meta.get('message') or 'no observation visible at this date'}"
        units = meta.get("units")
        if s.transform == "yoy":
            units = "Percent change from a year earlier"
        elif s.transform == "change" and units:
            units = f"{units}, change from previous observation"
        item = {"series": s.series_id, "label": s.label, "units": units, "frequency": s.frequency,
                "revised_by_source": s.revised, **summary}
        if s.transform != "level" and visible:
            item["level"] = {"date": visible[-1][0].isoformat(), "value": visible[-1][1]}
        return {k: v for k, v in item.items() if v is not None}, None

    async def _indicators(self, as_of: datetime, cutoff: date, backtest: bool) -> DataSnapshot:
        results = await asyncio.gather(*(self._series_item(s, cutoff) for s in self._series))
        items = [i for i, _ in results if i]
        notes = [n for _, n in results if n]
        snap_note = ""
        if backtest:
            revised = ", ".join(s.series_id for s in self._series if s.revised) or "none"
            unrevised = ", ".join(s.series_id for s in self._series if not s.revised) or "none"
            snap_note = REVISION_NOTE.format(revised=revised, unrevised=unrevised)
        if not items:
            return DataSnapshot(kind="macro:indicators", source="equibles", subject="market", as_of=as_of,
                                is_gap=True, note="; ".join(notes) or "No FRED data from Equibles.")
        return DataSnapshot(
            kind="macro:indicators", source="equibles", subject="market", as_of=as_of, note=snap_note,
            payload={
                "basis": "FRED via Equibles; latest observation whose period ended and whose typical "
                         "release date passed before this date. Dates are FRED observation dates "
                         "(period start for monthly/quarterly series).",
                "latest_revised_values": backtest,
                "series": items,
                "notes": notes,
            },
        )

    # -- CBOE ---------------------------------------------------------------------------

    async def _volatility(self, as_of: datetime, cutoff: date) -> DataSnapshot:
        start = minus_months(cutoff, 4).isoformat()
        rng = {"startDate": start, "endDate": cutoff.isoformat(), "maxResults": 500}
        calls: list[tuple[str, dict[str, Any], str, str, str]] = [(VIX_TOOL, dict(rng), "Close", "vix", "CBOE Volatility Index (VIX) close")]
        calls += [(PUT_CALL_TOOL, {"type": t, **rng}, "P/C Ratio", f"put_call_{t.lower()}",
                   f"CBOE {t} put/call ratio") for t in self._put_call_types]
        answers = await asyncio.gather(*(self._call(tool, args) for tool, args, *_ in calls))

        items: dict[str, Any] = {}
        notes: list[str] = []
        for (tool, args, column, key, label), (text, err) in zip(calls, answers):
            if err:
                notes.append(f"{key}: {err}")
                continue
            rows, msg = parse_dated_column(text, column)
            # Daily closes are public the same evening; keep only earlier Eastern days.
            rows = [(d, v) for d, v in rows if d < cutoff]
            summary = summarize(rows, "daily")
            if summary is None:
                notes.append(f"{key}: {msg or 'no observation visible at this date'}")
                continue
            if key.startswith("put_call"):
                recent = [v for _, v in rows[-20:]]
                summary["avg_last_20"] = round(sum(recent) / len(recent), 3)
            items[key] = {"label": label, **summary}
        if not items:
            return DataSnapshot(kind="macro:volatility", source="equibles", subject="market", as_of=as_of,
                                is_gap=True, note="; ".join(notes) or "No CBOE data from Equibles.")
        return DataSnapshot(kind="macro:volatility", source="equibles", subject="market", as_of=as_of,
                            payload={"basis": "CBOE via Equibles; daily values dated before this date "
                                              "(market-priced, never revised)", **items, "notes": notes})

    # -- Calendar -----------------------------------------------------------------------

    async def _calendar(self, as_of: datetime, cutoff: date) -> DataSnapshot:
        start = cutoff  # the as_of day, US/Eastern
        end = start + timedelta(days=self._calendar_days)
        text, err = await self._call(CALENDAR_TOOL, {
            "startDate": start.isoformat(), "endDate": end.isoformat(),
            "minImportance": self._min_importance, "maxResults": 500})
        if err:
            return DataSnapshot(kind="macro:calendar", source="equibles", subject="market", as_of=as_of,
                                is_gap=True, note=err)
        releases, msg = parse_calendar(text)
        releases = [r for r in releases if start.isoformat() <= r["date"] <= end.isoformat()]
        if not releases and msg and not msg.startswith("No economic releases"):
            return DataSnapshot(kind="macro:calendar", source="equibles", subject="market", as_of=as_of,
                                is_gap=True, note=msg)
        notes = [msg] if msg and releases else []
        return DataSnapshot(
            kind="macro:calendar", source="equibles", subject="market", as_of=as_of,
            payload={
                "basis": f"Scheduled US economic releases (FRED release calendar via Equibles), "
                         f"{start.isoformat()} to {end.isoformat()}, importance >= {self._min_importance}. "
                         "Dates only, no values. FOMC meetings are not included. Past windows show "
                         "the dates as finally held, so a later rescheduling can show up in backtests.",
                "releases": releases,
                "notes": notes,
            },
        )
