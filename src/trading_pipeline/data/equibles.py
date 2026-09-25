"""Point-in-time SEC fundamentals from Equibles.

Equibles (https://equibles.com, https://github.com/daniel3303/Equibles) ingests SEC
Company Facts and keeps every filing's value with its filing date and accession
number. Two providers:

* ``EquiblesFundamentals`` (default): the hosted MCP server
  (``https://mcp.equibles.com/mcp``). No database to run. ``GetFinancialFact`` returns
  each value with its Filed date in either "latest restated" or "as originally
  reported" mode; fetching both and keeping only rows filed before ``as_of``
  reconstructs what was known then. (Only a middle restatement of a period restated
  twice can be missed.)
* ``EquiblesPostgresFundamentals``: reads a self-hosted Equibles Postgres directly
  and sees every filing, for exact point-in-time.

Point-in-time rule: a fact is visible at ``as_of`` only if it was filed on an
earlier US/Eastern calendar day. ``FiledDate`` carries no time of day and SEC
accepts filings into the evening, so same-day filings are hidden. For each
(concept, unit, period) the latest filing visible at ``as_of`` wins, so a
restatement counts from the day after it was filed and never before.

Table and column names follow Equibles' EF Core model (checked at commit 67072d4).
See docs/equibles-evaluation.md.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable, Sequence
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from .base import DataSnapshot
from .mcp import McpToolCaller

Query = Callable[[str, dict[str, Any]], Awaitable[list[dict[str, Any]]]]

EASTERN = ZoneInfo("America/New_York")

# Equibles enum ordinals (Equibles.Sec.FinancialFacts.Data.Enums).
_TAXONOMY = {0: "us-gaap", 1: "dei", 2: "ifrs-full", 3: "srt", 4: "invest", 5: "custom"}
_FISCAL_PERIOD = {0: "FY", 1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
_PERIOD_TYPE = {0: "duration", 1: "instant"}

# A compact default set: enough for worthiness checks without flooding prompts.
# Several revenue tags are listed because filers switch tags over time.
DEFAULT_CONCEPTS: tuple[str, ...] = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "GrossProfit",
    "OperatingIncomeLoss",
    "NetIncomeLoss",
    "EarningsPerShareDiluted",
    "ResearchAndDevelopmentExpense",
    "NetCashProvidedByUsedInOperatingActivities",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "CashAndCashEquivalentsAtCarryingValue",
    "Assets",
    "Liabilities",
    "LongTermDebt",
    "StockholdersEquity",
    "EntityCommonStockSharesOutstanding",
)

_ISSUER_SQL = """
SELECT DISTINCT i."Id" AS issuer_id, i."Cik" AS cik, i."Name" AS name, i."Sic" AS sic
FROM "EquityListing" l
JOIN "EquitySecurity" s ON s."Id" = l."EquitySecurityId"
JOIN "EquityIssuer" i ON i."Id" = s."EquityIssuerId"
WHERE l."Ticker" = %(ticker)s
  AND l."MarketCountryCode" = 'US'
  AND (l."ListedOn" IS NULL OR l."ListedOn" <= %(day)s)
  AND (l."DelistedOn" IS NULL OR l."DelistedOn" > %(day)s)
"""

_FACTS_SQL = """
SELECT c."Taxonomy" AS taxonomy, c."Tag" AS tag, c."Label" AS label,
       f."Unit" AS unit, f."PeriodType" AS period_type,
       f."PeriodStart" AS period_start, f."PeriodEnd" AS period_end,
       f."FiscalYear" AS fiscal_year, f."FiscalPeriod" AS fiscal_period,
       f."Form" AS form, f."FiledDate" AS filed, f."AccessionNumber" AS accession,
       f."Value" AS value
FROM "FinancialFact" f
JOIN "FinancialConcept" c ON c."Id" = f."FinancialConceptId"
WHERE f."EquityIssuerId" = %(issuer_id)s
  AND f."DimensionsKey" = ''
  AND f."FiledDate" < %(visible_before)s
  AND f."PeriodEnd" >= %(period_floor)s
  AND c."Tag" = ANY(%(tags)s)
"""


def visible_before(as_of: datetime) -> date:
    """First US/Eastern date whose filings are NOT yet visible at ``as_of``."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    return as_of.astimezone(EASTERN).date()


