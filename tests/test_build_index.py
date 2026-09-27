"""Tests for scripts/build_index.py and scripts/render_dashboard.py."""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


bi = _load("build_index")
rd = _load("render_dashboard")

RUN_ID = "20260925T213314Z"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def make_workspace(ws: Path) -> None:
    _write(ws / "runs" / RUN_ID / "run.md", f"""---
run_id: {RUN_ID}
mode: live
as_of: 2026-09-25T21:33:14Z
prompt_commit: 174a3ea
status: complete
---
## Stages
""")

    _write(ws / "agents" / "company-deep-dive" / "analyses" / RUN_ID / "XOM" / "output.md", f"""---
agent: company-deep-dive
run_id: {RUN_ID}
mode: default
subject: XOM
as_of: 2026-09-25T21:33:14Z
prompt_commit: 174a3ea
confidence: 0.71
verdict: worthy
---
## Summary
""")
    _write(ws / "agents" / "technical-analysis" / "analyses" / RUN_ID / "XOM" / "output.md", f"""---
agent: technical-analysis
run_id: {RUN_ID}
mode: default
subject: XOM
as_of: 2026-09-25T21:33:14Z
prompt_commit: 174a3ea
confidence: 0.64
verdict: recommended
direction: long
entry: 118.40
stop: 111.00
target: 134.00
horizon: swing
---
## Summary
""")
    # A second candidate rejected before the technical stage ever ran.
    _write(ws / "agents" / "company-deep-dive" / "analyses" / RUN_ID / "CVX" / "output.md", f"""---
agent: company-deep-dive
run_id: {RUN_ID}
mode: default
subject: CVX
as_of: 2026-09-25T21:33:14Z
prompt_commit: 174a3ea
confidence: 0.30
verdict: not_worthy
---
## Summary
""")

    position_id = f"{RUN_ID}-XOM"
    _write(ws / "decisions" / f"{position_id}.md", f"""---
candidate_id: {position_id}
run_id: {RUN_ID}
ticker: XOM
decision: accept
decided_at: 2026-09-26T14:05:00-04:00
position_id: {position_id}
---
## Why
Reward:risk was strong and the catalyst checked out.

## Trade log
| date | action | price | size |
|---|---|---|---|
""")
    _write(ws / "positions" / position_id / "position.md", f"""---
position_id: {position_id}
ticker: XOM
direction: long
opened: 2026-09-26
entry: 118.40
stop: 111.00
target: 134.00
horizon: swing
level_trigger: close
status: open
closed: null
exit_price: null
plan: workspace/agents/technical-analysis/analyses/{RUN_ID}/XOM
---
""")
    _write(ws / "positions" / position_id / "alerts.md",
          f"- 2026-10-01T14:00:00Z delivered price_stop_hit: closed below stop (run {RUN_ID})\n")


def test_parse_frontmatter_scalars():
    fields = bi.parse_frontmatter("---\nrun_id: 20260925T213314Z\nconfidence: 0.64\nverdict: worthy\n---\n")
    assert fields == {"run_id": "20260925T213314Z", "confidence": "0.64", "verdict": "worthy"}


def test_build_and_query(tmp_path):
    ws = tmp_path / "workspace"
    make_workspace(ws)
    db_path = ws / "index.sqlite3"
    bi.build(ws, db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    runs = conn.execute("SELECT * FROM runs").fetchall()
    assert len(runs) == 1 and runs[0]["run_id"] == RUN_ID

    analyses = conn.execute("SELECT * FROM analyses ORDER BY subject").fetchall()
    assert [a["subject"] for a in analyses] == ["CVX", "XOM", "XOM"]
    xom_ta = next(a for a in analyses if a["subject"] == "XOM" and a["agent"] == "technical-analysis")
    assert xom_ta["entry"] == 118.40 and xom_ta["confidence"] == 0.64

    decisions = conn.execute("SELECT * FROM decisions").fetchall()
    assert decisions[0]["decision"] == "accept"
    assert "Reward:risk" in decisions[0]["why"]

    positions = conn.execute("SELECT * FROM positions").fetchall()
    assert positions[0]["status"] == "open" and positions[0]["entry"] == 118.40

    alerts = conn.execute("SELECT * FROM alerts").fetchall()
    assert len(alerts) == 1 and alerts[0]["state"] == "delivered"
    conn.close()


def test_dashboard_renders_accepted_and_rejected(tmp_path):
    ws = tmp_path / "workspace"
    make_workspace(ws)
    db_path = ws / "index.sqlite3"
    bi.build(ws, db_path)

    conn = sqlite3.connect(db_path)
    candidates = rd.fetch(conn, rd.CANDIDATES_SQL)
    positions = rd.fetch(conn, rd.POSITIONS_SQL)
    runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    conn.close()

    assert len(candidates) == 2  # XOM (accepted) and CVX (rejected, no technical stage)
    html = rd.render(candidates, positions, runs)
    assert html.startswith("<!doctype html>")
    assert "XOM" in html and "CVX" in html
    assert "accept" in html
    assert "118.40" in html


def test_build_index_never_touches_decisions_source_files(tmp_path):
    """The index writer only ever writes its own sqlite file, never back into workspace/."""
    ws = tmp_path / "workspace"
    make_workspace(ws)
    db_path = ws / "index.sqlite3"
    before = (ws / "decisions" / f"{RUN_ID}-XOM.md").read_text()
    bi.build(ws, db_path)
    after = (ws / "decisions" / f"{RUN_ID}-XOM.md").read_text()
    assert before == after
