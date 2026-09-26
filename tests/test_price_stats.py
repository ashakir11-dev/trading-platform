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


def table(closes, start=date(2025, 12, 1)):
    """An Equibles-style response: one weekday bar per close, high/low = close ± 1."""
    rows, d = [], start
    for c in closes:
        while d.weekday() >= 5:
            d += timedelta(days=1)
        rows.append(f"| {d} | {c:,.2f} | {c + 1:,.2f} | {c - 1:,.2f} | {c:,.2f} | {c:,.2f} | 1,000 |")
        d += timedelta(days=1)
    return ("Daily prices for TEST (Test Corp):\n\n| Date | Open | High | Low | Close | Adj Close | Volume |\n"
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


def test_unparseable_response_raises():
    with pytest.raises(ValueError):
        ps.parse("No price data for XYZ.")


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