def point_in_time(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse filing rows to one value per (concept, unit, period): the latest filed.

    ``revisions`` counts how many visible filings reported that period; > 1 means
    the value was restated or re-reported before ``as_of``.
    """
    groups: dict[tuple, list[dict[str, Any]]] = {}
    for r in rows:
        key = (r["taxonomy"], r["tag"], r["unit"], r["period_start"], r["period_end"])
        groups.setdefault(key, []).append(r)

    out = []
    for group in groups.values():
        latest = max(group, key=lambda r: (r["filed"], r["accession"]))
        first = min(group, key=lambda r: (r["filed"], r["accession"]))
        value = latest["value"]
        out.append({
            "concept": (f'{_TAXONOMY.get(latest["taxonomy"], latest["taxonomy"])}:{latest["tag"]}'
                        if latest["taxonomy"] is not None else latest["tag"]),
            "label": latest["label"],
            "unit": latest["unit"],
            "period_type": _PERIOD_TYPE.get(latest["period_type"], latest["period_type"]),
            "period_start": latest["period_start"].isoformat(),
            "period_end": latest["period_end"].isoformat(),
            "fiscal_year": latest["fiscal_year"],
            "fiscal_period": _FISCAL_PERIOD.get(latest["fiscal_period"], latest["fiscal_period"]),
            "value": float(value) if isinstance(value, Decimal) else value,
            "form": latest["form"],
            "filed": latest["filed"].isoformat(),
            "accession": latest["accession"],
            "revisions": len({r["accession"] for r in group}),
            "first_filed": first["filed"].isoformat(),
        })
    out.sort(key=lambda f: (f["concept"], f["period_end"], f["period_start"]))
    return [{k: v for k, v in f.items() if v is not None} for f in out]


class EquiblesPostgresFundamentals:
    """Point-in-time SEC fundamentals from a self-hosted Equibles Postgres database."""

    def __init__(self, query: Query, *, concepts: Sequence[str] = DEFAULT_CONCEPTS,
                 lookback_years: int = 3) -> None:
        self._query = query
        self._concepts = list(concepts)
        self._lookback = timedelta(days=365 * lookback_years)

    @classmethod
    def from_dsn(cls, dsn: str, **kwargs: Any) -> EquiblesPostgresFundamentals:
        """Connect with psycopg (``pip install 'trading-pipeline[equibles-postgres]'``). Read-only use."""
        import psycopg
        from psycopg.rows import dict_row

        async def query(sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
            async with await psycopg.AsyncConnection.connect(dsn, row_factory=dict_row) as conn:
                await conn.set_read_only(True)
                async with conn.cursor() as cur:
                    await cur.execute(sql, params)
                    return await cur.fetchall()

        return cls(query, **kwargs)

    def _gap(self, ticker: str, as_of: datetime, note: str) -> DataSnapshot:
        return DataSnapshot(kind="fundamentals", source="equibles", subject=ticker, as_of=as_of,
                            is_gap=True, note=note)

    async def fundamentals(self, ticker: str, as_of: datetime) -> DataSnapshot:
        cutoff = visible_before(as_of)
        issuers = await self._query(_ISSUER_SQL, {"ticker": ticker, "day": cutoff})
        if not issuers:
            return self._gap(ticker, as_of, f"Equibles has no US listing for {ticker} on {cutoff}.")
        if len({i["issuer_id"] for i in issuers}) > 1:
            names = ", ".join(sorted(f'{i["name"]} (CIK {i["cik"]})' for i in issuers))
            return self._gap(ticker, as_of, f"Ticker {ticker} is ambiguous on {cutoff}: {names}.")

        issuer = issuers[0]
        rows = await self._query(_FACTS_SQL, {
            "issuer_id": issuer["issuer_id"],
            "visible_before": cutoff,
            "period_floor": cutoff - self._lookback,
            "tags": self._concepts,
        })
        return DataSnapshot(
            kind="fundamentals", source="equibles", subject=ticker, as_of=as_of,
            payload={
                "issuer": {"cik": issuer["cik"], "name": issuer["name"], "sic": issuer["sic"]},
                "basis": "SEC XBRL, latest value filed before this date (point-in-time); "
                         "revisions > 1 means restated or re-reported before this date",
                "facts": point_in_time(rows),
            },
        )


# --------------------------------------------------------------------------------------
# Hosted MCP
# --------------------------------------------------------------------------------------

EQUIBLES_MCP_URL = "https://mcp.equibles.com/mcp"
FACT_TOOL = "GetFinancialFact"

# Equibles concept aliases (FinancialStatementConcepts in the Equibles source).
DEFAULT_ALIASES: tuple[str, ...] = (
    "revenue",
    "gross-profit",
    "operating-income",
    "net-income",
    "eps-diluted",
    "research-and-development",
    "operating-cash-flow",
    "capital-expenditures",
    "cash",
    "total-assets",
    "total-liabilities",
    "long-term-debt",
    "stockholders-equity",
    "weighted-average-shares-diluted",
)

# Emitted by Equibles when per-share values were restated to today's share basis,
# which in a backtest would reveal splits that happen after as_of.
_SPLIT_NOTE = "Per-share values are split-adjusted to today's share basis"
_HEADER = "| Period Start | Period End | FY | Period | Value | Unit | Form | Filed | Accession |"
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_TITLE = re.compile(r"^\S+ for \S+ \((?P<name>.*)\) — ", re.MULTILINE)


def _cells(line: str) -> list[str]:
    inner = line.strip()[1:-1]
    return [c.strip().replace("\\|", "|").replace("\\\\", "\\") for c in _CELL_SPLIT.split(inner)]


def _number(text: str) -> Decimal:
    t = text.replace("(as filed)", "").strip()
    neg = t.startswith("-")
    t = t.lstrip("-").lstrip("$").replace(",", "")
    value = Decimal(t)
    return -value if neg else value


def parse_fact_table(text: str, alias: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse a GetFinancialFact markdown answer into filing rows plus metadata."""
    meta: dict[str, Any] = {"split_adjusted": _SPLIT_NOTE in text, "company": None}
    if m := _TITLE.search(text):
        meta["company"] = m.group("name")
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == _HEADER) + 2
    except StopIteration:
        meta["message"] = text.strip()[:300]
        return [], meta

    rows = []
    for line in lines[start:]:
        if not line.strip().startswith("|"):
            break
        c = _cells(line)
        if len(c) != 9:
            continue
        rows.append({
            "taxonomy": None, "tag": alias, "label": alias, "unit": c[5], "period_type": None,
            "period_start": date.fromisoformat(c[0]), "period_end": date.fromisoformat(c[1]),
            "fiscal_year": int(c[2]), "fiscal_period": c[3], "form": c[6],
            "filed": date.fromisoformat(c[7]), "accession": c[8], "value": _number(c[4]),
            "as_filed": "(as filed)" in c[4],
        })
    return rows, meta


