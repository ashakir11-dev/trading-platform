#!/usr/bin/env python3
"""Render the tracking dashboard from workspace/index.sqlite3 as one HTML page.

    python3 scripts/build_index.py && python3 scripts/render_dashboard.py

Reads the index built by ``build_index.py`` (never the raw workspace files directly)
and lays out every candidate the pipeline has produced: the company and technical
verdicts, your accept/reject decision, the position it opened and where that position
stands now. It computes nothing but simple counts and rates from the indexed numbers,
and opens offline like ``report.html``. Standard library only.
"""

from __future__ import annotations

import sqlite3
import sys
from html import escape
from pathlib import Path
from typing import Any


def e(value: Any) -> str:
    return escape("" if value is None else str(value))


def num(value: Any) -> str:
    return "—" if value is None else f"{value:,.2f}"


def pct(part: int, whole: int) -> str:
    return "—" if not whole else f"{part / whole * 100:.0f}%"


def chip(text: str, kind: str) -> str:
    return f'<span class="chip chip-{e(kind)}">{e(text)}</span>' if text else ""


def decision_kind(decision: str | None) -> str:
    return {"accept": "accept", "reject": "reject"}.get(decision or "", "pending")


def position_kind(status: str | None) -> str:
    return {"open": "open", "closed": "closed"}.get(status or "", "none")


# --------------------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------------------

CANDIDATES_SQL = """
SELECT cd.run_id, cd.subject AS ticker, r.as_of,
       cd.verdict AS company_verdict, cd.confidence AS company_confidence,
       ta.verdict AS ta_verdict, ta.confidence AS ta_confidence, ta.direction,
       ta.entry, ta.stop, ta.target, ta.horizon,
       d.candidate_id, d.decision, d.decided_at, d.position_id, d.why,
       p.status AS position_status, p.exit_price, p.closed
FROM analyses cd
JOIN runs r ON r.run_id = cd.run_id
LEFT JOIN analyses ta ON ta.agent = 'technical-analysis' AND ta.run_id = cd.run_id
                     AND ta.subject = cd.subject
LEFT JOIN decisions d ON d.run_id = cd.run_id AND d.ticker = cd.subject
LEFT JOIN positions p ON p.position_id = d.position_id
WHERE cd.agent = 'company-deep-dive'
ORDER BY r.as_of DESC, cd.subject
"""

POSITIONS_SQL = """
SELECT p.*, (SELECT COUNT(*) FROM alerts a WHERE a.position_id = p.position_id) AS alert_count,
       (SELECT MAX(as_of) FROM alerts a WHERE a.position_id = p.position_id) AS last_alert
FROM positions p ORDER BY COALESCE(p.opened, '') DESC
"""


