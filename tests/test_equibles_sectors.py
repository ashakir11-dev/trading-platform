"""Equibles sector provider against a fake MCP that emits Equibles' exact markdown formats."""

from datetime import date, datetime, timedelta, timezone

import pytest

from trading_pipeline.data.base import RawDataBundle
from trading_pipeline.data.equibles_sectors import (
    ETF_TOOL,
    FUND_TOOL,
    PORTFOLIO_TOOL,
    PRICES_TOOL,
    SECTORS,
    EquiblesSectorData,
    normalize_company,
    parse_fund_profile,
    parse_portfolio,
    parse_prices,
    price_stats,
    resolve_sector,
    visible,
)

AS_OF = datetime(2026, 6, 30, 21, 0, tzinfo=timezone.utc)  # 17:00 ET, after the 06-30 close
FUTURE = date(2026, 7, 1)  # every series crashes 50% from here: any leak shows up
DAYS = [date(2025, 1, 1) + timedelta(days=i) for i in range(730)]
DAYS = [d for d in DAYS if d.weekday() < 5]


def series(kind):
    """(day, close, adj) rows. 'split' has a 2:1 split on 2026-04-01 (raw halves, adj continuous)."""
    out = []
    for i, d in enumerate(DAYS):
        adj = {"up": 100 * 1.001 ** i, "down": 100 * 0.999 ** i, "flat": 100.0,
               "split": 50 * 1.001 ** i}[kind]
        close = adj * 2 if kind == "split" and d < date(2026, 4, 1) else adj
        if d >= FUTURE:
            close, adj = close / 2, adj / 2
        out.append((d, close, adj))
    return out


def price(v):  # McpFormat.Price for values >= $1: F2, invariant culture
    return f"{v:.2f}"


def prices_text(ticker, rows):
    """StockPriceTools.GetStockPrices: title, blank, header (+Adj Close iff any row differs), rows, footnote."""
    adjusted = any(price(c) != price(a) for _, c, a in rows)
    if adjusted:
        head = "| Date | Open | High | Low | Close | Adj Close | Volume |\n|------|------|------|-----|-------|-----------|--------|"
        body = [f"| {d} | {price(c)} | {price(c)} | {price(c)} | {price(c)} | {price(a)} | 1,000,000 |" for d, c, a in rows]
        foot = "_Adj Close is the provider-adjusted close. Captured splits and cash dividends trigger a full-history refresh, but stored rows do not certify which split basis the provider returned. Do not infer a consistent total-return window from reconciliation status alone._"
    else:
        head = "| Date | Open | High | Low | Close | Volume |\n|------|------|------|-----|-------|--------|"
        body = [f"| {d} | {price(c)} | {price(c)} | {price(c)} | {price(c)} | 1,000,000 |" for d, c, _ in rows]
        foot = "_Adj Close equals Close on every row shown. Captured splits and cash dividends trigger a full-history refresh, but equality does not prove that a split-spanning window uses one basis._"
    return f"Daily prices for {ticker}:\n\n{head}\n" + "\n".join(body) + f"\n\n{foot}\n"


# FundDirectoryTools.GetFundProfile: header line built from series/registrant/report date, then the
# holdings table ordered by Value (USD) desc; names escaped with MarkdownTable.EscapeCell.
XLV_PROFILE = """Health Care Select Sector SPDR Fund (XLV) — registrant Select Sector SPDR Trust, reported 2026-03-31, net assets $38,123,456,789.00, total assets $38,200,000,000.00, 62 holdings reported, 61 holdings, showing stored rows 1-6 by value:

| Holding | CUSIP | Balance | Units | Value (USD) | % Net Assets | Category | Country |
|---------|-------|---------|-------|-------------|--------------|----------|---------|
| Eli Lilly & Co | 532457108 | 5,000,000 | NS (shares) | $4,200,000,000.00 | 11.02% | EC (equity-common) | US |
| UnitedHealth Group Inc | 91324P102 | 6,000,000 | NS (shares) | $3,000,000,000.00 | 7.87% | EC (equity-common) | US |
| Johnson & Johnson | 478160104 | 15,000,000 | NS (shares) | $2,500,000,000.00 | 6.56% | EC (equity-common) | US |
| AbbVie Inc | 00287Y109 | 10,000,000 | NS (shares) | $2,000,000,000.00 | 5.25% | EC (equity-common) | US |
| Obscure Pharma Holdings Corp | 999999999 | 1,000,000 | NS (shares) | $100,000,000.00 | 0.26% | EC (equity-common) | US |
| State Street Institutional US Government Money Market Fund | 857492706 | 50,000,000.50 | NS (shares) | $50,000,000.00 | 0.13% | STIV (short-term investment vehicle) | US |
"""

