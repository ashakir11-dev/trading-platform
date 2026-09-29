"""Tests for .claude/hooks/price_stats.py and its use by the PostToolUse hook."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / ".claude" / "hooks"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HOOKS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


ps = _load("price_stats")
guard = _load("workspace_guard")


def table(closes, start=date(2025, 12, 1), ticker="TEST"):
    """An Equibles-style response: one weekday bar per close, high/low = close ± 1."""
    rows, d = [], start
    for c in closes:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        rows.append(f"| {d} | {c:,.2f} | {c + 1:,.2f} | {c - 1:,.2f} | {c:,.2f} | {c:,.2f} | 1,000 |")
        d += timedelta(days=1)
    return (f"Daily prices for {ticker} (Test Corp):\n\n| Date | Open | High | Low | Close | Adj Close | Volume |\n"
            "|------|------|------|-----|-------|-----------|--------|\n" + "\n".join(rows) +
            "\n\n_Adj Close is the provider-adjusted close._\n\nData: Equibles")


def test_parse_reads_rows_oldest_first():
    title, bars = ps.parse(table([10, 11, 12]))
    assert title.startswith("Daily prices for TEST")
    assert [b.close for b in bars] == [10, 11, 12]
    assert bars[0].volume == 1000


def test_returns_and_moving_averages_are_exact():
    closes = list(range(1, 261))  # 260 bars, last close 260
    text = ps.summary(table(closes), raw_file="raw/001-GetStockPrices.json")
    assert "1w +1.96% (from 255.00" in text          # 260 / 255
    assert "1m +8.79% (from 239.00" in text          # 260 / 239
    assert "SMA20 250.50" in text                    # mean of 241..260
    assert "SMA50 235.50" in text                    # mean of 211..260
    assert "SMA200 160.50" in text                   # mean of 61..260
    assert "closing high 260.00" in text and "closing low 9.00" in text  # last 252 bars
    assert "raw/001-GetStockPrices.json" in text


def test_short_history_says_na_instead_of_guessing():
    text = ps.summary(table([100.0] * 30), raw_file="r.json")
    assert "3m n/a (only 30 bars)" in text
    assert "SMA200 n/a (needs 200 bars, have 30)" in text


def test_ytd_uses_last_close_of_prior_year():
    text = ps.summary(table([50.0] * 23 + [60.0] * 10), raw_file="r.json")  # Dec 2025, then Jan 2026
    assert "YTD +20.00% (from 50.00 on 2025-12-31)" in text


def test_atr_constant_range():
    _, bars = ps.parse(table([100.0] * 30))
    assert ps.atr(bars) == pytest.approx(2.0)  # high - low = 2 every bar


def test_levels_add_pivots_and_weekly_bars():
    closes = [100, 101, 102, 103, 104, 110, 104, 103, 102, 101, 100, 95, 100, 101, 102, 103, 104]
    text = ps.summary(table(closes), raw_file="r.json", with_levels=True)
    assert "Swing highs (5 bars each side), most recent last: 111.00" in text
    assert "Swing lows (5 bars each side), most recent last: 94.00" in text
    assert "| Week to | Open | High | Low | Close | Volume |" in text


def test_weekly_groups_by_iso_week():
    _, bars = ps.parse(table([1, 2, 3, 4, 5, 6, 7], start=date(2025, 12, 1)))  # Mon-Fri, then Mon-Tue
    weeks = ps.weekly(bars)
    assert [(w.open, w.close) for w in weeks] == [(1, 5), (6, 7)]
    assert weeks[0].high == 6 and weeks[0].low == 0


def test_rsi_extremes_and_midpoint():
    _, up = ps.parse(table(list(range(1, 31))))          # only gains
    assert ps.rsi(up) == 100.0
    _, down = ps.parse(table(list(range(60, 30, -1))))   # only losses
    assert ps.rsi(down) == pytest.approx(0.0)
    _, flat = ps.parse(table([10.0, 11.0] * 15))         # equal gains and losses
    assert 45.0 < ps.rsi(flat) < 55.0                    # Wilder smoothing tilts toward the last change
    assert ps.rsi(up[:10]) is None


def test_macd_is_zero_on_a_flat_series_and_positive_in_an_uptrend():
    _, flat = ps.parse(table([100.0] * 60))
    line, sig, hist = ps.macd(flat)
    assert line == pytest.approx(0.0) and sig == pytest.approx(0.0) and hist == pytest.approx(0.0)
    _, up = ps.parse(table([float(x) for x in range(1, 61)]))
    assert ps.macd(up)[0] > 0
    assert ps.macd(up[:30]) is None


def test_vwap_and_relative_volume():
    _, bars = ps.parse(table([100.0] * 25))              # typical price = 100, equal volumes
    assert ps.vwap(bars) == pytest.approx(100.0)
    assert ps.relative_volume(bars) == pytest.approx(1.0)
    spike = bars[:-1] + [ps.Bar(bars[-1].day, 100, 101, 99, 100, 3000)]
    assert ps.relative_volume(spike) == pytest.approx(3.0)
    assert ps.vwap(bars[:5]) is None and ps.relative_volume(bars[:5]) is None


def test_summary_reports_indicators():
    text = ps.summary(table([float(x) for x in range(1, 61)]), raw_file="r.json")
    assert "Indicators: RSI14 100.0; MACD(12,26,9) line" in text
    assert "VWAP20" in text and "relative volume 1.00x" in text
    assert "RSI14 n/a" in ps.summary(table([100.0] * 5), raw_file="r.json")


def test_unparseable_response_raises():
    with pytest.raises(ValueError):
        ps.parse("No price data for XYZ.")


# -- chart-reading statistics (technical agent) ------------------------------------------


def test_trend_lines_give_ma_slopes_order_and_extension():
    _, bars = ps.parse(table([float(x) for x in range(1, 261)]))  # 260 bars, +1 a day
    text = "\n".join(ps.trend_lines(bars))
    assert "SMA50 235.50 vs 215.50 20 bars earlier (+9.28%, rising)" in text     # 211..260 vs 191..240
    assert "SMA200 160.50 vs 140.50 20 bars earlier (+14.23%, rising)" in text   # 61..260 vs 41..240
    assert "30-week MA" in text and "weeks earlier" in text
    # 52 full weeks, weekly closes 5, 10, ..., 260: the last 30 average 5 x 37.5
    assert "MA order, highest first: close 260.00 > SMA50 235.50 > 30-week MA 187.50 > SMA200 160.50;" in text
    assert "close vs SMA50: +12.25 ATR14" in text                                 # (260 - 235.5) / ATR 2


def test_trend_lines_say_na_on_short_history():
    _, bars = ps.parse(table([100.0] * 30))
    text = "\n".join(ps.trend_lines(bars))
    assert "SMA200 slope n/a (needs 220 bars, have 30)" in text
    assert "SMA200 n/a" in text and "30-week MA" in text


def test_falling_ma_is_labelled_falling():
    _, bars = ps.parse(table([float(x) for x in range(300, 40, -1)]))
    assert "SMA50" in ps.trend_lines(bars)[0] and "falling" in ps.trend_lines(bars)[0]
    assert "rising" not in ps.trend_lines(bars)[0]


def test_volatility_contraction_shows_a_low_band_percentile():
    wide = [100 + (5 if i % 2 else -5) for i in range(100)]
    tight = [100 + (0.5 if i % 2 else -0.5) for i in range(40)]
    _, bars = ps.parse(table(wide + tight))
    line = ps.volatility_line(bars)
    assert "current at the 0th percentile" in line
    assert "ATR14" in line and "20 bars earlier (ratio" in line
    widths = ps.bollinger_widths(bars)
    assert widths[-1] == pytest.approx(4 * 0.5 / 100 * 100)  # 4 x sd 0.5 / mean 100, in %


def test_volume_line_up_down_ratio_dry_up_and_heaviest_bars():
    start = date(2026, 1, 1)
    bars, close = [], 100.0
    for i in range(51):
        up = i % 2 == 0
        close += 1 if up else -1
        vol = 3000 if i == 50 else (2000 if up else 1000)
        bars.append(ps.Bar(start + timedelta(days=i), close, close + 1, close - 1, close, vol))
    line = ps.volume_line(bars)
    # last 50 bars (i = 1..50): 25 up (i even: 24 x 2000 + the 3000 spike), 25 down x 1000
    assert "Up/down volume, last 50 bars: 2.04" in line                # (24*2000 + 3000) / 25000
    assert "50-bar average 1,520" in line                              # (51000 + 25000) / 50
    assert f"Heaviest bars of the last 50 (close change, x the 50-bar average): {bars[-1].day}" in line
    assert "Volume: n/a (needs 51 bars" in ps.volume_line(bars[:10])


def test_swing_points_carry_rsi_at_the_pivot():
    closes = [float(x) for x in range(100, 130)] + [float(x) for x in range(129, 110, -1)] + [111.0] * 10
    text = ps.summary(table(closes), raw_file="r.json", with_levels=True)
    assert "Swing highs (5 bars each side), most recent last: 130.00 (" in text and "RSI14 100.0)" in text


def test_ticker_of_reads_the_title():
    assert ps.ticker_of("Daily prices for AAPL (Apple Inc.):") == "AAPL"
    assert ps.ticker_of("Daily prices for brk.b (Berkshire):") == "BRK.B"
    assert ps.ticker_of("No data.") is None


def test_relative_strength_leader_against_a_flat_benchmark():
    _, stock = ps.parse(table([float(x) for x in range(100, 400)], ticker="XOM"))
    _, spy = ps.parse(table([100.0] * 300, ticker="SPY"))
    text = ps.relative("XOM", stock, "SPY", spy)
    assert "300 common dates" in text
    assert "1m +5.56 pp" in text                    # 399 / 378 - 1, SPY flat
    assert "new RS high in the last 5 dates: yes" in text and "new RS low in the last 5 dates: no" in text
    assert "SPY had no pullback in the last 126 common dates" in text


def test_relative_strength_measures_the_stock_during_the_benchmark_pullback():
    bench = [100.0 + i for i in range(40)] + [139.0 - 2 * i for i in range(1, 11)] + [120.0] * 20
    _, stock = ps.parse(table([50.0] * 70, ticker="XOM"))
    _, spy = ps.parse(table(bench, ticker="SPY"))
    text = ps.relative("XOM", stock, "SPY", spy)
    assert "SPY's deepest pullback in the last 70 common dates: -14.39% (139.00" in text  # 139 -> 119
    assert "XOM over the same dates: +0.00% (50.00 to 50.00)" in text
    assert "high on 2025-12-01" in text  # 50 / 100 on day one is the highest ratio
    assert "new RS high in the last 5 dates: no" in text


def test_relative_strength_needs_common_dates():
    _, a = ps.parse(table([1.0] * 30, ticker="A"))
    _, b = ps.parse(table([1.0] * 30, start=date(2027, 1, 4), ticker="B"))
    assert ps.relative("A", a, "B", b) is None


def test_relative_blocks_cover_stock_vs_market_and_sector_and_sector_vs_market():
    series = {t: ps.parse(table([100.0 + i for i in range(60)], ticker=t))[1] for t in ("XOM", "SPY", "XLE")}
    heads = lambda blocks: [b.split(" (")[0] for b in blocks]
    assert heads(ps.relative_blocks("XOM", series, "XLE")) == [
        "Relative strength, XOM vs XLE", "Relative strength, XLE vs SPY"]
    assert heads(ps.relative_blocks("xom", series, "SPY")) == [
        "Relative strength, XOM vs SPY", "Relative strength, XLE vs SPY"]
    only_etfs = {t: series[t] for t in ("SPY", "XLE")}  # stock not fetched yet
    assert heads(ps.relative_blocks("XOM", only_etfs, "XLE")) == ["Relative strength, XLE vs SPY"]


# -- the hook ---------------------------------------------------------------------------

FOLDER = "workspace/agents/market-scanner/analyses/20260925T213314Z/market"


def _event(project, tool, args, agent_type="market-scanner", response=None):
    e = {"cwd": str(project), "tool_name": tool, "tool_input": args,
         "agent_id": "a1", "agent_type": agent_type}
    if response is not None:
        e["tool_response"] = response
    return e


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize("agent_type,levels", [("market-scanner", False), ("technical-analysis", True)])
def test_hook_replaces_price_output_and_keeps_raw(project, agent_type, levels):
    guard.post(_event(project, "Write", {"file_path": f"{FOLDER}/claim.md"}, agent_type))
    response = [{"type": "text", "text": table(list(range(1, 61)))}]
    out = guard.post(_event(project, "mcp__equibles__GetStockPrices", {"ticker": "TEST"}, agent_type, response))

    assert out["hookEventName"] == "PostToolUse"
    text = out["updatedMCPToolOutput"][0]["text"]
    assert "statistics computed from 60 daily bars" in text
    assert f"{FOLDER}/raw/001-GetStockPrices.json" in text
    assert ("Swing highs" in text) is levels
    saved = json.loads((project / FOLDER / "raw" / "001-GetStockPrices.json").read_text())
    assert saved["response"] == response  # verbatim


def test_hook_leaves_other_tools_and_bad_tables_alone(project):
    guard.post(_event(project, "Write", {"file_path": f"{FOLDER}/claim.md"}))
    assert guard.post(_event(project, "mcp__equibles__ListFilings", {"ticker": "X"}, response="| a |")) is None
    assert guard.post(_event(project, "mcp__equibles__GetStockPrices", {"ticker": "X"},
                             response=[{"type": "text", "text": "No data."}])) is None
    assert len(list((project / FOLDER / "raw").iterdir())) == 2


@pytest.mark.parametrize("agent_type", ["follow-up", "stage-evaluator"])
def test_agents_that_need_bars_get_them_unchanged(project, agent_type):
    guard.post(_event(project, "Write", {"file_path": f"{FOLDER}/claim.md"}, agent_type))
    response = [{"type": "text", "text": table(list(range(1, 61)))}]
    assert guard.post(_event(project, "mcp__equibles__GetStockPrices", {"ticker": "T"}, agent_type, response)) is None
    assert (project / FOLDER / "raw" / "001-GetStockPrices.json").exists()


# -- backtest data packs ------------------------------------------------------------------

PACK = "workspace/runs/r1/packs/market-scanner/market"


def _gk(project, tool, args, response=None, agent_type="gatekeeper"):
    return _event(project, tool, args, agent_type, response)


def test_gatekeeper_raw_is_private_and_prices_are_cut_at_as_of(project):
    # as_of = 2025-12-03 18:00 UTC = 13:00 New York: the Dec 3 bar has not closed yet.
    guard.post(_gk(project, "Write", {"file_path": f"{PACK}/claim.md"}))
    (project / PACK).mkdir(parents=True)
    (project / PACK / "claim.md").write_text("---\nas_of: 2025-12-03T18:00:00Z\n---\n")
    response = [{"type": "text", "text": table([10, 11, 12, 13, 14])}]  # Dec 1..5
    assert guard.post(_gk(project, "mcp__equibles__GetStockPrices", {"ticker": "T"}, response)) is None

    assert (project / "workspace/runs/r1/.gatekeeper/market-scanner/market/raw/001-GetStockPrices.json").exists()
    assert not (project / PACK / "raw").exists()
    copied = (project / PACK / "data" / "001-GetStockPrices.md").read_text()
    assert "| 2025-12-02 |" in copied and "| 2025-12-03 |" not in copied
    assert "3 bars after as_of" in copied
    assert "Last close: 11.00 on 2025-12-02" in copied


@pytest.mark.parametrize("agent_type", ["market-scanner-backtest", "pit-auditor"])
@pytest.mark.parametrize("tool,args", [
    ("Read", {"file_path": "workspace/runs/r1/.gatekeeper/market-scanner/market/raw/001-GetStockPrices.json"}),
    ("Glob", {"pattern": "**/*.json", "path": "workspace/runs/r1"}),
    ("Glob", {"pattern": "workspace/runs/*/.gatekeeper/**"}),
    ("Grep", {"pattern": "Close", "path": "workspace/runs"}),
])
def test_backtest_agents_cannot_read_unfiltered_data(project, agent_type, tool, args):
    assert "unfiltered backtest data" in guard.pre(_event(project, tool, args, agent_type))


@pytest.mark.parametrize("tool,args", [
    ("Read", {"file_path": f"{PACK}/data/001-GetStockPrices.md"}),
    ("Glob", {"pattern": "*.md", "path": f"{PACK}/data"}),
    ("Read", {"file_path": "workspace/agents/market-scanner/analyses/r1/market/output.md"}),
])
def test_backtest_agents_can_read_their_pack(project, tool, args):
    assert guard.pre(_event(project, tool, args, "sector-deep-dive-backtest")) is None


def test_parses_a_real_equibles_response_without_adj_close():
    """A captured hosted response (tests/fixtures/equibles_live/GetStockPrices.md)."""
    text = (Path(__file__).parent / "fixtures" / "equibles_live" / "GetStockPrices.md").read_text()
    title, bars = ps.parse(text)
    assert title == "Daily prices for AAPL (Apple Inc.):"
    assert [b.day.isoformat() for b in bars][-1] == "2026-09-24" and len(bars) == 5
    assert bars[0].volume == 86_588_203
    assert "1w n/a (only 5 bars)" in ps.summary(text, raw_file="r.json")


# -- relative strength in the hook ------------------------------------------------------

TA_FOLDER = "workspace/agents/technical-analysis/analyses/20260925T213314Z/XOM"


def test_technical_agent_gets_relative_strength_once_both_tickers_are_in(project):
    guard.post(_event(project, "Write", {"file_path": f"{TA_FOLDER}/claim.md"}, "technical-analysis"))
    price = "mcp__equibles__GetStockPrices"
    xom = [{"type": "text", "text": table([100.0 + i for i in range(60)], ticker="XOM")}]
    spy = [{"type": "text", "text": table([200.0] * 60, ticker="SPY")}]
    xle = [{"type": "text", "text": table([50.0 + i / 2 for i in range(60)], ticker="XLE")}]
    first = guard.post(_event(project, price, {"ticker": "XOM"}, "technical-analysis", xom))
    assert "Relative strength" not in first["updatedMCPToolOutput"][0]["text"]
    second = guard.post(_event(project, price, {"ticker": "SPY"}, "technical-analysis", spy))["updatedMCPToolOutput"][0]["text"]
    assert "Relative strength, XOM vs SPY (" in second
    third = guard.post(_event(project, price, {"ticker": "XLE"}, "technical-analysis", xle))["updatedMCPToolOutput"][0]["text"]
    assert "Relative strength, XOM vs XLE (" in third and "Relative strength, XLE vs SPY (" in third
    assert "Relative strength, XOM vs SPY" not in third  # already given with SPY's response


def test_scanner_gets_no_relative_strength_blocks(project):
    guard.post(_event(project, "Write", {"file_path": f"{FOLDER}/claim.md"}))
    for t in ("SPY", "XLE"):
        out = guard.post(_event(project, "mcp__equibles__GetStockPrices", {"ticker": t}, "market-scanner",
                                [{"type": "text", "text": table([100.0] * 60, ticker=t)}]))
        assert "Relative strength" not in out["updatedMCPToolOutput"][0]["text"]


def test_technical_pack_gets_relative_strength_cut_at_as_of(project):
    pack = "workspace/runs/r1/packs/technical-analysis/XOM"
    guard.post(_gk(project, "Write", {"file_path": f"{pack}/claim.md"}))
    (project / pack).mkdir(parents=True)
    (project / pack / "claim.md").write_text("---\nas_of: 2026-02-20T21:00:00Z\n---\n")
    for t, closes in (("XOM", [100.0 + i for i in range(80)]), ("SPY", [200.0] * 80)):
        guard.post(_gk(project, "mcp__equibles__GetStockPrices", {"ticker": t},
                       [{"type": "text", "text": table(closes, ticker=t)}]))
    spy_file = (project / pack / "data" / "002-GetStockPrices.md").read_text()
    assert "Relative strength, XOM vs SPY (" in spy_file
    assert "to 2026-02-20)" in spy_file  # common dates end at as_of: later bars never reach the pack
    assert "## Daily bars" in spy_file and not list((project / pack / "data").glob(".*.tmp"))
    title, bars = ps.parse(spy_file.split("## Daily bars", 1)[1].strip())
    assert bars[-1].day.isoformat() == "2026-02-20"


def test_relative_strength_merges_chunks_and_works_in_either_order(project):
    guard.post(_event(project, "Write", {"file_path": f"{TA_FOLDER}/claim.md"}, "technical-analysis"))
    price = "mcp__equibles__GetStockPrices"
    spy = [{"type": "text", "text": table([200.0] * 80, ticker="SPY")}]
    guard.post(_event(project, price, {"ticker": "SPY"}, "technical-analysis", spy))
    # the stock in two date-ranged chunks (long_term fetches), arriving after SPY
    early = [{"type": "text", "text": table([100.0 + i for i in range(40)], ticker="XOM")}]
    late = [{"type": "text", "text": table([140.0 + i for i in range(40)], start=date(2026, 1, 26), ticker="XOM")}]
    first = guard.post(_event(project, price, {"ticker": "XOM"}, "technical-analysis", early))
    assert "40 common dates" in first["updatedMCPToolOutput"][0]["text"]
    second = guard.post(_event(project, price, {"ticker": "XOM"}, "technical-analysis", late))
    assert "Relative strength, XOM vs SPY (" in second["updatedMCPToolOutput"][0]["text"]
    assert "80 common dates" in second["updatedMCPToolOutput"][0]["text"]
