"""Sector performance, bulk sector screen and sector breadth from the hosted Equibles MCP.

``EquiblesSectorData`` implements ``SectorDataProvider`` with three open-source Equibles
tools (checked against the Equibles source, ``src/Equibles.*.Mcp/Tools``):

* ``GetStockPrices`` (Yahoo daily bars, ``StockPriceTools.cs``). ETFs are covered: the
  Yahoo importer fetches full history for listings in the exchange-traded reference feed
  (``YahooPriceImportService``, ``SecondaryTickerPolicy.IsExchangeTradedListing``).
* ``GetFundProfile`` (``FundDirectoryTools.cs``): a fund's largest holdings from its
  **latest** Form NPORT-P report. Used for sector constituents (the sector ETF's holdings).
* ``GetInstitutionPortfolio`` (``InstitutionalHoldingsTools.cs``): a 13F book, used only as
  a company-name -> ticker dictionary, because NPORT holding rows carry a name and CUSIP but
  no ticker, and no open-source tool maps a CUSIP to a ticker.

Sectors. Agent 0 names sectors in free text. ``resolve_sector`` maps a name to one of the 11
GICS sectors and its Select Sector SPDR ETF. Industry-level names ("Biotech", "Banks",
"Semiconductors") map to their **parent** sector: the screen then covers the whole parent
sector (e.g. all of health care for "Biotech"), and the payload says so (``mapped_via``).
Names that match nothing, or match several sectors equally well, return gap snapshots.

Constituents: trade-offs of the options found in the source.

* Sector ETF holdings via ``GetEtfHoldings`` (Equibles Cloud; primary, since its rows carry
  tickers), falling back to ``GetFundProfile`` when an ETF isn't covered.
* Sector ETF holdings via ``GetFundProfile`` (the open-source fallback). Real weights and a report date, but
  the tool only serves the latest report (no report-date parameter). A report is used only
  if it would have been public by ``as_of`` (period end + ``nport_lag_days``, default 60:
  NPORT-P is due 60 days after quarter end). Older backtests therefore get gap snapshots;
  reconstructing past constituents needs a dated-holdings tool that Equibles does not expose.
* ``GetFundsHoldingStock``: inverse lookup, also latest-report only; needs a candidate list.
* Issuer industry/sector classification exists in Equibles (``GetInstitutionSectorAllocation``
  groups 13F books by it) but no tool lists the members of a sector.
* The Equibles Cloud stock screener is not in the open-source server: its tool name and
  format are unknown, so key ratios and size are reported as an explicit gap.

Ticker mapping. Each ETF holding name is normalised ("Home Depot Inc/The" -> "home depot") and
matched against the company names in a broad 13F book (default: The Vanguard Group, CIK
102909, whose book spans nearly every US-listed stock), for the latest quarter-end at least
45 days (the 13F filing window) before ``as_of``. ``cusip_tickers`` overrides the match. A
name matching several listings (share classes) takes the largest position and lists the
others in ``ticker_candidates``. Unmatched holdings are listed in the coverage snapshot.

Point-in-time rules.

* A daily bar dated D is visible from 16:00 US/Eastern on D. Rows after that are dropped
  after parsing, not only by the request's ``endDate``.
* Ratio metrics (returns, distance from moving averages and 52-week high/low) use Adj Close.
  Back-adjustment scales every earlier bar by the same factor, so ratios inside the window do
  not change when a split or dividend happens after ``as_of``. Absolute prices (``last_close``)
  are raw closes. Share volumes may be restated to a later split basis; dollar volume
  (Adj Close x Volume) is not affected by splits.
* Survivorship: constituents from a past NPORT report are point-in-time, but prices come from
  Yahoo, where delisted names may be missing. Backtest snapshots say so and list the names
  without prices.

Call budget (hosted MCP):

* ``market_overview``: 12 ``GetStockPrices`` calls (SPY + 11 ETFs), plus 1-2 if SPY is
  missing (IVV, VOO fallbacks).
* ``sector_screen``: 1 ``GetEtfHoldings`` (or ``GetFundProfile``) + ``max_constituents`` (default 25)
  ``GetStockPrices`` + 1 for the ETF (reused from ``market_overview`` for the same ``as_of``),
  plus, only for holdings without a ticker, the 13F name map: 1-``ticker_map_max_pages``
  calls of 500 rows, fetched once per provider instance and ``as_of``, shared by every sector. About 27 calls per sector.
* ``sector_breadth``: 0 extra calls after ``sector_screen`` for the same sector and ``as_of``
  (results are cached per instance); otherwise the same as ``sector_screen``.

Decision support only: every tool used is read-only (``TOOLS`` is the allowlist).
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from statistics import mean
from typing import Any
from zoneinfo import ZoneInfo

from .base import DataSnapshot
from .equibles_md import find_table, number
from .mcp import McpToolCaller

EASTERN = ZoneInfo("America/New_York")
MARKET_CLOSE = time(16, 0)

PRICES_TOOL = "GetStockPrices"
ETF_TOOL = "GetEtfHoldings"
FUND_TOOL = "GetFundProfile"
PORTFOLIO_TOOL = "GetInstitutionPortfolio"

BENCHMARKS: tuple[str, ...] = ("SPY", "IVV", "VOO")
VANGUARD_CIK = "102909"
_PAGE = 500  # McpLimit.MaxResults in the Equibles source


# --------------------------------------------------------------------------------------
# Sector map
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Sector:
    name: str
    etf: str
    aliases: tuple[str, ...]  # sector synonyms and industries that roll up to this sector


SECTORS: tuple[Sector, ...] = (
    Sector("Information Technology", "XLK", (
        "information technology", "technology", "tech", "it", "software", "saas", "cloud",
        "semiconductors", "semiconductor", "semis", "chips", "hardware", "tech hardware",
        "it services", "cybersecurity")),
    Sector("Financials", "XLF", (
        "financials", "financial", "financial services", "banks", "banking", "regional banks",
        "insurance", "insurers", "capital markets", "brokers", "asset managers",
        "asset management", "payments", "consumer finance")),
    Sector("Health Care", "XLV", (
        "health care", "healthcare", "biotech", "biotechnology", "pharma", "pharmaceuticals",
        "drugmakers", "medical devices", "medtech", "life sciences", "managed care",
        "health insurers", "hospitals")),
    Sector("Energy", "XLE", (
        "energy", "oil", "oil and gas", "gas", "exploration and production", "e and p",
        "oilfield services", "refiners", "refining", "midstream", "pipelines")),
    Sector("Industrials", "XLI", (
        "industrials", "industrial", "aerospace", "defense", "aerospace and defense",
        "airlines", "transportation", "transports", "railroads", "trucking", "machinery",
        "construction and engineering", "building products", "logistics")),
    Sector("Consumer Discretionary", "XLY", (
        "consumer discretionary", "discretionary", "retail", "retailers", "autos",
        "automobiles", "automakers", "electric vehicles", "homebuilders", "restaurants",
        "leisure", "travel", "hotels", "e commerce", "ecommerce", "apparel")),
    Sector("Consumer Staples", "XLP", (
        "consumer staples", "staples", "food", "beverages", "food and beverage",
        "household products", "personal products", "tobacco", "grocery", "supermarkets")),
    Sector("Utilities", "XLU", (
        "utilities", "utility", "electric utilities", "power", "water utilities",
        "independent power producers")),
    Sector("Materials", "XLB", (
        "materials", "basic materials", "chemicals", "metals", "metals and mining", "mining",
        "steel", "gold miners", "construction materials", "packaging")),
    Sector("Real Estate", "XLRE", (
        "real estate", "reits", "reit", "real estate investment trusts")),
    Sector("Communication Services", "XLC", (
        "communication services", "communications", "telecom", "telecommunications",
        "media", "interactive media", "entertainment", "social media", "streaming",
        "advertising")),
)

_FILLER = {"sector", "sectors", "industry", "industries", "stocks", "names", "space", "group",
           "us", "the", "sub"}


def _words(text: str) -> str:
    t = text.lower().replace("&", " and ").replace("-", " ").replace("/", " ")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def resolve_sector(name: str) -> tuple[Sector | None, str]:
    """Map free text to a sector. Returns (sector, how) or (None, reason).

    ``how`` is "sector", "etf" or "alias:<alias>". Industry aliases resolve to their parent
    sector. Text that exactly equals no name/alias but contains aliases of several sectors
    ("food retail", "health care REITs") is ambiguous and resolves to None.
    """
    words = _words(name)
    core = " ".join(w for w in words.split() if w not in _FILLER)
    for s in SECTORS:
        if name.strip().upper() == s.etf:
            return s, "etf"
        if core == _words(s.name):
            return s, "sector"
    for s in SECTORS:
        if core in s.aliases:
            return s, f"alias:{core}"
    hits: dict[str, tuple[int, Sector, str]] = {}
    padded = f" {words} "
    for s in SECTORS:
        for alias in (_words(s.name), *s.aliases):
            if f" {alias} " in padded and len(alias) > hits.get(s.etf, (0,))[0]:
                hits[s.etf] = (len(alias), s, alias)
    if not hits:
        return None, f"No sector matches '{name}'."
    if len(hits) > 1:
        return None, f"'{name}' is ambiguous: " + ", ".join(sorted(h[1].name for h in hits.values())) + "."
    [(_, sector, alias)] = hits.values()
    return sector, f"alias:{alias}"


# --------------------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class DailyBar:
    day: date
    close: float  # raw close
    adj: float  # provider-adjusted close (== close when the table has no Adj Close column)
    volume: float


def parse_prices(text: str) -> list[DailyBar]:
    """GetStockPrices markdown -> bars, oldest first. Unknown tickers/no data -> []."""
    rows = find_table(text or "", {"Date", "Close"})
    bars = []
    for r in rows or []:
        try:
            day = date.fromisoformat(r["Date"])
        except ValueError:
            continue
        close = number(r["Close"])
        adj = number(r.get("Adj Close")) if "Adj Close" in r else close
        if close is None or close <= 0 or adj is None or adj <= 0:
            continue
        vol = number(r.get("Volume"))
        bars.append(DailyBar(day, float(close), float(adj), float(vol or 0)))
    bars.sort(key=lambda b: b.day)
    return bars


_REPORTED = re.compile(r"reported (\d{4}-\d{2}-\d{2})")


_ETF_REPORT = re.compile(r"holdings for (\d{4}-\d{2}-\d{2})")
_CUSIP = re.compile(r"^[0-9A-Z]{9}$")


def parse_etf_holdings(text: str) -> tuple[date | None, list[dict[str, Any]]]:
    """GetEtfHoldings markdown (Equibles Cloud; format verified against the hosted server,
    see tests/fixtures/equibles_live/GetEtfHoldings.md) -> (report period, holdings).

    The "Ticker / CUSIP" column carries a ticker when Equibles knows one, else the CUSIP.
    """
    rows = find_table(text or "", {"Holding", "Ticker / CUSIP", "Value", "Weight", "Category"})
    m = _ETF_REPORT.search(text or "")
    if rows is None or m is None:
        return None, []
    out = []
    for r in rows:
        ident = r["Ticker / CUSIP"].strip().upper()
        is_cusip = bool(_CUSIP.match(ident)) and any(ch.isdigit() for ch in ident)
        value, weight = number(r["Value"]), number(r["Weight"])
        out.append({
            "name": r["Holding"],
            "cusip": ident if is_cusip else None,
            "listed_ticker": None if is_cusip or ident in ("", "-", "—") else ident,
            "value_usd": float(value) if value is not None else None,
            "weight_pct": float(weight) if weight is not None else None,
            "category": r["Category"],
        })
    return date.fromisoformat(m.group(1)), out


def parse_fund_profile(text: str) -> tuple[date | None, list[dict[str, Any]]]:
    """GetFundProfile markdown -> (report period date, holdings largest first)."""
    rows = find_table(text or "", {"Holding", "CUSIP", "Value (USD)", "% Net Assets", "Category"})
    m = _REPORTED.search(text or "")
    if rows is None or m is None:
        return None, []
    out = []
    for r in rows:
        value = number(r["Value (USD)"])
        weight = number(r["% Net Assets"])
        out.append({
            "name": r["Holding"],
            "cusip": None if r["CUSIP"] in ("-", "") else r["CUSIP"],
            "value_usd": float(value) if value is not None else None,
            "weight_pct": float(weight) if weight is not None else None,
            "category": r["Category"],
        })
    return date.fromisoformat(m.group(1)), out


def parse_portfolio(text: str) -> list[tuple[str, str, str]]:
    """GetInstitutionPortfolio markdown -> [(ticker, company, type)] in value order."""
    rows = find_table(text or "", {"Ticker", "Company", "Type"})
    return [(r["Ticker"], r["Company"], r["Type"]) for r in rows or [] if r["Ticker"] not in ("—", "")]


_NAME_TAIL = {"inc", "incorporated", "corp", "corporation", "co", "company", "companies", "ltd",
              "limited", "plc", "the", "class", "cl", "a", "b", "c", "sa", "nv", "ag", "se",
              "lp", "llc", "and", "new", "com", "shs", "ord", "reit"}


def normalize_company(name: str) -> str:
    """Normalise a company name for matching NPORT holding names to 13F issuer names."""
    t = name.lower().replace("'", "").replace(".", "").replace("&", " and ")
    words = re.sub(r"[^a-z0-9]+", " ", t).split()
    while words and words[0] == "the":
        words.pop(0)
    while len(words) > 1 and words[-1] in _NAME_TAIL:
        words.pop()
    return " ".join(words)


# --------------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------------


def visible(bars: list[DailyBar], as_of: datetime) -> list[DailyBar]:
    """Bars whose session had closed by ``as_of`` (a bar dated D is known from 16:00 ET on D)."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    return [b for b in bars if datetime.combine(b.day, MARKET_CLOSE, EASTERN) <= as_of]


