"""FundamentalsProvider backed by a self-hosted Equibles database.

Equibles (https://github.com/daniel3303/Equibles) ingests SEC Company Facts into
Postgres and keeps every filing's value as its own row (restatements are separate
rows keyed by accession number, each with a ``FiledDate``). Its MCP tools only
offer "latest restated" or "as originally reported", neither of which is
point-in-time, so this adapter reads the tables directly.

Point-in-time rule: a fact is visible at ``as_of`` only if it was filed on an
earlier US/Eastern calendar day. ``FiledDate`` carries no time of day and SEC
accepts filings into the evening, so same-day filings are hidden. For each
(concept, unit, period) the latest filing visible at ``as_of`` wins, so a
restatement counts from the day after it was filed and never before.

Table and column names follow Equibles' EF Core model (checked at commit 67072d4).
See docs/equibles-evaluation.md.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from .base import DataSnapshot

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
            "concept": f'{_TAXONOMY.get(latest["taxonomy"], latest["taxonomy"])}:{latest["tag"]}',
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
    return out


class EquiblesFundamentals:
    """Point-in-time SEC fundamentals from a self-hosted Equibles Postgres database."""

    def __init__(self, query: Query, *, concepts: Sequence[str] = DEFAULT_CONCEPTS,
                 lookback_years: int = 3) -> None:
        self._query = query
        self._concepts = list(concepts)
        self._lookback = timedelta(days=365 * lookback_years)

    @classmethod
    def from_dsn(cls, dsn: str, **kwargs: Any) -> EquiblesFundamentals:
        """Connect with psycopg (``pip install 'trading-pipeline[equibles]'``). Read-only use."""
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
