#!/usr/bin/env python3
"""Claude Code hooks that enforce the subagent design's hard rules in the harness.

Prompts ask the agents to follow these rules; these hooks make the critical ones hold
even when a prompt is ignored. They contain no pipeline logic.

``pre`` (PreToolUse, every tool) denies:
  * any Equibles write tool (portfolios, lots, watches, reports), for every caller;
  * a subagent touching ``workspace/decisions/`` (the user's decisions) in any way;
  * a Equibles data call from the middleware agent (it never fetches data), from a
    ``*-backtest`` agent (backtests read gatekeeper data packs only), or from a subagent
    that has not claimed its analysis folder yet.

``post`` (PostToolUse, ``Write``/``Edit`` and Equibles tools):
  * a subagent's first write inside ``workspace/agents/<agent>/analyses/<run>/<subject>/``
    claims that folder for the subagent;
  * every Equibles response a subagent receives is saved verbatim to its claimed
    folder's ``raw/``, so raw data travels with the analysis without the agent copying it;
  * for the market scanner, sector deep dive and technical analysis, a ``GetStockPrices``
    response is replaced by statistics computed from it (``price_stats.py``); the full
    rows stay in ``raw/``.

Hook input (JSON on stdin) carries ``agent_id``/``agent_type`` only inside a subagent.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import price_stats  # noqa: E402

EQUIBLES_PREFIX = "mcp__equibles__"
WRITE_TOOLS = frozenset({
    "CreateMyPortfolio", "DeleteMyPortfolio", "AddPortfolioLot", "UpdatePortfolioLot",
    "ClosePortfolioLot", "RemovePortfolioLot", "WatchInstrument", "UnwatchInstrument",
    "ReportProblem", "SuggestToolImprovement",
})
# Agents that get price statistics instead of daily rows. The others (follow-up,
# evaluators) need individual bars to tell when a stop or target was hit.
STATS_AGENTS = frozenset({"market-scanner", "sector-deep-dive", "technical-analysis"})
FILE_TOOLS = frozenset({"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"})
SEARCH_TOOLS = frozenset({"Glob", "Grep", "LS"})


def project_dir(event: dict[str, Any]) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()


def workspace(event: dict[str, Any]) -> Path:
    return project_dir(event) / "workspace"


def _resolve(path: str, event: dict[str, Any]) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path(event.get("cwd") or project_dir(event)) / p
    return Path(os.path.normpath(p))


def _inside(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def _claim_file(event: dict[str, Any], agent_id: str) -> Path:
    return workspace(event) / ".state" / "claims" / f"{agent_id}.json"


def claimed_folder(event: dict[str, Any], agent_id: str) -> Path | None:
    f = _claim_file(event, agent_id)
    if not f.is_file():
        return None
    return Path(json.loads(f.read_text())["folder"])


def analysis_folder_of(path: Path, event: dict[str, Any]) -> Path | None:
    """The claimable folder containing ``path``, if any:
    ``workspace/agents/<agent>/analyses/<run>/<subject>`` or
    ``workspace/agents/<agent>/evaluations/<eval_id>`` or (the gatekeeper's backtest data
    packs) ``workspace/runs/<run>/packs/<stage>/<subject>``."""
    try:
        rel = path.relative_to(workspace(event))
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) >= 6 and parts[0] == "agents" and parts[2] == "analyses":
        return workspace(event).joinpath(*parts[:5])
    if len(parts) >= 5 and parts[0] == "agents" and parts[2] == "evaluations":
        return workspace(event).joinpath(*parts[:4])
    if len(parts) >= 6 and parts[0] == "runs" and parts[2] == "packs":
        return workspace(event).joinpath(*parts[:5])
    return None


def _pack_parts(folder: Path, event: dict[str, Any]) -> tuple[str, str, str] | None:
    """(run, stage, subject) if ``folder`` is a backtest data pack."""
    try:
        parts = folder.relative_to(workspace(event)).parts
    except ValueError:
        return None
    return (parts[1], parts[3], parts[4]) if len(parts) == 5 and parts[0] == "runs" and parts[2] == "packs" else None


def gatekeeper_raw(event: dict[str, Any], run: str, stage: str, subject: str) -> Path:
    """Unfiltered gatekeeper responses: never readable by backtest stage agents or the auditor."""
    return workspace(event) / "runs" / run / ".gatekeeper" / stage / subject / "raw"


# --------------------------------------------------------------------------------------
# PreToolUse
# --------------------------------------------------------------------------------------


def _touches_decisions(event: dict[str, Any]) -> bool:
    decisions = workspace(event) / "decisions"
    tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
    if tool in FILE_TOOLS:
        path = args.get("file_path") or args.get("notebook_path")
        if path and _inside(_resolve(path, event), decisions):
            return True
    if tool in SEARCH_TOOLS:
        # A search whose root is at or above decisions/ would expose it; one inside it too.
        # The root is the path plus the pattern's literal (wildcard-free) leading folders.
        root = _resolve(args.get("path") or event.get("cwd") or str(project_dir(event)), event)
        pattern = args.get("pattern", "") if tool == "Glob" else args.get("glob", "") or ""
        literal = []
        for part in Path(pattern).parts[:-1]:
            if any(c in part for c in "*?[{"):
                break
            literal.append(part)
        root = _resolve(str(root.joinpath(*literal)), event)
        if _inside(decisions, root) or _inside(root, decisions):
            return True
    if tool == "Bash":
        return bool(re.search(r"decisions(/|\b)", args.get("command", "")))
    return False


def _search_root(event: dict[str, Any]) -> Path:
    args = event.get("tool_input") or {}
    root = _resolve(args.get("path") or event.get("cwd") or str(project_dir(event)), event)
    pattern = args.get("pattern", "") if event.get("tool_name") == "Glob" else args.get("glob", "") or ""
    literal = []
    for part in Path(pattern).parts[:-1]:
        if any(c in part for c in "*?[{"):
            break
        literal.append(part)
    return _resolve(str(root.joinpath(*literal)), event)


def _touches_gatekeeper_raw(event: dict[str, Any]) -> bool:
    """Would this call reach ``runs/<run>/.gatekeeper/`` (unfiltered backtest data)?"""
    tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
    if any(".gatekeeper" in str(v) for v in args.values() if isinstance(v, str) and tool != "Write"):
        return True
    if tool in FILE_TOOLS:
        path = args.get("file_path") or args.get("notebook_path")
        return bool(path) and ".gatekeeper" in _resolve(path, event).parts
    if tool in SEARCH_TOOLS:
        root = _search_root(event)
        runs = workspace(event) / "runs"
        # Searches must stay inside a pack, an analysis folder or prompts/: a root at or
        # above a run folder would include its .gatekeeper/.
        if ".gatekeeper" in root.parts or _inside(runs, root):
            return True
        try:
            rel = root.relative_to(runs).parts
        except ValueError:
            return False
        return len(rel) <= 1
    return False


def pre(event: dict[str, Any]) -> str | None:
    """Reason to deny, or None to let the normal permission flow decide."""
    tool = event.get("tool_name", "")
    agent_id, agent_type = event.get("agent_id"), event.get("agent_type") or ""
    lower = tool.lower()

    if lower.startswith(EQUIBLES_PREFIX) and tool.split("__")[-1] in WRITE_TOOLS:
        return f"{tool} changes the Equibles account; the pipeline is read-only."

    if agent_id and _touches_decisions(event):
        return ("workspace/decisions/ holds the user's decisions; only the middleware agent may "
                "read it, and it never reaches a stage agent. Give searches a narrower path "
                "(e.g. your analysis folder).")

    if agent_id and (agent_type.endswith("-backtest") or agent_type == "pit-auditor") \
            and _touches_gatekeeper_raw(event):
        return ("runs/<run>/.gatekeeper/ holds unfiltered backtest data; read only your data pack "
                "(runs/<run>/packs/<stage>/<subject>/). Give searches that folder as their path.")

    if tool.startswith(EQUIBLES_PREFIX):
        if not agent_id:
            return "The middleware agent does not fetch data; launch the stage agent that needs it."
        if agent_type.endswith("-backtest"):
            return "Backtest agents read their gatekeeper data pack only; they have no data tools."
        if claimed_folder(event, agent_id) is None:
            return ("Claim your analysis folder first: Write <analysis_folder>/claim.md (see "
                    "prompts/shared.md), then call data tools. Responses are saved to its raw/.")
    return None


# --------------------------------------------------------------------------------------
# PostToolUse
# --------------------------------------------------------------------------------------


def post(event: dict[str, Any]) -> dict[str, Any] | None:
    """Hook-specific output to return (a replaced tool output), or None."""
    tool, agent_id = event.get("tool_name", ""), event.get("agent_id")
    if not agent_id:
        return None
    args = event.get("tool_input") or {}

    if tool in {"Write", "Edit", "MultiEdit"} and args.get("file_path"):
        folder = analysis_folder_of(_resolve(args["file_path"], event), event)
        claim = _claim_file(event, agent_id)
        if folder is not None and not claim.exists():
            claim.parent.mkdir(parents=True, exist_ok=True)
            claim.write_text(json.dumps({"folder": str(folder), "agent_type": event.get("agent_type"),
                                         "claimed_at": _now()}))
        return None

    if tool.startswith(EQUIBLES_PREFIX):
        folder = claimed_folder(event, agent_id)
        if folder is None:  # pre() blocks this; keep the data anyway
            folder = workspace(event) / ".state" / "unclaimed" / agent_id
        pack = _pack_parts(folder, event)
        raw = gatekeeper_raw(event, *pack) if pack else folder / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        name = tool.split("__")[-1]
        body = json.dumps({"tool": name, "input": args, "received_at": _now(),
                           "response": event.get("tool_response")}, indent=1, default=str)
        seq = len(list(raw.glob("*.json"))) + 1
        while True:  # parallel tool calls: exclusive create, take the next free number
            try:
                path = raw / f"{seq:03d}-{name}.json"
                with open(path, "x") as f:
                    f.write(body)
                break
            except FileExistsError:
                seq += 1
        if name == "GetStockPrices" and pack:
            _pack_prices(event, folder, path)
        elif name == "GetStockPrices" and (event.get("agent_type") or "") in STATS_AGENTS:
            return _price_stats_output(event, path)
    return None


def _pack_as_of(folder: Path) -> datetime | None:
    claim = folder / "claim.md"
    if not claim.is_file():
        return None
    m = re.search(r"^as_of:\s*(\S+)", claim.read_text(), re.MULTILINE)
    if not m:
        return None
    try:
        return datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
    except ValueError:
        return None


def _pack_prices(event: dict[str, Any], folder: Path, raw_path: Path) -> None:
    """Copy a gatekeeper price response into its pack, keeping only bars closed by as_of.

    A daily bar counts from 16:00 New York time on its date. This is a mechanical filter
    in addition to the gatekeeper's own; the pit-auditor still checks the pack."""
    as_of = _pack_as_of(folder)
    try:
        title, bars = price_stats.parse(_response_text(event.get("tool_response")))
    except ValueError:
        return
    if as_of is None:
        return  # no claim with as_of: nothing safe to copy; the gatekeeper must write it
    ny = ZoneInfo("America/New_York")
    kept = [b for b in bars if datetime.combine(b.day, time(16), ny) <= as_of]
    dropped = len(bars) - len(kept)
    data = folder / "data"
    data.mkdir(parents=True, exist_ok=True)
    name = raw_path.stem  # NNN-GetStockPrices
    if not kept:
        (data / f"{name}.md").write_text(f"{title}\nNo bars closed by as_of {as_of.isoformat()} "
                                         f"({dropped} later bars dropped).\n")
        return
    table = [title, "", "| Date | Open | High | Low | Close | Volume |", "|---|---|---|---|---|---|"]
    table += [f"| {b.day} | {b.open} | {b.high} | {b.low} | {b.close} | {b.volume:.0f} |" for b in kept]
    text = "\n".join(table)
    stats = price_stats.summary(text, raw_file=f"data/{name}.md", with_levels=True)
    (data / f"{name}.md").write_text(
        f"<!-- copied by the hook from the gatekeeper's response; {dropped} bars after as_of "
        f"{as_of.isoformat()} dropped -->\n{stats}\n\n## Daily bars\n\n{text}\n")