# InstitutionalHoldingsTools.RenderInstitutionPortfolio: title, subtitle, blank, header, numbered rows
# (Company is h.Issuer.Name, unescaped), then the Type and Coverage footnotes.
PORTFOLIO = """Portfolio of Vanguard Group Inc (CIK: 102909) as of 2026-03-31:
Showing holding rows 1-6 of 6, largest value first (6 distinct tracked stocks — a stock held as shares and as options appears as separate rows). Tracked 13F value: $9,000.0M

| # | Ticker | Company | Type | Shares | Value ($M) | % of Portfolio |
|---|--------|---------|------|--------|-----------|----------------|
| 1 | LLY | Eli Lilly And Co | Common | 80,000,000 | 4,000.0 | 44.4% |
| 2 | UNH | Unitedhealth Group Inc. | Common | 90,000,000 | 2,000.0 | 22.2% |
| 3 | JNJ | Johnson & Johnson | Common | 250,000,000 | 1,500.0 | 16.7% |
| 4 | HD | Home Depot, Inc. | Common | 100,000,000 | 1,000.0 | 11.1% |
| 5 | OBSC | Obscure Pharma Holdings Corp | Put | 1,000,000 | 400.0 | 4.4% |
| 6 | XYZ | Other Co | Common | 1,000 | 100.0 | 1.1% |

_Type: Common = shares held outright; Principal = a principal-denominated security. Put/Call = an option position, reported at the notional value of the underlying shares, not the premium paid. A PUT IS A BEARISH POSITION — the filer profits if the stock falls. Option notional is included in the portfolio total and the percentages above, exactly as the filer reported it._
_Coverage: totals span the U.S.-listed common stock (and its put/call positions) this platform tracks. A 13F can also report security types outside that coverage — preferred shares, bonds, warrants, untracked share classes — so the filing's own declared total can exceed the figure above._
"""

KINDS = {"SPY": "flat", "LLY": "up", "UNH": "down", "JNJ": "up", "XLV": "flat", "XLK": "up",
         "SPLT": "split"}


class FakeEquibles:
    def __init__(self, kinds=KINDS):
        self.kinds = kinds
        self.calls = []

    async def call_tool(self, name, args):
        assert name in EquiblesSectorData.TOOLS  # the adapter never calls outside its allowlist
        self.calls.append((name, args))
        if name == PRICES_TOOL:
            t = args["ticker"]
            if t not in self.kinds:  # StockPriceTools: records.Count == 0
                return f"No price data found for {t} in the specified date range."
            start = date.fromisoformat(args["startDate"])
            # Deliberately ignores endDate: the adapter must filter parsed rows itself.
            rows = [r for r in series(self.kinds[t]) if r[0] >= start][-args["maxResults"]:]
            return prices_text(t, rows)
        if name == ETF_TOOL:
            # This fake's ETFs aren't in the Cloud ETF tool, exercising the GetFundProfile fallback;
            # test_etf_holdings_primary covers the primary path.
            return f"No ETF holdings found for '{args['ticker']}'."
        if name == FUND_TOOL:
            if args["fund"] == "XLV":
                return XLV_PROFILE
            return (f"No registered fund found for '{args['fund']}' in the tracked Form NPORT-P directory. "
                    "Use SearchFunds to find a profile id.")
        if name == PORTFOLIO_TOOL:
            return PORTFOLIO if args["offset"] == 0 else "No results at offset 500 - only 6 holding rows on file."
        raise AssertionError(name)

    def count(self, tool):
        return sum(1 for n, _ in self.calls if n == tool)