def _r(x: float | None, nd: int = 4) -> float | None:
    return None if x is None else round(x, nd)


def _base(bars: list[DailyBar], target: date) -> DailyBar | None:
    base = None
    for b in bars:
        if b.day > target:
            break
        base = b
    return base


def price_stats(bars: list[DailyBar]) -> dict[str, Any] | None:
    """Ratio metrics from visible bars (oldest first). None when there are no bars."""
    if not bars:
        return None
    last = bars[-1]

    def ret(target: date) -> float | None:
        b = _base(bars, target)
        return None if b is None else last.adj / b.adj - 1

    def sma(n: int) -> float | None:
        return mean(b.adj for b in bars[-n:]) if len(bars) >= n else None

    ma50, ma200 = sma(50), sma(200)
    year_start = last.day - timedelta(days=365)
    window = [b for b in bars if b.day > year_start]
    hi, lo = max(b.adj for b in window), min(b.adj for b in window)
    recent = bars[-20:]
    return {
        "last_bar_date": last.day.isoformat(),
        "last_close": last.close,
        "ret_1w": _r(ret(last.day - timedelta(days=7))),
        "ret_1m": _r(ret(last.day - timedelta(days=30))),
        "ret_3m": _r(ret(last.day - timedelta(days=91))),
        "ret_6m": _r(ret(last.day - timedelta(days=182))),
        "ret_ytd": _r(ret(date(last.day.year - 1, 12, 31))),
        "pct_vs_50dma": _r(last.adj / ma50 - 1 if ma50 else None),
        "pct_vs_200dma": _r(last.adj / ma200 - 1 if ma200 else None),
        "above_50dma": None if ma50 is None else last.adj > ma50,
        "above_200dma": None if ma200 is None else last.adj > ma200,
        "pct_from_52w_high": _r(last.adj / hi - 1),
        "pct_from_52w_low": _r(last.adj / lo - 1),
        "at_52w_high": last.adj >= hi,
        "at_52w_low": last.adj <= lo,
        "partial_52w": window[0].day > year_start + timedelta(days=14),
        "avg_volume_20d": round(mean(b.volume for b in recent)),
        "avg_dollar_volume_20d": round(mean(b.adj * b.volume for b in recent)),
        "bars": len(bars),
    }