def fetch(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(sql).fetchall()


# --------------------------------------------------------------------------------------
# Pieces
# --------------------------------------------------------------------------------------


def tile(label: str, value: str, sub: str = "") -> str:
    return (f'<div class="tile"><div class="k">{e(label)}</div><div class="v">{e(value)}</div>'
            f'<div class="s">{e(sub)}</div></div>')


def summary(candidates: list[sqlite3.Row], positions: list[sqlite3.Row], runs: int) -> str:
    decided = [c for c in candidates if c["decision"]]
    accepted = [c for c in decided if c["decision"] == "accept"]
    rejected_stage = [c for c in candidates if not c["decision"] and
                      ((c["ta_verdict"] and "reject" in (c["ta_verdict"] or "").lower())
                       or (c["company_verdict"] and c["company_verdict"].lower() not in ("worthy", "")))]
    open_pos = [p for p in positions if p["status"] == "open"]
    tiles = [
        tile("Candidates", str(len(candidates)), f"across {runs} run(s)"),
        tile("Accepted", str(len(accepted)), pct(len(accepted), len(decided)) + " of decided"),
        tile("Rejected", str(len(decided) - len(accepted) + len(rejected_stage)),
             "by you or a stage verdict"),
        tile("Open positions", str(len(open_pos)), f"{len(positions) - len(open_pos)} closed"),
    ]
    return f'<div class="tiles">{"".join(tiles)}</div>'


def candidates_table(rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "<p class=muted>No candidates indexed yet — run the pipeline and /decide, then rebuild the index.</p>"
    body = []
    for c in rows:
        plan = "—"
        if c["entry"] is not None:
            plan = f'{num(c["entry"])} / {num(c["stop"])} / {num(c["target"])}'
        decision = c["decision"] or ("rejected" if (c["ta_verdict"] and "reject" in
                                     (c["ta_verdict"] or "").lower()) else "pending")
        pos = f'{chip(c["position_status"], position_kind(c["position_status"]))}' if c["position_id"] else ""
        body.append(f"""<tr>
  <td><code>{e(c['run_id'])}</code><br><span class=muted>{e(c['as_of'])}</span></td>
  <td><b>{e(c['ticker'])}</b>{' ' + chip((c['direction'] or '').upper(), 'long' if c['direction'] == 'long' else 'short') if c['direction'] else ''}</td>
  <td>{e(c['company_verdict']) or '—'}<br><span class=muted>conf {num(c['company_confidence'])}</span></td>
  <td>{e(c['ta_verdict']) or '—'}<br><span class=muted>conf {num(c['ta_confidence'])}</span></td>
  <td>{e(plan)}<br><span class=muted>{e(c['horizon']) or ''}</span></td>
  <td>{chip(decision, decision_kind(c['decision']))}</td>
  <td>{pos}</td>
</tr>""")
    return f"""<div class="tablewrap"><table>
<thead><tr><th>Run</th><th>Ticker</th><th>Company deep dive</th><th>Technical analysis</th>
<th>Plan (entry/stop/target)</th><th>Decision</th><th>Position</th></tr></thead>
<tbody>{''.join(body)}</tbody></table></div>"""


def positions_table(rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "<p class=muted>No positions yet.</p>"
    body = []
    for p in rows:
        body.append(f"""<tr>
  <td><b>{e(p['ticker'])}</b> {chip((p['direction'] or '').upper(), 'long' if p['direction'] == 'long' else 'short')}</td>
  <td>{num(p['entry'])} / {num(p['stop'])} / {num(p['target'])}</td>
  <td>{e(p['opened']) or '—'}</td>
  <td>{chip(p['status'], position_kind(p['status']))}</td>
  <td>{e(p['closed']) or '—'}{f" @ {num(p['exit_price'])}" if p['exit_price'] is not None else ''}</td>
  <td>{p['alert_count']}<span class=muted>{f" (last {e(p['last_alert'])})" if p['last_alert'] else ''}</span></td>
</tr>""")
    return f"""<div class="tablewrap"><table>
<thead><tr><th>Position</th><th>Entry/Stop/Target</th><th>Opened</th><th>Status</th>
<th>Closed</th><th>Alerts</th></tr></thead><tbody>{''.join(body)}</tbody></table></div>"""


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#16181d;--muted:#5f6673;--line:#e3e6eb;--accent:#2f5bea;
--gain:#138a52;--gain-bg:rgba(19,138,82,.14);--loss:#c9362b;--loss-bg:rgba(201,54,43,.13);
--warn:#9a6700;--warn-bg:#fff5d6;--chip:#eef1f5}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a20;--ink:#e8eaee;--muted:#9aa2af;
--line:#2a2f38;--accent:#7c9cff;--gain:#3fcf8e;--gain-bg:rgba(63,207,142,.16);--loss:#ff6b5e;
--loss-bg:rgba(255,107,94,.15);--warn:#f2c14e;--warn-bg:rgba(242,193,78,.12);--chip:#232833}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:26px;margin:0 0 4px}h3{font-size:17px;margin:24px 0 8px}
p{margin:0 0 8px}code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere}
a{color:var(--accent)}.muted{color:var(--muted)}
.banner{border-radius:10px;padding:10px 14px;margin:12px 0;font-size:14px;background:var(--chip)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:16px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.tile .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.tile .v{font-size:26px;font-weight:600}.tile .s{font-size:12.5px;color:var(--muted)}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:14px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:500;white-space:nowrap}
.chip{display:inline-block;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;
padding:2px 7px;border-radius:999px;background:var(--chip);color:var(--muted);white-space:nowrap}
.chip-accept,.chip-open,.chip-long{background:var(--gain-bg);color:var(--gain)}
.chip-reject,.chip-short{background:var(--loss-bg);color:var(--loss)}
.chip-pending{background:var(--warn-bg);color:var(--warn)}
.chip-closed{background:var(--chip);color:var(--muted)}
footer.page{color:var(--muted);font-size:13px;margin-top:24px}
"""


def render(candidates: list[sqlite3.Row], positions: list[sqlite3.Row], runs: int) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trading pipeline dashboard</title><style>{CSS}</style></head>
<body><main>
<h1>Trading pipeline dashboard</h1>
<p class="muted">Every candidate the pipeline has produced, your decisions, and what became of the
positions they opened.</p>
<div class="banner">Decision support only, read from <code>workspace/index.sqlite3</code>
(built by <code>scripts/build_index.py</code> from the run files) — the files stay the record;
this page is a rebuildable view over them.</div>
{summary(candidates, positions, runs)}
<h3>Candidates</h3>
{candidates_table(candidates)}
<h3>Positions</h3>
{positions_table(positions)}
<footer class="page">Rebuild after a run or a decision: <code>python3 scripts/build_index.py &&
python3 scripts/render_dashboard.py</code></footer>
</main></body></html>
"""


def main(argv: list[str]) -> int:
    ws = Path(argv[1]) if len(argv) > 1 else Path("workspace")
    db_path = ws / "index.sqlite3"
    if not db_path.is_file():
        print(f"no index at {db_path} — run scripts/build_index.py first", file=sys.stderr)
        return 2
    conn = sqlite3.connect(db_path)
    candidates = fetch(conn, CANDIDATES_SQL)
    positions = fetch(conn, POSITIONS_SQL)
    runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    conn.close()
    out = ws / "dashboard.html"
    out.write_text(render(candidates, positions, runs))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
