"""EquiblesFundamentals tests.

The pure point-in-time logic runs everywhere. The SQL runs against a real Postgres
when EQUIBLES_TEST_DSN is set (a scratch database; tables mirroring Equibles'
schema are created and dropped by the test).
"""

import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from trading_pipeline.data.equibles import EquiblesFundamentals, point_in_time, visible_before


def row(value, filed, accession, *, tag="NetIncomeLoss", end=date(2025, 12, 31), fp=0):
    return {"taxonomy": 0, "tag": tag, "label": tag, "unit": "USD", "period_type": 0,
            "period_start": date(end.year, 1, 1), "period_end": end, "fiscal_year": end.year,
            "fiscal_period": fp, "form": "10-K", "filed": filed, "accession": accession,
            "value": Decimal(value)}


def test_visible_before_uses_eastern_date():
    # 03:00 UTC on Mar 2 is still Mar 1 in New York.
    assert visible_before(datetime(2026, 3, 2, 3, 0, tzinfo=timezone.utc)) == date(2026, 3, 1)
    with pytest.raises(ValueError):
        visible_before(datetime(2026, 3, 2))


def test_point_in_time_picks_latest_visible_filing():
    facts = point_in_time([
        row("100", date(2026, 2, 20), "A-1"),
        row("90", date(2026, 5, 1), "A-2"),  # restatement
    ])
    assert len(facts) == 1
    f = facts[0]
    assert f["value"] == 90.0 and f["accession"] == "A-2"
    assert f["revisions"] == 2 and f["first_filed"] == "2026-02-20"
    assert f["concept"] == "us-gaap:NetIncomeLoss" and f["fiscal_period"] == "FY"


# ------------------------------------------------------------------------------------
# SQL against real Postgres
# ------------------------------------------------------------------------------------

DSN = os.environ.get("EQUIBLES_TEST_DSN")
needs_pg = pytest.mark.skipif(not DSN, reason="set EQUIBLES_TEST_DSN to run against Postgres")

# Subset of Equibles' tables, same names/columns/types for everything the adapter reads.
SCHEMA = """
CREATE TABLE "EquityIssuer" ("Id" uuid PRIMARY KEY, "Cik" text, "Name" text, "Sic" text);
CREATE TABLE "EquitySecurity" ("Id" uuid PRIMARY KEY, "EquityIssuerId" uuid NOT NULL);
CREATE TABLE "EquityListing" ("Id" uuid PRIMARY KEY, "EquitySecurityId" uuid NOT NULL,
    "Ticker" text, "MarketCountryCode" text, "ListedOn" date, "DelistedOn" date, "Active" boolean);
CREATE TABLE "FinancialConcept" ("Id" uuid PRIMARY KEY, "Taxonomy" integer NOT NULL,
    "Tag" text, "Label" text);
CREATE TABLE "FinancialFact" ("Id" uuid PRIMARY KEY, "EquityIssuerId" uuid NOT NULL,
    "FinancialConceptId" uuid NOT NULL, "Unit" text, "PeriodType" integer NOT NULL,
    "PeriodStart" date NOT NULL, "PeriodEnd" date NOT NULL, "Value" numeric NOT NULL,
    "FiscalYear" integer NOT NULL, "FiscalPeriod" integer NOT NULL, "Form" text,
    "FiledDate" date NOT NULL, "AccessionNumber" text, "Frame" text,
    "DimensionsKey" text NOT NULL DEFAULT '');
"""


@pytest.fixture
async def pg():
    import psycopg

    schema = f"eqtest_{uuid.uuid4().hex[:8]}"
    conn = await psycopg.AsyncConnection.connect(DSN, autocommit=True)
    await conn.execute(f'CREATE SCHEMA "{schema}"')
    await conn.execute(f'SET search_path TO "{schema}"')
    await conn.execute(SCHEMA)
    try:
        yield conn, schema
    finally:
        await conn.execute(f'DROP SCHEMA "{schema}" CASCADE')
        await conn.close()


