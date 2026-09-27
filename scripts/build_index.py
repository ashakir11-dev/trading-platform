#!/usr/bin/env python3
"""Build a queryable SQLite index over workspace/ for the tracking dashboard.

    python3 scripts/build_index.py [workspace_dir]

Walks the run manifests, agent analyses, decisions and positions written under
``workspace/`` (formats in ``prompts/formats.md``) and loads them into
``workspace/index.sqlite3``. This is a disposable index, not a second source of truth:
it is rebuilt from the files every time, so the files stay authoritative and this
script never writes into ``workspace/decisions/`` or any analysis folder — only into
its own database file. Standard library only.

Run it again (e.g. after ``/run``, ``/decide`` or ``/trade``) to refresh the dashboard;
``render_dashboard.py`` reads whatever is in the database at the time.
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
ALERT_LINE = re.compile(r"^-\s*(\S+)\s+(delivered|held)\s+([^:]+):\s*(.*?)\s*\(run (\S+)\)\s*$")


def parse_frontmatter(text: str) -> dict[str, str]:
    """A minimal parser for the flat ``key: value`` frontmatter these files use.

    Good enough for the scalars the dashboard needs; nested structures (``upstream:
    [...]``, ``options: {...}``) are kept as their raw, unparsed string."""
    m = FRONTMATTER.match(text)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line[0] in " \t#":
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if len(value) > 1 and value[0] in "'\"" and value[-1] == value[0]:
            value = value[1:-1]
        fields[key.strip()] = value
    return fields


def as_float(value: str | None) -> float | None:
    if value in (None, "", "null", "~"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


SCHEMA = """
CREATE TABLE runs (
  run_id TEXT PRIMARY KEY, mode TEXT, as_of TEXT, status TEXT, prompt_commit TEXT, path TEXT
);
CREATE TABLE analyses (
  id INTEGER PRIMARY KEY, agent TEXT, run_id TEXT, subject TEXT, mode TEXT, as_of TEXT,
  prompt_commit TEXT, verdict TEXT, confidence REAL, direction TEXT, potential_score REAL,
  entry REAL, stop REAL, target REAL, horizon TEXT, path TEXT
);
CREATE TABLE decisions (
  candidate_id TEXT PRIMARY KEY, run_id TEXT, ticker TEXT, decision TEXT, decided_at TEXT,
  position_id TEXT, why TEXT
);
CREATE TABLE positions (
  position_id TEXT PRIMARY KEY, ticker TEXT, direction TEXT, opened TEXT, entry REAL,
  stop REAL, target REAL, horizon TEXT, status TEXT, closed TEXT, exit_price REAL,
  last_check TEXT, last_full_review TEXT, plan TEXT
);
CREATE TABLE alerts (
  id INTEGER PRIMARY KEY, position_id TEXT, as_of TEXT, state TEXT, kind TEXT, detail TEXT,
  run_id TEXT
);
CREATE INDEX idx_analyses_run_subject ON analyses(run_id, subject);
CREATE INDEX idx_analyses_agent ON analyses(agent);
CREATE INDEX idx_decisions_run_ticker ON decisions(run_id, ticker);
CREATE INDEX idx_alerts_position ON alerts(position_id);
"""


def index_runs(ws: Path, conn: sqlite3.Connection) -> None:
    for run_md in sorted(ws.glob("runs/*/run.md")):
        f = parse_frontmatter(run_md.read_text())
        conn.execute(
            "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?)",
            (f.get("run_id") or run_md.parent.name, f.get("mode"), f.get("as_of"), f.get("status"),
             f.get("prompt_commit"), str(run_md.parent)),
        )


def index_analyses(ws: Path, conn: sqlite3.Connection) -> None:
    for output_md in sorted(ws.glob("agents/*/analyses/*/*/output.md")):
        f = parse_frontmatter(output_md.read_text())
        agent = output_md.parents[2].name  # agents/<agent>/analyses/<run>/<subject>/output.md
        conn.execute(
            "INSERT INTO analyses (agent, run_id, subject, mode, as_of, prompt_commit, verdict, "
            "confidence, direction, potential_score, entry, stop, target, horizon, path) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f.get("agent") or agent, f.get("run_id") or output_md.parents[1].name,
             f.get("subject") or output_md.parent.name, f.get("mode"), f.get("as_of"),
             f.get("prompt_commit"), f.get("verdict"), as_float(f.get("confidence")),
             f.get("direction"), as_float(f.get("potential_score")), as_float(f.get("entry")),
             as_float(f.get("stop")), as_float(f.get("target")), f.get("horizon"),
             str(output_md.parent)),
        )


def index_decisions(ws: Path, conn: sqlite3.Connection) -> None:
    for dec_md in sorted(ws.glob("decisions/*.md")):
        text = dec_md.read_text()
        f = parse_frontmatter(text)
        why_match = re.search(r"## Why\n(.*?)(\n##|\Z)", text, re.S)
        why = why_match.group(1).strip() if why_match else None
        conn.execute(
            "INSERT OR REPLACE INTO decisions VALUES (?,?,?,?,?,?,?)",
            (f.get("candidate_id") or dec_md.stem, f.get("run_id"), f.get("ticker"), f.get("decision"),
             f.get("decided_at"), f.get("position_id"), why),
        )


def index_positions(ws: Path, conn: sqlite3.Connection) -> None:
    for pos_md in sorted(ws.glob("positions/*/position.md")):
        f = parse_frontmatter(pos_md.read_text())
        position_id = f.get("position_id") or pos_md.parent.name
        conn.execute(
            "INSERT OR REPLACE INTO positions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (position_id, f.get("ticker"), f.get("direction"), f.get("opened"), as_float(f.get("entry")),
             as_float(f.get("stop")), as_float(f.get("target")), f.get("horizon"), f.get("status"),
             f.get("closed"), as_float(f.get("exit_price")), f.get("last_check"),
             f.get("last_full_review"), f.get("plan")),
        )
        alerts_md = pos_md.with_name("alerts.md")
        if alerts_md.is_file():
            for line in alerts_md.read_text().splitlines():
                m = ALERT_LINE.match(line.strip())
                if m:
                    as_of, state, kind, detail, run_id = m.groups()
                    conn.execute(
                        "INSERT INTO alerts (position_id, as_of, state, kind, detail, run_id) "
                        "VALUES (?,?,?,?,?,?)",
                        (position_id, as_of, state, kind.strip(), detail, run_id),
                    )


def build(ws: Path, db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    index_runs(ws, conn)
    index_analyses(ws, conn)
    index_decisions(ws, conn)
    index_positions(ws, conn)
    conn.commit()
    conn.close()


def main(argv: list[str]) -> int:
    ws = Path(argv[1]) if len(argv) > 1 else Path("workspace")
    if not ws.is_dir():
        print(f"no workspace at {ws}", file=sys.stderr)
        return 2
    db_path = ws / "index.sqlite3"
    build(ws, db_path)
    print(db_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
