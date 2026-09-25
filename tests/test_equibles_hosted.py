"""Hosted Equibles MCP provider, against a fake server emitting Equibles' exact table format."""

from datetime import date, datetime, timezone

import pytest

from trading_pipeline.data.equibles import FACT_TOOL, EquiblesFundamentals, parse_fact_table
from trading_pipeline.data.mcp import HttpMcpClient

HEADER = ("| Period Start | Period End | FY | Period | Value | Unit | Form | Filed | Accession |\n"
          "|--------------|------------|---:|--------|------:|------|------|-------|-----------|")
SPLIT_NOTE = ("_Per-share values are split-adjusted to today's share basis using splits effective "
              "strictly after each fact's Filed date._")


def table(concept, basis, rows, *, split=False):
    body = "\n".join(
        f"| {s} | {e} | {fy} | {fp} | {v} | {u} | 10-K | {filed} | {acc} |"
        for s, e, fy, fp, v, u, filed, acc in rows)
    text = f"{concept} for ACME (Acme \\| Co) — {basis}:\n\n{HEADER}\n{body}\n"
    return text + (f"\n{SPLIT_NOTE}\n" if split else "")


class FakeEquibles:
    """Latest-restated vs as-originally-reported answers, like the real tool."""

    def __init__(self):
        self.calls = []
        self.data = {
            "net-income": {
                True: [("2025-01-01", "2025-12-31", 2025, "FY", "$100,000", "USD", "2026-02-20", "A-1")],
                False: [("2025-01-01", "2025-12-31", 2025, "FY", "-$5,000", "USD", "2026-05-01", "A-2")],
            },
            "eps-diluted": {
                True: [("2025-01-01", "2025-12-31", 2025, "FY", "$0.50", "USD/shares", "2026-02-20", "A-1")],
                False: [("2025-01-01", "2025-12-31", 2025, "FY", "$0.50", "USD/shares", "2026-02-20", "A-1")],
            },
        }

    async def call_tool(self, name, arguments):
        assert name == FACT_TOOL
        self.calls.append(arguments)
        alias, original = arguments["concept"], arguments["asOriginallyReported"]
        if alias not in self.data:
            return f"No '{alias}' data has been ingested for ACME."
        basis = "as originally reported" if original else "latest restated"
        return table(alias, basis, self.data[alias][original], split=alias == "eps-diluted")


def at(y, m, d):
    return datetime(y, m, d, 21, 0, tzinfo=timezone.utc)


def provider(fake, now=at(2026, 9, 25), **kw):
    return EquiblesFundamentals(fake, aliases=["net-income", "eps-diluted", "revenue"], now=lambda: now, **kw)


def test_parse_fact_table():
    rows, meta = parse_fact_table(table("net-income", "latest restated", [
        ("2025-01-01", "2025-12-31", 2025, "FY", "-$1,234,567", "USD", "2026-02-20", "A-1"),
        ("2025-01-01", "2025-03-31", 2025, "Q1", "$2.01 (as filed)", "USD/shares", "2025-05-01", "Q-1"),
    ]), "net-income")
    assert meta["company"] == "Acme \\| Co" and not meta["split_adjusted"]
    assert rows[0]["value"] == -1234567 and rows[0]["filed"] == date(2026, 2, 20)
    assert rows[1]["as_filed"] and float(rows[1]["value"]) == 2.01
    assert parse_fact_table("Unknown concept 'x'.", "x")[0] == []


async def test_restatement_only_after_its_filing_date():
    fake = FakeEquibles()
    before = await provider(fake).fundamentals("ACME", at(2026, 3, 1))
    ni = [f for f in before.payload["facts"] if f["concept"] == "net-income"]
    assert [(f["value"], f["revisions"]) for f in ni] == [(100000.0, 1)]

    after = await provider(fake).fundamentals("ACME", at(2026, 5, 2))
    ni = [f for f in after.payload["facts"] if f["concept"] == "net-income"]
    assert [(f["value"], f["revisions"]) for f in ni] == [(-5000.0, 2)]

    none_yet = await provider(fake).fundamentals("ACME", at(2026, 2, 20))  # filed that same day
    assert none_yet.payload["facts"] == []
    # Both modes queried per concept, with period ends capped at the cutoff.
    assert {(c["concept"], c["asOriginallyReported"]) for c in fake.calls} >= {("net-income", True), ("net-income", False)}
    assert all(c["toDate"] <= "2026-05-02" for c in fake.calls)


async def test_split_adjusted_per_share_dropped_in_backtests_only():
    fake = FakeEquibles()
    backtest = await provider(fake).fundamentals("ACME", at(2026, 3, 1))
    assert not any(f["concept"] == "eps-diluted" for f in backtest.payload["facts"])
    assert any("per-share values omitted" in n for n in backtest.payload["notes"])

    live = await provider(fake, now=at(2026, 3, 1)).fundamentals("ACME", at(2026, 3, 1))
    assert any(f["concept"] == "eps-diluted" for f in live.payload["facts"])


async def test_original_only_mode_halves_calls():
    fake = FakeEquibles()
    await provider(fake, include_restatements=False).fundamentals("ACME", at(2026, 5, 2))
    assert len(fake.calls) == 3 and all(c["asOriginallyReported"] for c in fake.calls)


async def test_unknown_ticker_is_gap():
    class Empty:
        async def call_tool(self, name, arguments):
            return "Ticker ZZZZ (not found in the tracked SEC issuer set)"

    snap = await provider(Empty()).fundamentals("ZZZZ", at(2026, 5, 2))
    assert snap.is_gap and "not found" in snap.note


async def test_http_client_enforces_allowlist():
    client = HttpMcpClient("https://example.invalid/mcp", allowed_tools={FACT_TOOL})
    with pytest.raises(PermissionError):
        await client.call_tool("PlaceOrder", {})