def _et_date(as_of: datetime) -> date:
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    return as_of.astimezone(EASTERN).date()


_BASIS = ("Equibles GetStockPrices daily bars (Yahoo) visible at as_of. Returns and moving-average/"
          "52-week distances use Adj Close ratios; last_close is the raw close. 1w/1m/3m/6m are "
          "measured from the last close on or before 7/30/91/182 calendar days earlier.")
_SURVIVORSHIP = ("Backtest caveat: constituents come from a past NPORT-P report (point-in-time), but "
                 "prices come from Yahoo via Equibles, where delisted or renamed names may be missing; "
                 "they are excluded from metrics and listed under missing_prices.")
_SCREENER_GAP = ("Key ratios and size (P/E, market cap, margins) would come from the Equibles Cloud "
                 "stock screener, which is not in the open-source server (tool name and format unknown), "
                 "so they are not in this screen. Full fundamentals are fetched for shortlisted companies.")


@dataclass
class _Constituents:
    sector: Sector
    report_date: date
    holdings: list[dict[str, Any]]  # with "ticker" (or None), largest first
    weight_covered_pct: float
    notes: list[str]
    source: str = FUND_TOOL


# --------------------------------------------------------------------------------------
# Provider
# --------------------------------------------------------------------------------------


class EquiblesSectorData:
    """SectorDataProvider backed by the hosted Equibles MCP (see the module docstring).

    ``mcp`` is any McpToolCaller, e.g. ``HttpMcpClient(EQUIBLES_MCP_URL,
    allowed_tools=set(EquiblesSectorData.TOOLS), headers=...)``.
    """

    TOOLS: frozenset[str] = frozenset({PRICES_TOOL, ETF_TOOL, FUND_TOOL, PORTFOLIO_TOOL})

    def __init__(self, mcp: McpToolCaller, *, max_constituents: int = 25, nport_lag_days: int = 60,
                 ticker_map_institution: str = VANGUARD_CIK, ticker_map_max_pages: int = 6,
                 thirteen_f_lag_days: int = 45, cusip_tickers: Mapping[str, str] | None = None,
                 max_parallel: int = 6,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self._mcp = mcp
        self._max = max_constituents
        self._nport_lag = timedelta(days=nport_lag_days)
        self._institution = ticker_map_institution
        self._max_pages = ticker_map_max_pages
        self._13f_lag = timedelta(days=thirteen_f_lag_days)
        self._cusip_tickers = {k.upper(): v for k, v in (cusip_tickers or {}).items()}
        self._sem = asyncio.Semaphore(max_parallel)
        self._now = now
        self._tasks: dict[tuple, asyncio.Task] = {}
        self._name_maps: dict[str, dict[str, Any]] = {}
        self._name_lock = asyncio.Lock()

    # -- plumbing -------------------------------------------------------------------------

    async def _call(self, tool: str, args: dict[str, Any]) -> str:
        async with self._sem:
            return await self._mcp.call_tool(tool, args)

    def _once(self, key: tuple, factory: Callable[[], Awaitable[Any]]) -> asyncio.Task:
        if key not in self._tasks:
            self._tasks[key] = asyncio.ensure_future(factory())
        return self._tasks[key]

    def _backtest(self, as_of: datetime) -> bool:
        return as_of < self._now() - timedelta(days=1)

    async def _bars(self, ticker: str, as_of: datetime) -> tuple[list[DailyBar], str | None]:
        async def fetch():
            end = _et_date(as_of)
            args = {"ticker": ticker, "startDate": (end - timedelta(days=400)).isoformat(),
                    "endDate": end.isoformat(), "maxResults": _PAGE}
            try:
                text = await self._call(PRICES_TOOL, args)
            except Exception as e:  # one bad ticker must not sink the sector
                return [], f"{ticker}: {PRICES_TOOL} failed: {e}"
            bars = visible(parse_prices(text), as_of)
            return bars, None if bars else f"{ticker}: no daily prices on or before as_of ({str(text).strip()[:160]})"
        return await self._once(("bars", ticker, as_of), fetch)

    async def _stats(self, ticker: str, as_of: datetime) -> tuple[dict[str, Any] | None, str | None]:
        bars, note = await self._bars(ticker, as_of)
        return price_stats(bars), note

    def _gap(self, kind: str, subject: str, as_of: datetime, note: str) -> DataSnapshot:
        return DataSnapshot(kind=kind, source="equibles", subject=subject, as_of=as_of, is_gap=True, note=note)

    # -- market overview ------------------------------------------------------------------

    async def market_overview(self, as_of: datetime) -> list[DataSnapshot]:
        notes: list[str] = []
        benchmark = None
        for t in BENCHMARKS:
            stats, note = await self._stats(t, as_of)
            if stats:
                benchmark = {"ticker": t, **stats}
                break
            notes.append(note)
        results = await asyncio.gather(*(self._stats(s.etf, as_of) for s in SECTORS))
        sectors = []
        for s, (stats, note) in zip(SECTORS, results):
            row: dict[str, Any] = {"sector": s.name, "etf": s.etf}
            if stats is None:
                row["unavailable"] = note
            else:
                row.update(stats)
                if benchmark:
                    for p in ("1m", "3m", "6m", "ytd"):
                        a, b = stats[f"ret_{p}"], benchmark[f"ret_{p}"]
                        row[f"vs_benchmark_{p}"] = _r(None if a is None or b is None else a - b)
            sectors.append(row)
        if benchmark is None and all("unavailable" in r for r in sectors):
            return [self._gap("sector_performance", "market", as_of,
                              "Equibles returned no prices for the benchmark or any sector ETF: " + "; ".join(notes))]
        return [DataSnapshot(
            kind="sector_performance", source="equibles", subject="market", as_of=as_of,
            payload={"benchmark": benchmark, "sectors": sectors, "basis": _BASIS,
                     "notes": notes if benchmark is None else []},
        )]

    # -- constituents ---------------------------------------------------------------------

    async def _name_map(self, as_of: datetime, wanted: set[str]) -> tuple[dict[str, list[str]], list[str]]:
        """13F company-name index, paged lazily until ``wanted`` names are covered."""
        report = (_et_date(as_of) - self._13f_lag).isoformat()
        async with self._name_lock:
            state = self._name_maps.setdefault(report, {"index": {}, "pages": 0, "done": False, "notes": []})
            while not state["done"] and not wanted <= set(state["index"]) and state["pages"] < self._max_pages:
                args = {"institutionName": self._institution, "reportDate": report,
                        "maxResults": _PAGE, "offset": state["pages"] * _PAGE}
                try:
                    text = await self._call(PORTFOLIO_TOOL, args)
                except Exception as e:
                    state["notes"].append(f"{PORTFOLIO_TOOL} failed: {e}")
                    break
                rows = parse_portfolio(text)
                state["pages"] += 1
                if not rows and state["pages"] == 1:
                    state["notes"].append(f"{PORTFOLIO_TOOL} returned no table: {str(text).strip()[:160]}")
                for ticker, company, kind in rows:
                    if kind == "Common":
                        tickers = state["index"].setdefault(normalize_company(company), [])
                        if ticker not in tickers:
                            tickers.append(ticker)
                if len(rows) < _PAGE:
                    state["done"] = True
            return state["index"], state["notes"]

    async def _constituents(self, sector: Sector, as_of: datetime) -> _Constituents | str:
        async def build() -> _Constituents | str:
            # Primary: GetEtfHoldings, which carries tickers. Fallback: GetFundProfile (names and
            # CUSIPs only, tickers matched through the 13F name index below).
            source = ETF_TOOL
            try:
                etf_text = await self._call(ETF_TOOL, {"ticker": sector.etf, "maxResults": self._max + 15})
            except Exception as e:
                etf_text = f"{ETF_TOOL} failed: {e}"
            report_date, holdings = parse_etf_holdings(etf_text)
            if report_date is None:
                source = FUND_TOOL
                try:
                    text = await self._call(FUND_TOOL, {"fund": sector.etf, "maxResults": self._max + 15})
                except Exception as e:
                    return f"{FUND_TOOL} failed for {sector.etf}: {e}"
                report_date, holdings = parse_fund_profile(text)
                if report_date is None:
                    return f"No NPORT-P holdings for {sector.etf}: {str(text).strip()[:200]}"
            public_by = report_date + self._nport_lag
            if public_by > _et_date(as_of):
                return (f"The only NPORT-P holdings Equibles serves for {sector.etf} are for period "
                        f"{report_date}, not assumed public until {public_by} (period + "
                        f"{self._nport_lag.days} days), after as_of. GetFundProfile has no report-date "
                        "parameter, so constituents as of this date are unavailable.")
            equities = [h for h in holdings if h["category"].startswith("EC")][: self._max]
            notes = []
            stale = (_et_date(as_of) - report_date).days
            if stale > 200:
                notes.append(f"Holdings report is {stale} days older than as_of; constituents may be stale.")

            unresolved = []
            for h in equities:
                h["ticker"] = self._cusip_tickers.get((h["cusip"] or "").upper())
                h["ticker_source"] = "cusip_override" if h["ticker"] else None
                if not h["ticker"] and h.get("listed_ticker"):
                    h["ticker"], h["ticker_source"] = h["listed_ticker"], "etf_holdings"
                if not h["ticker"]:
                    unresolved.append(normalize_company(h["name"]))
            if unresolved:
                index, map_notes = await self._name_map(as_of, set(unresolved))
                notes += map_notes
                for h in equities:
                    if h["ticker"]:
                        continue
                    tickers = index.get(normalize_company(h["name"]), [])
                    if tickers:
                        h["ticker"], h["ticker_source"] = tickers[0], "13f_name_match"
                        if len(tickers) > 1:
                            h["ticker_candidates"] = tickers
            covered = sum(h["weight_pct"] or 0 for h in equities)
            return _Constituents(sector, report_date, equities, round(covered, 2), notes, source)

        return await self._once(("constituents", sector.etf, as_of), build)

    # -- screen ---------------------------------------------------------------------------

    async def sector_screen(self, sector: str, as_of: datetime) -> list[DataSnapshot]:
        s, how = resolve_sector(sector)
        if s is None:
            return [self._gap("screen", sector, as_of, f"Unknown sector: {how} Known sectors: "
                              + ", ".join(f"{x.name} ({x.etf})" for x in SECTORS) + ".")]
        cons = await self._constituents(s, as_of)
        if isinstance(cons, str):
            return [self._gap("screen", sector, as_of, cons), self._gap("screen", sector, as_of, _SCREENER_GAP)]

        resolved = [h for h in cons.holdings if h["ticker"]]
        stats = await asyncio.gather(*(self._stats(h["ticker"], as_of) for h in resolved))
        snaps: list[DataSnapshot] = []
        missing = []
        seen: set[str] = set()
        for h, (st, note) in zip(resolved, stats):
            if h["ticker"] in seen:
                continue
            seen.add(h["ticker"])
            payload: dict[str, Any] = {
                "ticker": h["ticker"], "company": h["name"], "cusip": h["cusip"],
                "sector": s.name, "etf": s.etf, "etf_weight_pct": h["weight_pct"],
                "etf_position_value_usd": h["value_usd"],
                "holdings_report_date": cons.report_date.isoformat(),
                "ticker_source": h["ticker_source"],
            }
            if "ticker_candidates" in h:
                payload["ticker_candidates"] = h["ticker_candidates"]
            if st is None:
                missing.append(h["ticker"])
                payload["prices_unavailable"] = note
            else:
                payload.update(st)
            snaps.append(DataSnapshot(kind="screen", source="equibles", subject=h["ticker"],
                                      as_of=as_of, payload=payload))

        notes = list(cons.notes)
        if self._backtest(as_of):
            notes.append(_SURVIVORSHIP)
        snaps.append(DataSnapshot(
            kind="screen_coverage", source="equibles", subject=sector, as_of=as_of,
            payload={
                "sector": s.name, "etf": s.etf, "mapped_via": how,
                "parent_sector_note": (f"'{sector}' was mapped to its parent sector {s.name}; the screen "
                                       f"covers the whole sector ETF, not only that industry.")
                if how.startswith("alias:") else None,
                "constituents_source": f"{s.etf} top holdings by value from its NPORT-P report for period "
                                       f"{cons.report_date} (Equibles {cons.source})",
                "holdings_report_date": cons.report_date.isoformat(),
                "constituents_screened": len(snaps),
                "etf_weight_covered_pct": cons.weight_covered_pct,
                "unresolved_tickers": [h["name"] for h in cons.holdings if not h["ticker"]],
                "missing_prices": missing,
                "basis": _BASIS, "notes": notes,
            }))
        snaps.append(self._gap("screen", sector, as_of, _SCREENER_GAP))
        return snaps

    # -- breadth --------------------------------------------------------------------------

    async def sector_breadth(self, sector: str, as_of: datetime) -> DataSnapshot:
        s, how = resolve_sector(sector)
        if s is None:
            return self._gap("sector_breadth", sector, as_of, f"Unknown sector: {how}")
        cons = await self._constituents(s, as_of)
        if isinstance(cons, str):
            return self._gap("sector_breadth", sector, as_of, cons)

        tickers = list(dict.fromkeys(h["ticker"] for h in cons.holdings if h["ticker"]))
        results = await asyncio.gather(*(self._stats(t, as_of) for t in tickers))
        stats = {t: st for t, (st, _) in zip(tickers, results) if st}
        missing = [t for t in tickers if t not in stats]
        etf, etf_note = await self._stats(s.etf, as_of)

        def share(key: str, pred: Callable[[Any], bool]) -> float | None:
            vals = [st[key] for st in stats.values() if st[key] is not None]
            return _r(sum(1 for v in vals if pred(v)) / len(vals)) if vals else None

        def ew(key: str) -> float | None:
            vals = [st[key] for st in stats.values() if st[key] is not None]
            return _r(mean(vals)) if vals else None

        comparison = {}
        for p in ("1m", "3m"):
            e, x = ew(f"ret_{p}"), (etf or {}).get(f"ret_{p}")
            comparison[p] = {"equal_weight": e, "etf": x,
                             "spread": _r(None if e is None or x is None else e - x)}
        notes = list(cons.notes)
        if etf is None:
            notes.append(etf_note)
        if self._backtest(as_of):
            notes.append(_SURVIVORSHIP)
        return DataSnapshot(
            kind="sector_breadth", source="equibles", subject=sector, as_of=as_of,
            payload={
                "sector": s.name, "etf": s.etf, "mapped_via": how,
                "universe": f"top {len(cons.holdings)} equity holdings of {s.etf} by value, NPORT-P "
                            f"period {cons.report_date} ({cons.weight_covered_pct}% of net assets)",
                "constituents_with_prices": len(stats),
                "pct_above_50dma": share("above_50dma", bool),
                "pct_above_200dma": share("above_200dma", bool),
                "pct_positive_1m": share("ret_1m", lambda v: v > 0),
                "new_52w_highs": sum(1 for st in stats.values() if st["at_52w_high"]),
                "new_52w_lows": sum(1 for st in stats.values() if st["at_52w_low"]),
                "equal_weight_vs_etf": comparison,
                "missing_prices": missing,
                "unresolved_tickers": [h["name"] for h in cons.holdings if not h["ticker"]],
                "basis": _BASIS, "notes": notes,
            })