def provider(fake, **kw):
    kw.setdefault("now", lambda: AS_OF)  # a live run unless a test says otherwise
    return EquiblesSectorData(fake, cusip_tickers={"00287y109": "ABBV"}, **kw)


def expected_ret(kind, back_days):
    rows = [r for r in series(kind) if r[0] <= AS_OF.date()]
    base = [r for r in rows if r[0] <= rows[-1][0] - timedelta(days=back_days)][-1]
    return round(rows[-1][2] / base[2] - 1, 4)


# -- sector map ------------------------------------------------------------------------


def test_sector_map():
    assert len(SECTORS) == 11 and {s.etf for s in SECTORS} == {
        "XLK", "XLF", "XLV", "XLE", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"}
    for text, etf in [("Biotech", "XLV"), ("Pharma", "XLV"), ("Healthcare", "XLV"), ("Health Care sector", "XLV"),
                      ("Semiconductors", "XLK"), ("XLRE", "XLRE"), ("US Regional Banks", "XLF"),
                      ("Oil & Gas", "XLE"), ("Communication Services", "XLC"), ("REITs", "XLRE")]:
        s, how = resolve_sector(text)
        assert s is not None and s.etf == etf, text
    assert resolve_sector("Biotech")[1] == "alias:biotech"
    assert resolve_sector("Quantum widgets")[0] is None
    s, why = resolve_sector("banks and software")
    assert s is None and "ambiguous" in why


# -- parsing ---------------------------------------------------------------------------


def test_parsers():
    bars = parse_prices(prices_text("SPLT", series("split")[300:305]))
    assert len(bars) == 5 and bars[0].close != bars[0].adj
    plain = parse_prices(prices_text("SPY", series("flat")[:3]))
    assert [b.adj for b in plain] == [100.0] * 3 and plain[0].volume == 1_000_000
    assert parse_prices("No price data found for ZZZ in the specified date range.") == []

    report, holdings = parse_fund_profile(XLV_PROFILE)
    assert report == date(2026, 3, 31) and len(holdings) == 6
    assert holdings[0] == {"name": "Eli Lilly & Co", "cusip": "532457108", "value_usd": 4.2e9,
                           "weight_pct": 11.02, "category": "EC (equity-common)"}
    assert parse_fund_profile("No registered fund found for 'X'.") == (None, [])

    rows = parse_portfolio(PORTFOLIO)
    assert rows[0] == ("LLY", "Eli Lilly And Co", "Common") and rows[4][2] == "Put"

    assert normalize_company("Home Depot Inc/The") == normalize_company("Home Depot, Inc.") == "home depot"
    assert normalize_company("Alphabet Inc Class A") == "alphabet"
    assert normalize_company("Eli Lilly & Co") == normalize_company("Eli Lilly And Co")
    assert normalize_company("JPMorgan Chase & Co") == normalize_company("JPMorgan Chase & Co.")


# -- point-in-time ---------------------------------------------------------------------


def test_bars_visible_only_after_their_close():
    bars = parse_prices(prices_text("SPY", series("up")))
    at_close = visible(bars, datetime(2026, 6, 30, 20, 0, tzinfo=timezone.utc))  # 16:00 ET
    before_close = visible(bars, datetime(2026, 6, 30, 19, 59, tzinfo=timezone.utc))
    assert at_close[-1].day == date(2026, 6, 30) and before_close[-1].day == date(2026, 6, 29)
    with pytest.raises(ValueError):
        visible(bars, datetime(2026, 6, 30))


def test_split_inside_window_does_not_distort_ratios():
    bars = visible(parse_prices(prices_text("SPLT", series("split"))), AS_OF)
    st = price_stats(bars)
    assert st["ret_3m"] == expected_ret("split", 91) > 0  # raw closes would show about -50%
    assert st["above_200dma"] is True and st["at_52w_high"] is True
    assert st["last_close"] == pytest.approx(bars[-1].close)


async def test_market_overview_is_point_in_time():
    fake = FakeEquibles()
    [snap] = await provider(fake).market_overview(AS_OF)
    assert snap.kind == "sector_performance" and snap.subject == "market" and not snap.is_gap
    p = snap.payload
    assert p["benchmark"]["ticker"] == "SPY" and p["benchmark"]["last_bar_date"] == "2026-06-30"
    xlk = next(s for s in p["sectors"] if s["etf"] == "XLK")
    # The fake returned the post-as_of crash; none of it may show.
    assert xlk["last_bar_date"] == "2026-06-30"
    assert xlk["ret_1m"] == expected_ret("up", 30) > 0 and xlk["ret_ytd"] > 0
    assert xlk["vs_benchmark_1m"] == xlk["ret_1m"]  # benchmark is flat
    assert xlk["above_50dma"] and xlk["above_200dma"] and xlk["pct_from_52w_high"] == 0
    xlf = next(s for s in p["sectors"] if s["etf"] == "XLF")
    assert "no daily prices" in xlf["unavailable"]
    assert all(a["endDate"] <= "2026-06-30" for n, a in fake.calls if n == PRICES_TOOL)
    assert fake.count(PRICES_TOOL) == 12
    RawDataBundle(as_of=AS_OF).extend([snap])  # passes the look-ahead guard


async def test_market_overview_falls_back_and_gaps():
    fake = FakeEquibles(kinds={"IVV": "up"})
    [snap] = await provider(fake).market_overview(AS_OF)
    assert snap.payload["benchmark"]["ticker"] == "IVV"
    [gap] = await provider(FakeEquibles(kinds={})).market_overview(AS_OF)
    assert gap.is_gap and gap.subject == "market"


# -- screen and breadth ----------------------------------------------------------------


async def test_sector_screen():
    fake = FakeEquibles()
    snaps = await provider(fake).sector_screen("Biotech", AS_OF)
    screens = {s.subject: s for s in snaps if s.kind == "screen" and not s.is_gap}
    assert set(screens) == {"LLY", "UNH", "JNJ", "ABBV"}
    lly = screens["LLY"].payload
    assert lly["etf"] == "XLV" and lly["etf_weight_pct"] == 11.02 and lly["ticker_source"] == "13f_name_match"
    assert lly["holdings_report_date"] == "2026-03-31" and lly["last_bar_date"] == "2026-06-30"
    assert lly["ret_1m"] == expected_ret("up", 30) and lly["pct_from_52w_high"] == 0
    assert lly["avg_volume_20d"] == 1_000_000 and "income" not in str(lly).lower()
    assert screens["UNH"].payload["ret_3m"] < 0 and screens["UNH"].payload["above_50dma"] is False
    abbv = screens["ABBV"].payload
    assert abbv["ticker_source"] == "cusip_override" and "no daily prices" in abbv["prices_unavailable"]

    [cov] = [s for s in snaps if s.kind == "screen_coverage"]
    assert cov.subject == "Biotech" and cov.payload["etf"] == "XLV"
    assert "parent sector Health Care" in cov.payload["parent_sector_note"]
    # The put row must not name a holding; the money-market sweep is not a constituent.
    assert cov.payload["unresolved_tickers"] == ["Obscure Pharma Holdings Corp"]
    assert cov.payload["missing_prices"] == ["ABBV"]
    assert not any("Backtest caveat" in n for n in cov.payload["notes"])  # live run
    [gap] = [s for s in snaps if s.is_gap]
    assert "Cloud stock screener" in gap.note

    assert fake.count(FUND_TOOL) == 1 and fake.count(PORTFOLIO_TOOL) == 1
    portfolio_args = next(a for n, a in fake.calls if n == PORTFOLIO_TOOL)
    assert portfolio_args["reportDate"] <= "2026-05-16"  # 13F lag before as_of

    # The company deep dive keeps sector + own ticker + market; screens must key by ticker.
    bundle = RawDataBundle(as_of=AS_OF)
    bundle.extend(snaps)
    kept = bundle.filter(subjects={"Biotech", "LLY"})
    assert {s.subject for s in kept.snapshots} == {"Biotech", "LLY"}


async def test_sector_breadth_reuses_screen_calls():
    fake = FakeEquibles()
    p = provider(fake)
    await p.sector_screen("Health Care", AS_OF)
    calls = len(fake.calls)
    b = await p.sector_breadth("Health Care", AS_OF)
    assert len(fake.calls) == calls + 1  # only the ETF's own prices

    assert b.kind == "sector_breadth" and b.subject == "Health Care" and not b.is_gap
    q = b.payload
    assert q["constituents_with_prices"] == 3 and q["missing_prices"] == ["ABBV"]
    assert q["pct_above_50dma"] == q["pct_above_200dma"] == q["pct_positive_1m"] == 0.6667
    assert (q["new_52w_highs"], q["new_52w_lows"]) == (2, 1)
    ew = round((2 * expected_ret("up", 30) + expected_ret("down", 30)) / 3, 4)
    assert q["equal_weight_vs_etf"]["1m"] == {"equal_weight": ew, "etf": 0.0, "spread": ew}


async def test_backtest_snapshots_carry_survivorship_caveat():
    fake = FakeEquibles()
    p = provider(fake, now=lambda: AS_OF + timedelta(days=90))
    b = await p.sector_breadth("XLV", AS_OF)
    assert any("Backtest caveat" in n for n in b.payload["notes"])
    assert b.payload["pct_positive_1m"] == 0.6667  # the post-as_of crash stays invisible


async def test_holdings_not_yet_public_are_a_gap():
    fake = FakeEquibles()
    early = datetime(2026, 5, 15, 21, 0, tzinfo=timezone.utc)  # 2026-03-31 + 60d is 2026-05-30
    snaps = await provider(fake).sector_screen("Healthcare", early)
    assert snaps and all(s.is_gap for s in snaps) and "2026-05-30" in snaps[0].note
    b = await provider(fake).sector_breadth("Healthcare", early)
    assert b.is_gap and b.subject == "Healthcare"
    assert fake.count(PRICES_TOOL) == 0


async def test_unknown_sector_and_missing_fund_are_gaps():
    fake = FakeEquibles()
    [gap] = await provider(fake).sector_screen("Quantum widgets", AS_OF)
    assert gap.is_gap and gap.subject == "Quantum widgets" and "Unknown sector" in gap.note
    assert (await provider(fake).sector_breadth("Quantum widgets", AS_OF)).is_gap
    snaps = await provider(fake).sector_screen("Energy", AS_OF)
    assert all(s.is_gap for s in snaps) and "No NPORT-P holdings for XLE" in snaps[0].note
    assert fake.calls == [(ETF_TOOL, {"ticker": "XLE", "maxResults": 40}),
                          (FUND_TOOL, {"fund": "XLE", "maxResults": 40})]



async def test_etf_holdings_primary():
    """GetEtfHoldings (real hosted format) supplies tickers directly: no 13F name matching."""
    from pathlib import Path

    etf_text = (Path(__file__).parent / "fixtures" / "equibles_live" / "GetEtfHoldings.md").read_text()

    class Fake(FakeEquibles):
        async def call_tool(self, name, args):
            if name == ETF_TOOL:
                self.calls.append((name, args))
                return etf_text
            return await super().call_tool(name, args)

    fake = Fake()
    # The 2026-06-30 report is public from 2026-08-29 (period + 60 days), so screen after that;
    # as of AS_OF (06-30) the same report is correctly withheld.
    later = datetime(2026, 9, 25, 21, 0, tzinfo=timezone.utc)
    assert all(s.is_gap for s in await provider(Fake()).sector_screen("Health Care", AS_OF))
    snaps = await provider(fake, now=lambda: later).sector_screen("Health Care", later)
    screened = {s.subject: s.payload for s in snaps if s.kind == "screen" and not s.is_gap}
    assert set(screened) == {"LLY", "JNJ", "ABBV"}
    assert screened["LLY"]["ticker_source"] == "etf_holdings" and screened["LLY"]["etf_weight_pct"] == 16.51
    assert fake.count(FUND_TOOL) == 0 and fake.count(PORTFOLIO_TOOL) == 0
    cov = next(s for s in snaps if s.kind == "screen_coverage")
    assert "GetEtfHoldings" in cov.payload["constituents_source"]