def _per_share(unit: str) -> bool:
    parts = unit.split("/")
    return len(parts) == 2 and parts[1].strip().lower() in ("shares", "share")


class EquiblesFundamentals:
    """Point-in-time SEC fundamentals from the hosted Equibles MCP server.

    ``mcp`` is any McpToolCaller, e.g. ``HttpMcpClient(EQUIBLES_MCP_URL,
    allowed_tools={FACT_TOOL}, headers={"Authorization": f"Bearer {key}"})``.

    Budget: one call per concept, two with ``include_restatements`` (the default).
    With the 14 default concepts that is 28 calls per ticker, so the Free plan
    (100 calls/day) only suits development; real runs need Plus (10,000/day).
    """

    def __init__(self, mcp: McpToolCaller, *, aliases: Sequence[str] = DEFAULT_ALIASES,
                 lookback_years: int = 3, include_restatements: bool = True, max_parallel: int = 4,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self._mcp = mcp
        self._aliases = list(aliases)
        self._lookback = timedelta(days=365 * lookback_years)
        self._include_restatements = include_restatements
        self._sem = asyncio.Semaphore(max_parallel)
        self._now = now

    async def _fetch(self, ticker: str, alias: str, original: bool, since: date, until: date):
        args = {"ticker": ticker, "concept": alias, "fromDate": since.isoformat(),
                "toDate": until.isoformat(), "maxResults": 40, "asOriginallyReported": original}
        async with self._sem:
            text = await self._mcp.call_tool(FACT_TOOL, args)
        return parse_fact_table(text, alias)

    async def fundamentals(self, ticker: str, as_of: datetime) -> DataSnapshot:
        cutoff = visible_before(as_of)
        since = cutoff - self._lookback
        # Per-share values come back adjusted for splits up to today; in a backtest that
        # leaks splits after as_of, so they are dropped unless the run is live.
        backtest = as_of < self._now() - timedelta(days=1)
        modes = [True, False] if self._include_restatements else [True]

        jobs = [(alias, mode) for alias in self._aliases for mode in modes]
        results = await asyncio.gather(*(self._fetch(ticker, a, m, since, cutoff) for a, m in jobs))

        rows: list[dict[str, Any]] = []
        notes: list[str] = []
        company = None
        for (alias, _), (parsed, meta) in zip(jobs, results):
            company = company or meta["company"]
            if "message" in meta and meta["message"] not in notes:
                notes.append(meta["message"])
            for r in parsed:
                if r["filed"] >= cutoff:
                    continue
                if backtest and meta["split_adjusted"] and _per_share(r["unit"]) and not r["as_filed"]:
                    note = f"{alias}: per-share values omitted (split-adjusted to today's basis)."
                    if note not in notes:
                        notes.append(note)
                    continue
                rows.append(r)

        if not rows and company is None:
            return DataSnapshot(kind="fundamentals", source="equibles", subject=ticker, as_of=as_of,
                                is_gap=True, note="; ".join(notes) or f"No Equibles data for {ticker}.")
        return DataSnapshot(
            kind="fundamentals", source="equibles", subject=ticker, as_of=as_of,
            payload={
                "company": company,
                "basis": "SEC XBRL via Equibles, latest value filed before this date (point-in-time); "
                         "revisions > 1 means restated or re-reported before this date",
                "facts": point_in_time(rows),
                "notes": notes,
            },
        )