async def seed_company(conn, ticker, name, *, listed=None, delisted=None):
    issuer, security = uuid.uuid4(), uuid.uuid4()
    await conn.execute('INSERT INTO "EquityIssuer" VALUES (%s, %s, %s, %s)', (issuer, f"CIK-{name}", name, "2834"))
    await conn.execute('INSERT INTO "EquitySecurity" VALUES (%s, %s)', (security, issuer))
    await conn.execute('INSERT INTO "EquityListing" VALUES (%s, %s, %s, %s, %s, %s, %s)',
                       (uuid.uuid4(), security, ticker, "US", listed, delisted, delisted is None))
    return issuer


async def seed_fact(conn, issuer, concept, value, filed, accession, *, end=date(2025, 12, 31), dims=""):
    await conn.execute(
        'INSERT INTO "FinancialFact" ("Id","EquityIssuerId","FinancialConceptId","Unit","PeriodType",'
        '"PeriodStart","PeriodEnd","Value","FiscalYear","FiscalPeriod","Form","FiledDate",'
        '"AccessionNumber","DimensionsKey") VALUES (%s,%s,%s,%s,0,%s,%s,%s,%s,0,%s,%s,%s,%s)',
        (uuid.uuid4(), issuer, concept, "USD", date(end.year, 1, 1), end, Decimal(value), end.year,
         "10-K", filed, accession, dims))


def adapter(schema):
    import psycopg
    from psycopg.rows import dict_row

    async def query(sql, params):
        async with await psycopg.AsyncConnection.connect(DSN, row_factory=dict_row) as conn:
            await conn.execute(f'SET search_path TO "{schema}"')
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                return await cur.fetchall()

    return EquiblesFundamentals(query)


def at(y, m, d):  # 17:00 New York time
    return datetime(y, m, d, 21, 0, tzinfo=timezone.utc)


@needs_pg
async def test_sql_point_in_time_restatement(pg):
    conn, schema = pg
    issuer = await seed_company(conn, "ACME", "Acme")
    ni = uuid.uuid4()
    await conn.execute('INSERT INTO "FinancialConcept" VALUES (%s, 0, %s, %s)', (ni, "NetIncomeLoss", "Net income"))
    await seed_fact(conn, issuer, ni, "100", date(2026, 2, 20), "A-1")
    await seed_fact(conn, issuer, ni, "90", date(2026, 5, 1), "A-2")  # restatement
    await seed_fact(conn, issuer, ni, "55", date(2026, 2, 20), "A-1", dims="segmenthash")  # segment row

    fx = adapter(schema)
    assert (await fx.fundamentals("ACME", at(2026, 2, 19))).payload["facts"] == []
    # Filed on the 20th: hidden that same day, visible the next.
    assert (await fx.fundamentals("ACME", at(2026, 2, 20))).payload["facts"] == []
    before = (await fx.fundamentals("ACME", at(2026, 2, 21))).payload["facts"]
    assert [(f["value"], f["revisions"]) for f in before] == [(100.0, 1)]
    after = (await fx.fundamentals("ACME", at(2026, 5, 2))).payload
    assert [(f["value"], f["revisions"]) for f in after["facts"]] == [(90.0, 2)]
    assert after["issuer"]["name"] == "Acme"


@needs_pg
async def test_sql_ticker_reuse_and_unknown(pg):
    conn, schema = pg
    await seed_company(conn, "RE", "OldCo", listed=date(2000, 1, 1), delisted=date(2020, 6, 30))
    await seed_company(conn, "RE", "NewCo", listed=date(2022, 1, 1))
    fx = adapter(schema)

    old = await fx.fundamentals("RE", at(2019, 1, 2))
    new = await fx.fundamentals("RE", at(2024, 1, 2))
    assert old.payload["issuer"]["name"] == "OldCo" and new.payload["issuer"]["name"] == "NewCo"
    assert (await fx.fundamentals("RE", at(2021, 1, 4))).is_gap  # between listings
    assert (await fx.fundamentals("NOPE", at(2024, 1, 2))).is_gap
