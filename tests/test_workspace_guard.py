"""Tests for the Claude Code hooks in .claude/hooks/workspace_guard.py."""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "workspace_guard.py"
spec = importlib.util.spec_from_file_location("workspace_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

FOLDER = "workspace/agents/sector-deep-dive/analyses/20260925T213314Z/energy"


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return tmp_path


def event(project, tool, args=None, *, agent="a1", agent_type="sector-deep-dive", response=None):
    e = {"cwd": str(project), "tool_name": tool, "tool_input": args or {}}
    if agent:
        e |= {"agent_id": agent, "agent_type": agent_type}
    if response is not None:
        e["tool_response"] = response
    return e


def claim(project, agent="a1"):
    guard.post(event(project, "Write", {"file_path": f"{FOLDER}/claim.md", "content": "---\n---\n"}, agent=agent))


@pytest.mark.parametrize("agent", ["a1", None])
def test_equibles_write_tools_denied_for_everyone(project, agent):
    assert guard.pre(event(project, "mcp__equibles__AddPortfolioLot", agent=agent))
    assert guard.pre(event(project, "mcp__Equibles__WatchInstrument", agent=agent))


@pytest.mark.parametrize("tool,args", [
    ("Read", {"file_path": "workspace/decisions/x.md"}),
    ("Write", {"file_path": "/{p}/workspace/decisions/x.md", "content": ""}),
    ("Edit", {"file_path": "workspace/agents/../decisions/x.md"}),
    ("Glob", {"pattern": "**/*.md"}),
    ("Glob", {"pattern": "*.md", "path": "workspace"}),
    ("Glob", {"pattern": "workspace/decisions/*.md"}),
    ("Grep", {"pattern": "accept"}),
    ("Grep", {"pattern": "accept", "path": "workspace/decisions"}),
    ("Bash", {"command": "cat workspace/decisions/x.md"}),
])
def test_subagents_cannot_reach_decisions(project, tool, args):
    args = {k: v.replace("/{p}", str(project)) for k, v in args.items()}
    assert guard.pre(event(project, tool, args))
    assert guard.pre(event(project, tool, args, agent=None)) is None  # the middleware agent may


@pytest.mark.parametrize("tool,args", [
    ("Read", {"file_path": f"{FOLDER}/raw/001-GetStockPrices.json"}),
    ("Glob", {"pattern": f"{FOLDER}/raw/*.json"}),
    ("Glob", {"pattern": "*.json", "path": f"{FOLDER}/raw"}),
    ("Grep", {"pattern": "XLE", "path": "workspace/agents"}),
    ("Write", {"file_path": f"{FOLDER}/output.md", "content": "Rate decisions by the Fed matter."}),
])
def test_normal_agent_work_is_allowed(project, tool, args):
    assert guard.pre(event(project, tool, args)) is None


def test_middleware_does_not_fetch_data(project):
    assert "does not fetch data" in guard.pre(event(project, "mcp__equibles__GetStockPrices", agent=None))


def test_backtest_agents_have_no_data_tools(project):
    claim(project)
    assert guard.pre(event(project, "mcp__equibles__GetStockPrices", agent_type="sector-deep-dive-backtest"))


def test_data_calls_need_a_claimed_folder_and_are_saved_to_raw(project):
    tool = "mcp__equibles__GetStockPrices"
    assert "Claim your analysis folder" in guard.pre(event(project, tool))

    claim(project)
    assert guard.pre(event(project, tool)) is None
    guard.post(event(project, tool, {"ticker": "XLE"}, response=[{"type": "text", "text": "| date | close |"}]))
    guard.post(event(project, tool, {"ticker": "SPY"}, response="table"))

    raw = sorted((project / FOLDER / "raw").iterdir())
    assert [p.name for p in raw] == ["001-GetStockPrices.json", "002-GetStockPrices.json"]
    saved = json.loads(raw[0].read_text())
    assert saved["tool"] == "GetStockPrices" and saved["input"] == {"ticker": "XLE"}
    assert saved["response"][0]["text"] == "| date | close |"


def test_claim_is_per_agent_and_first_write_wins(project):
    claim(project, agent="a1")
    guard.post(event(project, "Write", {"file_path": "workspace/agents/x/analyses/r/other/claim.md"}, agent="a1"))
    assert guard.claimed_folder(event(project, "Read"), "a1") == project / FOLDER
    assert guard.pre(event(project, "mcp__equibles__GetStockPrices", agent="a2"))  # a2 has not claimed


def test_writes_outside_analysis_folders_do_not_claim(project):
    guard.post(event(project, "Write", {"file_path": "workspace/runs/r/run.md"}))
    assert guard.claimed_folder(event(project, "Read"), "a1") is None


def test_main_prints_deny_json(project, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event(project, "Read", {"file_path": "workspace/decisions/x.md"}))))
    assert guard.main(["guard", "pre"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_evaluation_folders_can_be_claimed(project):
    guard.post(event(project, "Write", {"file_path": "workspace/agents/technical-analysis/evaluations/r1--20261026/claim.md"},
                     agent_type="stage-evaluator"))
    assert guard.claimed_folder(event(project, "Read"), "a1") == \
        project / "workspace/agents/technical-analysis/evaluations/r1--20261026"
