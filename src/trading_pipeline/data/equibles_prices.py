"""Daily prices, derived weekly bars, local technicals and last-close quotes from Equibles.

Source tools (open-source Equibles, ``src/Equibles.Yahoo.Mcp/Tools/StockPriceTools.cs``):

* ``GetStockPrices(ticker, startDate, endDate, maxResults<=500)``: daily OHLCV, oldest
  first, newest rows kept when truncated, zero-volume days excluded. An ``Adj Close``
  column appears when it differs from Close.
* ``GetLatestClosingPrices(tickers[])``: newest settled daily close per ticker.

Intervals: "1d" comes straight from ``GetStockPrices``; "1w" is aggregated locally
(Monday-Friday weeks); "1h" has no open-source tool (intraday bars are Equibles
Cloud-only, tool reference not available), so it is an explicit gap.

Point-in-time: a daily bar dated D counts as known only from D 16:00 US/Eastern (the
close). Rows after ``as_of`` are dropped after parsing, not just by the request's
``endDate``, and every indicator/pivot is computed from those filtered bars only.

Split/dividend basis (investigated in the Equibles source): prices come from Yahoo's
chart API (``YahooFinanceClient.GetChart``), whose OHLC are split-adjusted but not
dividend-adjusted, and ``Adj Close`` is split+dividend-adjusted. When Equibles captures a
split or cash dividend, ``CorporateActionPriceReconciliationManager`` triggers a
full-history refresh of the series, so stored history is restated to the split basis
current at the last refresh. Equibles itself warns the rows "do not certify which split
basis the provider returned". No MCP tool exposes split events, so bars cannot be
restated to the ``as_of`` basis here. Consequences, flagged in every backtest snapshot:
absolute price levels and volumes before a split that happened after ``as_of`` are on
the later basis (a look-ahead of the split); returns and indicator shapes are
unaffected. ``Adj Close`` is never used: it would also leak later dividends.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from . import technicals as ta
from .base import DataSnapshot, PriceBar
from .equibles_md import find_table, number, tables
from .mcp import McpToolCaller

EASTERN = ZoneInfo("America/New_York")
PRICES_TOOL = "GetStockPrices"
LATEST_CLOSE_TOOL = "GetLatestClosingPrices"
MAX_RESULTS = 500  # McpLimit.MaxResults

_TITLE = re.compile(r"^Daily prices for (?P<title>.+):\s*$", re.M)
_TRUNCATED = re.compile(r"_Showing the newest (\d+) of (\d+) records")

BASIS = ("Equibles GetStockPrices daily bars (Yahoo source): OHLC split-adjusted, not dividend-adjusted; "
         "zero-volume days excluded; a bar is included once its session has closed (16:00 ET).")
BACKTEST_SPLIT_NOTE = (
    "Backtest caveat: Equibles restates the whole price history after each split, so these bars use the "
    "split basis current when Equibles last refreshed, not the basis as of this date. If the stock split "
    "after this date, absolute price levels and volumes are on the post-split basis (percent moves and "
    "indicator shapes are unaffected). Equibles exposes no split events, so this can't be corrected here; "
    "don't compare these levels with prices or per-share figures quoted at the time.")
INTRADAY_GAP = ("Intraday (1h) bars are not available: they exist only on Equibles Cloud, whose tool "
                "reference isn't available yet. Use the 1d/1w charts.")


def session_close(d: date) -> datetime:
    """The moment a daily bar dated ``d`` becomes known: 16:00 US/Eastern, as UTC."""
    return datetime.combine(d, time(16, 0), EASTERN).astimezone(timezone.utc)


def _eastern_date(as_of: datetime) -> date:
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    return as_of.astimezone(EASTERN).date()


def parse_price_table(text: str) -> tuple[list[PriceBar], dict[str, Any]]:
    """Parse a GetStockPrices answer into daily bars (ts = session close) plus metadata."""
    meta: dict[str, Any] = {"title": None, "truncated": False, "adj_close": False}
    if m := _TITLE.search(text):
        meta["title"] = m.group("title")
    if _TRUNCATED.search(text):
        meta["truncated"] = True
    rows = find_table(text, {"Date", "Open", "High", "Low", "Close", "Volume"})
    if rows is None:
        meta["message"] = text.strip()[:300]
        return [], meta
    bars = []
    for r in rows:
        try:
            d = date.fromisoformat(r["Date"])
        except ValueError:
            continue
        vals = [number(r[c]) for c in ("Open", "High", "Low", "Close", "Volume")]
        if any(v is None for v in vals):
            continue
        o, h, lo, c, v = (float(x) for x in vals)  # type: ignore[arg-type]
        bars.append(PriceBar(ts=session_close(d), open=o, high=h, low=lo, close=c, volume=v))
        meta["adj_close"] |= "Adj Close" in r
    return bars, meta


def parse_latest_closes(text: str) -> dict[str, dict[str, Any]]:
    """Parse a GetLatestClosingPrices answer: ticker -> row (placeholder rows have no price)."""
    rows = find_table(text, {"Ticker", "Date", "Close"}) or []
    out = {}
    for r in rows:
        price = number(r["Close"])
        try:
            d = date.fromisoformat(r["Date"])
        except ValueError:
            d = None
        out[r["Ticker"].upper()] = {
            "price": float(price) if price is not None and d else None,
            "date": d,
            "status": r["Close"] if price is None or d is None else None,
            "change_pct": _float(r.get("Change %")),
            "volume": _float(r.get("Volume")),
            "high_52w": _float(r.get("52W High")),
            "low_52w": _float(r.get("52W Low")),
        }
    return out


def _float(cell: str | None) -> float | None:
    v = number(cell.replace("\\*", "") if cell else cell)
    return float(v) if v is not None else None


def _row(b: PriceBar) -> list[Any]:
    return [b.ts.astimezone(EASTERN).date().isoformat(), b.open, b.high, b.low, b.close, b.volume]


class EquiblesPrices:
    """``PriceDataProvider`` over the hosted Equibles MCP (daily prices + local technicals).

    Budget: one ``GetStockPrices`` call per ``chunk_days`` window (default ~600 calendar
    days, under the 500-row cap). Daily history is cached per (ticker, as_of date), so the
    ohlcv/indicators/pivots trio for one chart costs one or two calls, and the 1w chart
    reuses the daily bars. Indicators look back ``indicator_days`` (enough for SMA 200 on
    that interval).
    """

    TOOLS: frozenset[str] = frozenset({PRICES_TOOL})
    INTERVALS = ("1h", "1d", "1w")
    PIVOT_PERIODS = {"1d": ("day", "week", "month"), "1w": ("week", "month", "year")}

    def __init__(self, mcp: McpToolCaller, *, chunk_days: int = 600, max_parallel: int = 4,
                 indicator_days: dict[str, int] | None = None, pivot_days: dict[str, int] | None = None,
                 cache_size: int = 64,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self._mcp = mcp
        self._chunk = timedelta(days=chunk_days)
        self._sem = asyncio.Semaphore(max_parallel)
        self._indicator_days = {"1d": 450, "1w": 1500, **(indicator_days or {})}
        self._pivot_days = {"1d": 200, "1w": 800, **(pivot_days or {})}
        self._cache: dict[tuple[str, date], tuple[date, list[PriceBar], dict[str, Any]]] = {}
        self._cache_size = cache_size
        self._now = now

    # ---------------------------------------------------------------- fetching

    async def _fetch(self, ticker: str, start: date, end: date) -> tuple[list[PriceBar], dict[str, Any]]:
        args = {"ticker": ticker, "startDate": start.isoformat(), "endDate": end.isoformat(),
                "maxResults": MAX_RESULTS}
        async with self._sem:
            text = await self._mcp.call_tool(PRICES_TOOL, args)
        return parse_price_table(str(text))

    async def _fetch_range(self, ticker: str, start: date, end: date) -> tuple[list[PriceBar], dict[str, Any]]:
        windows = []
        s = start
        while s <= end:
            e = min(end, s + self._chunk - timedelta(days=1))
            windows.append((s, e))
            s = e + timedelta(days=1)
        results = await asyncio.gather(*(self._fetch(ticker, s, e) for s, e in windows))
        bars: list[PriceBar] = []
        meta: dict[str, Any] = {"title": None, "notes": []}
        for (s, e), (b, m) in zip(windows, results):
            bars += b
            meta["title"] = meta["title"] or m["title"]
            if m.get("truncated"):
                meta["notes"].append(f"Equibles truncated {s}..{e}; older bars in that window are missing.")
            if "message" in m and m["message"] not in meta.setdefault("messages", []):
                meta["messages"].append(m["message"])
        return bars, meta

    async def _daily(self, ticker: str, start: date, as_of: datetime) -> tuple[list[PriceBar], dict[str, Any]]:
        """Daily bars with start <= date and session close <= as_of, oldest first."""
        end = _eastern_date(as_of)
        key = (ticker.upper(), end)
        cached = self._cache.get(key)
        if cached is None:
            bars, meta = await self._fetch_range(ticker, start, end)
            fetched_from = start
        else:
            fetched_from, bars, meta = cached
            if start < fetched_from:
                more, more_meta = await self._fetch_range(ticker, start, fetched_from - timedelta(days=1))
                bars = more + bars
                meta = {"title": meta["title"] or more_meta["title"],
                        "notes": meta["notes"] + more_meta["notes"],
                        "messages": meta.get("messages", []) + more_meta.get("messages", [])}
                fetched_from = start
        by_date = {b.ts: b for b in bars}
        bars = [by_date[t] for t in sorted(by_date)]
        if len(self._cache) >= self._cache_size and key not in self._cache:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = (fetched_from, bars, meta)
        start_ts = datetime.combine(start, time(0), EASTERN)
        return [b for b in bars if start_ts <= b.ts <= as_of], meta

    async def _interval_bars(self, ticker: str, start: date, as_of: datetime, interval: str):
        if interval == "1w":
            start = start - timedelta(days=start.weekday())  # whole first week
        daily, meta = await self._daily(ticker, start, as_of)
        bars = ta.weekly_bars(daily) if interval == "1w" else daily
        return bars, daily, meta

    # ---------------------------------------------------------------- snapshot helpers

    def _check_interval(self, interval: str) -> None:
        if interval not in self.INTERVALS:
            raise ValueError(f"unsupported interval {interval!r}; expected one of {self.INTERVALS}")

    def _notes(self, as_of: datetime, meta: dict[str, Any], bars: list[PriceBar], interval: str) -> list[str]:
        notes = list(meta.get("notes", []))
        if as_of < self._now() - timedelta(days=1):
            notes.append(BACKTEST_SPLIT_NOTE)
        if interval == "1w" and bars:
            last = bars[-1].ts.astimezone(EASTERN).date()
            friday = last + timedelta(days=4 - last.weekday())
            if last < friday and _eastern_date(as_of) <= friday:
                notes.append(f"The latest weekly bar is partial (sessions through {last.isoformat()}).")
        return notes

    def _gap(self, kind: str, ticker: str, as_of: datetime, interval: str, note: str) -> DataSnapshot:
        return DataSnapshot(kind=f"{kind}:{interval}", source="equibles", subject=ticker, as_of=as_of,
                            is_gap=True, note=note)

    def _no_data(self, ticker: str, meta: dict[str, Any]) -> str:
        return "; ".join(meta.get("messages", [])) or f"No Equibles price data for {ticker} up to this date."

    # ---------------------------------------------------------------- PriceDataProvider

    async def bars(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> list[PriceBar]:
        self._check_interval(interval)
        if interval == "1h":
            return []
        bars, _, _ = await self._interval_bars(ticker, start, as_of, interval)
        return bars

    async def ohlcv(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        self._check_interval(interval)
        if interval == "1h":
            return self._gap("ohlcv", ticker, as_of, interval, INTRADAY_GAP)
        bars, _, meta = await self._interval_bars(ticker, start, as_of, interval)
        if not bars:
            return self._gap("ohlcv", ticker, as_of, interval, self._no_data(ticker, meta))
        return DataSnapshot(kind=f"ohlcv:{interval}", source="equibles", subject=ticker, as_of=as_of, payload={
            "listing": meta.get("title"),
            "interval": interval,
            "basis": BASIS + (" Weekly bars aggregated from daily (Mon-Fri); date = last session."
                              if interval == "1w" else ""),
            "columns": ["date", "o", "h", "l", "c", "v"],
            "rows": [_row(b) for b in bars],
            "notes": self._notes(as_of, meta, bars, interval),
        })

    async def indicators(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        self._check_interval(interval)
        if interval == "1h":
            return self._gap("indicators", ticker, as_of, interval, INTRADAY_GAP)
        start = _eastern_date(as_of) - timedelta(days=self._indicator_days[interval])
        bars, _, meta = await self._interval_bars(ticker, start, as_of, interval)
        if not bars:
            return self._gap("indicators", ticker, as_of, interval, self._no_data(ticker, meta))
        return DataSnapshot(kind=f"indicators:{interval}", source="equibles", subject=ticker, as_of=as_of, payload={
            "listing": meta.get("title"),
            "interval": interval,
            "basis": "Computed locally from the bars below this date. " + BASIS,
            **ta.indicator_summary(bars),
            "notes": self._notes(as_of, meta, bars, interval),
        })

    async def pivots(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        self._check_interval(interval)
        if interval == "1h":
            return self._gap("pivots", ticker, as_of, interval, INTRADAY_GAP)
        start = _eastern_date(as_of) - timedelta(days=self._pivot_days[interval])
        bars, daily, meta = await self._interval_bars(ticker, start, as_of, interval)
        if not bars:
            return self._gap("pivots", ticker, as_of, interval, self._no_data(ticker, meta))
        return DataSnapshot(kind=f"pivots:{interval}", source="equibles", subject=ticker, as_of=as_of, payload={
            "listing": meta.get("title"),
            "interval": interval,
            "basis": ("Classic floor pivots from each completed prior period, plus swing highs/lows "
                      f"(fractals) on {interval} bars. " + BASIS),
            **ta.pivot_summary(bars, daily, self.PIVOT_PERIODS[interval], _eastern_date(as_of)),
            "notes": self._notes(as_of, meta, bars, interval),
        })


LIVE_QUOTE_TOOL = "GetLiveQuote"


def parse_live_quotes(text: str) -> dict[str, dict[str, Any]]:
    """GetLiveQuote (Equibles Cloud, paid plans) -> {TICKER: {price, timestamp, stale}}.

    Verified against real Free (upgrade notice, no table) and Pro (Ticker/Price/As of
    (UTC)/Stale table) answers. Accepts a table only when it has a ticker column and a
    last-trade/price column, and returns {} otherwise; callers then fall back to the last
    close.
    """
    for rows in tables(text or ""):
        if not rows:
            continue
        cols = list(rows[0])
        tcol = next((c for c in cols if c.lower().startswith("ticker") or c.lower() == "symbol"), None)
        pcol = next((c for c in cols if "last" in c.lower() or c.lower() == "price"), None)
        if tcol is None or pcol is None:
            continue
        tscol = next((c for c in cols if "time" in c.lower() or "utc" in c.lower()), None)
        stcol = next((c for c in cols if "stale" in c.lower()), None)
        out = {}
        for r in rows:
            price = number(r[pcol])
            if price is None:
                continue
            out[r[tcol].strip().upper()] = {
                "price": float(price),
                "timestamp": r[tscol] if tscol else None,
                "stale": (r[stcol].strip().lower() in ("true", "yes", "stale")) if stcol else None,
            }
        return out
    return {}


class EquiblesQuotes:
    """``QuoteProvider`` from Equibles. READ-ONLY; there are no order methods by design.

    ``quote`` first asks ``GetLiveQuote`` (Equibles Plus: 15-minute delayed, Pro: real-time,
    consolidated SIP). On the Free plan, or whenever the answer isn't a recognisable quote
    table or the quote is stale, it falls back to the latest settled daily close from
    ``GetLatestClosingPrices``, labelled as such and saying why. ``positions`` is always a
    gap: this system has no brokerage account.
    """

    TOOLS: frozenset[str] = frozenset({LIVE_QUOTE_TOOL, LATEST_CLOSE_TOOL})

    def __init__(self, mcp: McpToolCaller, *,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self._mcp = mcp
        self._now = now

    async def quote(self, ticker: str) -> DataSnapshot:
        now = self._now()
        why_not_live = None
        try:
            live_text = str(await self._mcp.call_tool(LIVE_QUOTE_TOOL, {"tickers": [ticker]}))
            live = parse_live_quotes(live_text).get(ticker.upper())
            if live is not None and not live["stale"]:
                return DataSnapshot(kind="quote", source="equibles", subject=ticker, as_of=now, payload={
                    "price": live["price"], "timestamp": live["timestamp"],
                    "basis": "live quote (Equibles GetLiveQuote: consolidated SIP; 15-min delayed on Plus)",
                })
            why_not_live = ("live quote is stale" if live is not None
                            else (live_text.strip().splitlines() or ["no live quote"])[0][:160])
        except Exception as e:
            why_not_live = f"{LIVE_QUOTE_TOOL} failed: {e}"[:160]
        text = await self._mcp.call_tool(LATEST_CLOSE_TOOL, {"tickers": [ticker]})
        row = parse_latest_closes(str(text)).get(ticker.upper())
        if row is None or row["price"] is None:
            reason = row["status"] if row else str(text).strip()[:200]
            return DataSnapshot(kind="quote", source="equibles", subject=ticker, as_of=now, is_gap=True,
                                note=f"No Equibles close for {ticker}: {reason}")
        closed = session_close(row["date"])
        return DataSnapshot(kind="quote", source="equibles", subject=ticker, as_of=min(closed, now), payload={
            "price": row["price"],
            "as_of_date": row["date"].isoformat(),
            "basis": "last close (EOD), not live",
            "why_not_live": why_not_live,
            "change_pct": row["change_pct"],
            "volume": row["volume"],
            "high_52w_close": row["high_52w"],
            "low_52w_close": row["low_52w"],
        })

    async def positions(self) -> DataSnapshot:
        return DataSnapshot(kind="positions", source="unavailable", subject="account", as_of=self._now(),
                            is_gap=True, note="No brokerage account is connected (by design: decision support only).")
