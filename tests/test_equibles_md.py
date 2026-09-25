from decimal import Decimal

from trading_pipeline.data.equibles_md import find_table, number, tables

SAMPLE = """Prices for ACME (Acme \\| Co):

| Date | Open | High | Low | Close | Volume |
|------|-----:|-----:|----:|------:|-------:|
| 2026-06-01 | $10.00 | $11.00 | $9.50 | $10.50 | 1,200,000 |
| 2026-06-02 | $10.50 | $10.80 | $10.10 | $10.20 | 900,000 |

_Split-adjusted._

| Name | Note |
|---|---|
| a \\| b | x |
"""


def test_tables_and_find():
    ts = tables(SAMPLE)
    assert len(ts) == 2 and ts[1][0]["Name"] == "a | b"
    rows = find_table(SAMPLE, {"Date", "Close"})
    assert [r["Close"] for r in rows] == ["$10.50", "$10.20"]
    assert find_table(SAMPLE, {"Nope"}) is None
    assert find_table("| Date | Close |\n|---|---|\n", {"Date"}) == []


def test_number():
    assert number("$1,234") == 1234 and number("-$5.10") == Decimal("-5.10")
    assert number("12.5%") == Decimal("12.5") and number("1.2B") == Decimal("1.2e9")
    assert number("2.01 (as filed)") == Decimal("2.01") and number("—") is None and number("abc") is None