def _response_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        response = response.get("content", [])
    if isinstance(response, list):
        return "\n".join(b.get("text", "") for b in response if isinstance(b, dict))
    return ""


def _price_stats_output(event: dict[str, Any], path: Path) -> dict[str, Any] | None:
    """Replace hundreds of daily rows with computed statistics (the rows stay in raw/).

    The technical-analysis agent also gets swing highs/lows and weekly bars, since it
    reads levels. If the response can't be parsed, the agent sees it unchanged."""
    try:
        rel = path.relative_to(project_dir(event))
    except ValueError:
        rel = path
    try:
        text = price_stats.summary(_response_text(event.get("tool_response")), raw_file=str(rel),
                                   with_levels=(event.get("agent_type") or "").startswith("technical-analysis"))
    except (ValueError, KeyError):
        return None
    return {"hookEventName": "PostToolUse", "updatedMCPToolOutput": [{"type": "text", "text": text}]}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else ""
    event = json.load(sys.stdin)
    if mode == "pre":
        reason = pre(event)
        if reason:
            json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": "deny",
                                              "permissionDecisionReason": reason}}, sys.stdout)
        return 0
    if mode == "post":
        out = post(event)
        if out:
            json.dump({"hookSpecificOutput": out}, sys.stdout)
        return 0
    print(f"usage: {argv[0]} pre|post", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
