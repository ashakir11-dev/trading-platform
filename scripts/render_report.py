#!/usr/bin/env python3
"""Render a run's recommendation report as one self-contained HTML page.

    python3 scripts/render_report.py workspace/runs/<run_id>/report.json

Writes ``report.html`` next to the JSON. The middleware agent writes ``report.json`` at
the end of a run (format in ``prompts/middleware/report.md``), copying values from the
agents' analyses; this script only lays them out. It computes nothing but the plan's
distances (max loss %, gain %, reward:risk, current price vs entry) from the plan's own
numbers, and the chart's moving averages from the agent's own ``raw/`` bars; it has no
opinion: every word on the page comes from the JSON.

The page loads nothing from the network (no fonts, scripts or images), so it opens
offline and leaks nothing about the run. Standard library only.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from html import escape
from pathlib import Path
from typing import Any

STATUS_ORDER = ("verified", "unverified", "contradicted")
BUCKET_ORDER = ["core", "growth", "speculative"]
ROOT = Path(__file__).resolve().parents[1]


def _load_price_stats():
    spec = importlib.util.spec_from_file_location("price_stats", ROOT / ".claude" / "hooks" / "price_stats.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("price_stats", mod)
    spec.loader.exec_module(mod)
    return mod


def e(value: Any) -> str:
    return escape("" if value is None else str(value))


def num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def price(value: Any) -> str:
    v = num(value)
    return "—" if v is None else f"{v:,.2f}"


def pct(value: float | None, signed: bool = False) -> str:
    if value is None:
        return "—"
    return f"{value:+.1f}%" if signed else f"{value:.1f}%"


def targets_of(rec: dict[str, Any]) -> list[tuple[float, float | None]]:
    """[(price, fraction)] nearest first; a single ``target`` counts as one full target."""
    out = []
    for t in rec.get("targets") or []:
        p = num((t or {}).get("price"))
        if p is not None:
            out.append((p, num(t.get("fraction"))))
    if not out and num(rec.get("target")) is not None:
        out.append((num(rec.get("target")), 1.0))
    return out


# --------------------------------------------------------------------------------------
# Plan arithmetic (the only computation on the page)
# --------------------------------------------------------------------------------------


def plan_metrics(rec: dict[str, Any]) -> dict[str, float | None]:
    entry, stop, target = num(rec.get("entry")), num(rec.get("stop")), num(rec.get("target"))
    cur = num((rec.get("current_price") or {}).get("price"))
    out: dict[str, float | None] = {"risk_pct": None, "reward_pct": None, "rr": None, "vs_entry_pct": None}
    if entry:
        if stop is not None:
            out["risk_pct"] = abs(entry - stop) / entry * 100
        if target is not None:
            out["reward_pct"] = abs(target - entry) / entry * 100
        if cur is not None:
            out["vs_entry_pct"] = (cur - entry) / entry * 100
    if entry is not None and stop is not None and target is not None and entry != stop:
        out["rr"] = abs(target - entry) / abs(entry - stop)
    return out


# --------------------------------------------------------------------------------------
# Pieces
# --------------------------------------------------------------------------------------


def ladder_svg(rec: dict[str, Any]) -> str:
    """A vertical price ladder: targets, entry, stop (and the current price) to scale."""
    entry, stop = num(rec.get("entry")), num(rec.get("stop"))
    targets = targets_of(rec)
    if entry is None or stop is None or not targets:
        return ""
    cur = num((rec.get("current_price") or {}).get("price"))
    levels = [entry, stop] + [p for p, _ in targets] + ([cur] if cur is not None else [])
    hi, lo = max(levels), min(levels)
    span = (hi - lo) or 1.0
    top, bottom, width = 14.0, 206.0, 240

    def y(v: float) -> float:
        return top + (hi - v) / span * (bottom - top)

    ye, ys = y(entry), y(stop)
    far = targets[-1][0]
    parts = [
        f'<svg class="ladder" viewBox="0 0 {width} 220" role="img" '
        f'aria-label="Price plan: stop {price(stop)}, entry {price(entry)}, '
        f'targets {", ".join(price(p) for p, _ in targets)}">',
        f'<rect class="zone-gain" x="56" y="{min(ye, y(far)):.1f}" width="40" height="{abs(y(far) - ye):.1f}" rx="3"/>',
        f'<rect class="zone-loss" x="56" y="{min(ye, ys):.1f}" width="40" height="{abs(ys - ye):.1f}" rx="3"/>',
    ]
    marks = [("entry", entry, ye, "ENTRY", ""), ("stop", stop, ys, "STOP", "")]
    for i, (p, frac) in enumerate(targets):
        label = f"T{i + 1}" if len(targets) > 1 else "TARGET"
        suffix = f" ({frac * 100:.0f}%)" if frac is not None and len(targets) > 1 else ""
        marks.append(("target", p, y(p), label, suffix))
    if cur is not None:
        marks.append(("now", cur, y(cur), "NOW", ""))
    placed: list[float] = []
    for name, value, yy, label, suffix in sorted(marks, key=lambda m: m[2]):
        ly = yy
        for p in placed:
            if abs(ly - p) < 15:
                ly = p + 15
        placed.append(ly)
        cls = f"mark-{name}"
        if name == "now":
            parts.append(f'<circle class="{cls}" cx="76" cy="{yy:.1f}" r="4.5"/>')
        else:
            parts.append(f'<line class="{cls}" x1="48" x2="104" y1="{yy:.1f}" y2="{yy:.1f}"/>')
        parts.append(f'<text class="lbl {cls}" x="112" y="{ly + 4:.1f}">{e(label)} {price(value)}{e(suffix)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _bars_from_file(path: str | None):
    """Daily bars from a saved ``GetStockPrices`` response (raw/NNN-GetStockPrices.json)."""
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        response = data.get("response", data) if isinstance(data, dict) else data
        if isinstance(response, list):
            text = "\n".join(b.get("text", "") for b in response if isinstance(b, dict))
        else:
            text = str(response)
        _, bars = _load_price_stats().parse(text)
    except (OSError, ValueError, json.JSONDecodeError, AttributeError):
        return None
    return bars


def chart_svg(rec: dict[str, Any]) -> str:
    """Candlesticks of the plan's primary timeframe with SMA20/50 and the plan's levels.

    Drawn only from the technical agent's own raw bars (``chart.bars``); nothing is
    fetched. Empty string when the file is missing or unreadable."""
    chart = rec.get("chart") or {}
    bars = _bars_from_file(chart.get("bars"))
    if not bars:
        return ""
    ps = _load_price_stats()
    weekly = str(chart.get("timeframe") or "1d") == "1w"
    series = ps.weekly(bars) if weekly else bars
    closes_all = [b.close for b in series]

    def sma(n: int) -> list[float | None]:
        return [sum(closes_all[i - n + 1:i + 1]) / n if i >= n - 1 else None for i in range(len(closes_all))]

    sma20, sma50 = sma(20), sma(50)
    shown = 104 if weekly else 130
    view = series[-shown:]
    off = len(series) - len(view)
    entry, stop = num(rec.get("entry")), num(rec.get("stop"))
    levels = [(p, "target") for p, _ in targets_of(rec)]
    if entry is not None:
        levels.append((entry, "entry"))
    if stop is not None:
        levels.append((stop, "stop"))
    hi = max([b.high for b in view] + [p for p, _ in levels])
    lo = min([b.low for b in view] + [p for p, _ in levels])
    span = (hi - lo) or 1.0
    W, H, L, R, T, B = 720, 260, 8, 118, 10, 236

    def x(i: int) -> float:
        return L + (i + 0.5) * (W - L - R) / len(view)

    def y(v: float) -> float:
        return T + (hi - v) / span * (B - T)

    cw = max(1.0, (W - L - R) / len(view) * 0.6)
    parts = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="'
             f'{"Weekly" if weekly else "Daily"} bars {view[0].day} to {view[-1].day} with the plan levels">']
    for i, b in enumerate(view):
        up = b.close >= b.open
        parts.append(f'<line class="wick" x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{y(b.high):.1f}" y2="{y(b.low):.1f}"/>')
        top, bot = y(max(b.open, b.close)), y(min(b.open, b.close))
        parts.append(f'<rect class="{"c-up" if up else "c-dn"}" x="{x(i) - cw / 2:.1f}" y="{top:.1f}" '
                     f'width="{cw:.1f}" height="{max(bot - top, 1.0):.1f}"/>')
    for name, values in (("sma20", sma20), ("sma50", sma50)):
        pts = [f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(values[off:]) if v is not None]
        if len(pts) > 1:
            parts.append(f'<polyline class="{name}" points="{" ".join(pts)}"/>')
    ti = 0
    for v, name in sorted(levels, key=lambda l: -l[0]):
        yy = y(v)
        parts.append(f'<line class="lvl mark-{name}" x1="{L}" x2="{W - R}" y1="{yy:.1f}" y2="{yy:.1f}"/>')
        label = name.upper()
        if name == "target" and len([1 for _, n in levels if n == "target"]) > 1:
            ti += 1
            label = f"T{len([1 for _, n in levels if n == 'target']) - ti + 1}"
        parts.append(f'<text class="lbl mark-{name}" x="{W - R + 4}" y="{yy + 4:.1f}">{label} {price(v)}</text>')
    parts.append(f'<text class="axis" x="{L}" y="{H - 2}">{view[0].day}</text>')
    parts.append(f'<text class="axis end" x="{W - R}" y="{H - 2}">{view[-1].day}</text>')
    parts.append("</svg>")
    legend = ('<p class="muted legend"><span class="sw sma20"></span>SMA20 <span class="sw sma50"></span>SMA50 · '
              f'{"weekly" if weekly else "daily"} bars from <code>{e(chart.get("bars"))}</code></p>')
    return "".join(parts) + legend


def chip(text: str, kind: str) -> str:
    return f'<span class="chip chip-{e(kind)}">{e(text)}</span>'


def confidence_bar(label: str, value: Any) -> str:
    v = num(value)
    if v is None:
        return ""
    v = max(0.0, min(1.0, v))
    return (f'<div class="conf"><span>{e(label)}</span>'
            f'<span class="bar"><span style="width:{v * 100:.0f}%"></span></span>'
            f'<b>{v:.2f}</b></div>')


def _targets_text(rec: dict[str, Any]) -> str:
    targets = targets_of(rec)
    if len(targets) <= 1:
        return price(rec.get("target"))
    return " / ".join(f"{price(p)}" + (f" ({frac * 100:.0f}%)" if frac is not None else "") for p, frac in targets)


def rec_card(rec: dict[str, Any], profile: dict[str, Any], open_: bool = True) -> str:
    m = plan_metrics(rec)
    direction = (rec.get("direction") or "").lower()
    bucket = rec.get("risk_bucket")
    bp = (profile.get("buckets") or {}).get(bucket) or {}
    max_loss = num(bp.get("max_loss_per_trade_pct"))
    min_rr = num(bp.get("min_reward_to_risk"))
    size = num(rec.get("position_size_pct") if rec.get("position_size_pct") is not None else bp.get("position_size_pct"))
    cur = rec.get("current_price") or {}
    flags = rec.get("flags") or []

    tiles = [
        ("Entry", price(rec.get("entry")), e(rec.get("entry_valid_until")) and f"valid until {e(rec.get('entry_valid_until'))}"),
        ("Stop", price(rec.get("stop")), f"−{pct(m['risk_pct'])} max loss"
         + (f" (limit {max_loss:g}%)" if max_loss is not None else "")),
        ("Target" + ("s" if len(targets_of(rec)) > 1 else ""), _targets_text(rec),
         f"+{pct(m['reward_pct'])} potential" + (" (size-weighted)" if len(targets_of(rec)) > 1 else "")),
        ("Reward : risk", "—" if m["rr"] is None else f"{m['rr']:.2f}",
         f"minimum {min_rr:g}" if min_rr is not None else ""),
    ]
    if size is not None:
        tiles.append(("Position size", f"{size:g}%", "of account, from the bucket's profile"))
    tiles_html = "".join(f'<div class="tile"><div class="k">{e(k)}</div><div class="v">{e(v)}</div>'
                         f'<div class="s">{e(s)}</div></div>' for k, v, s in tiles)

    now = ""
    if cur.get("price") is not None:
        now = (f'<p class="now">Price now {price(cur.get("price"))} '
               f'({pct(m["vs_entry_pct"], signed=True)} vs entry) · {e(cur.get("source"))}'
               + (f' · {e(cur.get("at"))}' if cur.get("at") else "") + "</p>")

    catalysts = sorted(rec.get("catalysts") or [],
                       key=lambda c: STATUS_ORDER.index(c.get("status")) if c.get("status") in STATUS_ORDER else 9)
    cat_html = "".join(f'<li>{chip(c.get("status", "?"), c.get("status", "unknown"))} {e(c.get("catalyst"))}</li>'
                       for c in catalysts) or "<li class=muted>None cited.</li>"

    flags_html = ""
    if flags:
        flags_html = '<div class="flags"><b>Watch out</b><ul>' + "".join(
            f'<li><code>{e(f.get("rule"))}</code> {e(f.get("detail"))}</li>' for f in flags) + "</ul></div>"

    risks = rec.get("key_risks") or []
    risks_html = ("<h4>Key risks</h4><ul>" + "".join(f"<li>{e(r)}</li>" for r in risks) + "</ul>") if risks else ""

    earnings = rec.get("next_earnings")
    earnings_html = ""
    if earnings:
        confirmed = rec.get("next_earnings_confirmed")
        earnings_html = (f'<p class="muted">Next earnings: {e(earnings)}'
                         + ("" if confirmed is None else (" (confirmed)" if confirmed else " (estimated)")) + "</p>")

    conf = rec.get("confidence") or {}
    files = rec.get("files") or {}
    files_html = "".join(f"<li><code>{e(v)}</code> <span class=muted>({e(k)})</span></li>" for k, v in files.items())
    pick = num(rec.get("pick_score"))
    meta_bits = [e(rec.get("sector")), f"{e(rec.get('horizon'))} horizon" if rec.get("horizon") else "",
                 f"pick score {pick:.2f}" if pick is not None else "",
                 f"{e(bp.get('entry_style'))} entry" if bp.get("entry_style") else ""]
    meta = " · ".join(b for b in meta_bits if b)

    rr_text = "—" if m["rr"] is None else f"{m['rr']:.2f}"
    flags_text = f" · {len(flags)} flag{'s' if len(flags) != 1 else ''}" if flags else ""
    summary_stats = (f'<span class="sum-plan">{price(rec.get("entry"))} → {_targets_text(rec)} · stop {price(rec.get("stop"))}</span>'
                     f'<span class="sum-kpi"><b class="loss">−{pct(m["risk_pct"])}</b> '
                     f'<b class="gain">+{pct(m["reward_pct"])}</b> R:R {rr_text}{flags_text}</span>')

    return f"""
<details class="card" id="{e(rec.get('ticker'))}"{' open' if open_ else ''}>
  <summary class="card-head">
    <div class="sum-title">
      <h2>{e(rec.get('ticker'))} <span class="company">{e(rec.get('company'))}</span></h2>
      <p class="muted">{meta}{' · ' if meta else ''}<code>{e(rec.get('candidate_id'))}</code></p>
    </div>
    <div class="sum-mid">{summary_stats}</div>
    <div class="sum-chips">{chip(direction.upper() or '?', 'long' if direction == 'long' else 'short')}
    {chip(bucket, f'bucket-{bucket}') if bucket else ''}</div>
  </summary>
  <div class="card-body">
  <div class="plan">
    <div class="tiles">{tiles_html}</div>
    {ladder_svg(rec)}
  </div>
  {now}
  {chart_svg(rec)}
  <dl class="conds">
    <dt>Enter when</dt><dd>{e(rec.get('entry_condition')) or '—'}</dd>
    <dt>Plan is wrong if</dt><dd>{e(rec.get('invalidation')) or '—'}</dd>
  </dl>
  {flags_html}
  <div class="cols">
    <section>
      <h4>Why (company deep dive)</h4>
      <p>{e(rec.get('thesis'))}</p>
      <h4>Chart (technical analysis)</h4>
      <p>{e(rec.get('setup'))}</p>
      {earnings_html}
    </section>
    <section>
      <h4>Catalysts</h4>
      <ul class="cats">{cat_html}</ul>
      {risks_html}
      <h4>Agent confidence</h4>
      {confidence_bar('Company deep dive', conf.get('company_deep_dive'))}
      {confidence_bar('Technical analysis', conf.get('technical_analysis'))}
    </section>
  </div>
  <footer class="card-foot">
    <div class="decide"><code>/decide {e(rec.get('candidate_id'))} accept|reject [note]</code></div>
    {f'<details><summary>Analysis files</summary><ul>{files_html}</ul></details>' if files_html else ''}
  </footer>
  </div>
</details>"""


def funnel(data: dict[str, Any]) -> str:
    f = data.get("funnel") or {}
    steps = [("Sectors called", f.get("sectors_called")), ("Sectors pursued", f.get("sectors_pursued")),
             ("Companies screened", f.get("companies_screened")), ("Candidates", f.get("candidates")),
             ("Passed fundamentals", f.get("passed_company")), ("Passed every filter", f.get("eligible")),
             ("Recommended", f.get("recommended"))]
    steps = [(k, v) for k, v in steps if v is not None]
    if not steps:
        return ""
    return '<ol class="funnel">' + "".join(f"<li><b>{e(v)}</b><span>{e(k)}</span></li>" for k, v in steps) + "</ol>"


def market(data: dict[str, Any]) -> str:
    mk = data.get("market") or {}
    if not mk:
        return ""
    rows = "".join(
        f"<tr><td>{e(s.get('sector'))}</td><td>{chip(s.get('direction', ''), 'long' if s.get('direction') == 'upside' else 'short')}</td>"
        f"<td>{price(s.get('confidence'))}</td><td>{'yes' if s.get('pursued') else 'no'}</td>"
        f"<td class=muted>{e(s.get('note'))}</td></tr>"
        for s in mk.get("sectors") or [])
    table = ("<div class=\"tablewrap\"><table><thead><tr><th>Sector</th><th>Call</th><th>Confidence</th><th>Pursued</th><th></th></tr></thead>"
             f"<tbody>{rows}</tbody></table></div>") if rows else ""
    return f'<section class="block"><h3>Market backdrop</h3><p>{e(mk.get("summary"))}</p>{table}</section>'


def listing(title: str, items: list[Any], cls: str = "") -> str:
    if not items:
        return ""
    lis = []
    for it in items:
        if isinstance(it, dict):
            lis.append(f"<li><b>{e(it.get('subject'))}</b> <span class=muted>{e(it.get('stage'))}</span> — {e(it.get('reason'))}</li>")
        else:
            lis.append(f"<li>{e(it)}</li>")
    return f'<section class="block {cls}"><h3>{e(title)}</h3><ul>{"".join(lis)}</ul></section>'


def _by_bucket(recs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(recs, key=lambda r: BUCKET_ORDER.index(r["risk_bucket"])
                  if r.get("risk_bucket") in BUCKET_ORDER else len(BUCKET_ORDER))


# --------------------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------------------


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#16181d;--muted:#5f6673;--line:#e3e6eb;--accent:#2f5bea;
--gain:#138a52;--gain-bg:rgba(19,138,82,.14);--loss:#c9362b;--loss-bg:rgba(201,54,43,.13);
--warn:#9a6700;--warn-bg:#fff5d6;--chip:#eef1f5;--sma20:#2f5bea;--sma50:#b0662a}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a20;--ink:#e8eaee;--muted:#9aa2af;
--line:#2a2f38;--accent:#7c9cff;--gain:#3fcf8e;--gain-bg:rgba(63,207,142,.16);--loss:#ff6b5e;
--loss-bg:rgba(255,107,94,.15);--warn:#f2c14e;--warn-bg:rgba(242,193,78,.12);--chip:#232833;--sma20:#7c9cff;--sma50:#e0a060}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:22px;margin:0}h3{font-size:17px;margin:0 0 8px}
h4{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:16px 0 6px}
p{margin:0 0 8px}code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere}
h1,h2{overflow-wrap:anywhere}
a{color:var(--accent)}.muted{color:var(--muted)}.company{font-weight:400;color:var(--muted);font-size:17px}
.banner{border-radius:10px;padding:10px 14px;margin:12px 0;font-size:14px}
.banner.info{background:var(--chip)}.banner.warn{background:var(--warn-bg);color:var(--warn)}
.headline{font-size:18px;margin:16px 0}
.funnel{display:flex;flex-wrap:wrap;gap:6px;list-style:none;padding:0;margin:16px 0}
.funnel li{flex:1 1 100px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.funnel b{display:block;font-size:22px}.funnel span{font-size:12.5px;color:var(--muted)}
.card,.block{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:0 20px 0;margin:16px 0}
.block{padding:20px}
.card>summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px 0;flex-wrap:wrap}
.card>summary::-webkit-details-marker{display:none}
.card>summary::before{content:"▸";color:var(--muted);font-size:14px;margin-right:2px}
.card[open]>summary::before{content:"▾"}
.sum-title{flex:1 1 260px;min-width:0}.sum-mid{flex:1 1 240px;font-size:14px;display:flex;flex-direction:column;gap:2px}
.sum-plan{font-variant-numeric:tabular-nums}.sum-kpi{color:var(--muted)}.sum-kpi .gain{color:var(--gain)}.sum-kpi .loss{color:var(--loss)}
.sum-chips{display:flex;gap:6px;flex-wrap:wrap}
.card-body{padding:0 0 20px;border-top:1px solid var(--line)}
.group-title{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:24px 0 -8px}
.also .card>summary{padding:12px 0}.also .card{margin:8px 0}
.plan{display:flex;gap:16px;align-items:center;margin-top:14px;flex-wrap:wrap}
.tiles{flex:1 1 280px;min-width:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}
.tile{border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.tile .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.tile .v{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}.tile .s{font-size:12.5px;color:var(--muted)}
.ladder{flex:0 0 240px;width:240px;height:220px}
.chart{width:100%;height:auto;display:block;margin-top:12px;background:var(--bg);border:1px solid var(--line);border-radius:10px}
.chart .wick{stroke:var(--muted);stroke-width:1}.chart .c-up{fill:var(--gain)}.chart .c-dn{fill:var(--loss)}
.chart .sma20{fill:none;stroke:var(--sma20);stroke-width:1.5}.chart .sma50{fill:none;stroke:var(--sma50);stroke-width:1.5}
.chart .lvl{stroke-width:1.5;stroke-dasharray:6 4}.chart .axis{font:11px ui-monospace,Menlo,monospace;fill:var(--muted)}
.chart .axis.end{text-anchor:end}
.legend{font-size:12.5px;margin-top:4px}.sw{display:inline-block;width:14px;height:3px;vertical-align:middle;margin:0 4px 0 6px}
.sw.sma20{background:var(--sma20)}.sw.sma50{background:var(--sma50)}
.zone-gain{fill:var(--gain-bg)}.zone-loss{fill:var(--loss-bg)}
line.mark-target{stroke:var(--gain);stroke-width:2.5}line.mark-stop{stroke:var(--loss);stroke-width:2.5}
line.mark-entry{stroke:var(--ink);stroke-width:2.5}circle.mark-now{fill:var(--accent)}
.lbl{font:600 12px ui-monospace,Menlo,monospace;fill:var(--muted)}
text.mark-target{fill:var(--gain)}text.mark-stop{fill:var(--loss)}text.mark-entry{fill:var(--ink)}text.mark-now{fill:var(--accent)}
.now{font-size:14px;color:var(--muted);margin-top:8px}
.conds{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;margin:12px 0}
.conds dt{color:var(--muted);font-size:14px}.conds dd{margin:0}
.flags{background:var(--warn-bg);color:var(--warn);border-radius:10px;padding:10px 14px;margin:12px 0}
.flags ul{margin:4px 0 0;padding-left:18px}.flags code{color:inherit}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}
@media (max-width:720px){.cols{grid-template-columns:1fr}.conds{grid-template-columns:1fr}.conds dd{margin-bottom:6px}}
.cols>section{min-width:0}.tablewrap{overflow-x:auto}
ul{padding-left:18px;margin:0}.cats{list-style:none;padding:0}.cats li{margin:4px 0}
.chip{display:inline-block;font-size:11.5px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;
padding:2px 8px;border-radius:999px;background:var(--chip);color:var(--muted);white-space:nowrap}
.chip-long,.chip-verified{background:var(--gain-bg);color:var(--gain)}
.chip-short,.chip-contradicted{background:var(--loss-bg);color:var(--loss)}
.chip-unverified{background:var(--warn-bg);color:var(--warn)}
.chip-bucket-core{background:var(--gain-bg);color:var(--gain)}
.chip-bucket-growth{background:var(--warn-bg);color:var(--warn)}
.chip-bucket-speculative{background:var(--loss-bg);color:var(--loss)}
.conf{display:grid;grid-template-columns:140px 1fr 40px;align-items:center;gap:8px;font-size:13.5px;margin:4px 0}
.bar{height:6px;background:var(--chip);border-radius:3px;overflow:hidden}.bar span{display:block;height:100%;background:var(--accent)}
.card-foot{border-top:1px solid var(--line);margin-top:16px;padding-top:12px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.decide code{background:var(--chip);padding:4px 8px;border-radius:6px}
details summary{cursor:pointer;color:var(--muted);font-size:13.5px}
table{width:100%;border-collapse:collapse;font-size:14px;margin-top:8px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:500}
.errors{border-color:var(--loss)}
footer.page{color:var(--muted);font-size:13px;margin-top:24px}
"""


def render(data: dict[str, Any]) -> str:
    recs = _by_bucket(data.get("recommendations") or [])
    also = _by_bucket(data.get("also_passed") or [])
    profile = data.get("profile") or {}
    bt = data.get("backtest")
    title = f"{'Backtest' if bt else 'Pipeline'} run {data.get('run_id', '')}"

    meta = " · ".join(x for x in [
        f"As of {e(data.get('as_of'))}",
        f"profile {e(profile.get('name'))}" if profile.get("name") else "",
        f"prompt {e(data.get('prompt_commit'))}" if data.get("prompt_commit") else "",
    ] if x)

    banners = []
    if bt:
        limits = "; ".join(e(x) for x in bt.get("limits") or [])
        banners.append(f'<div class="banner warn"><b>BACKTEST as of {e(data.get("as_of"))}</b> · '
                       f'point in time: {e(bt.get("point_in_time"))}' + (f" · {limits}" if limits else "") + "</div>")
    banners.append('<div class="banner info">Decision support with paper-trading execution: '
                   "you make every call, <code>/decide accept</code> records it and places the sized paper "
                   "entry order; nothing here touches a live account.</div>")

    if recs:
        headline = (f"{len(recs)} recommendation{'s' if len(recs) != 1 else ''} "
                    f"(at most one per bucket): "
                    + ", ".join(f'<a href="#{e(r.get("ticker"))}">{e(r.get("ticker"))}</a> '
                                f'({e(r.get("risk_bucket"))}, {e((r.get("direction") or "").lower())})' for r in recs)
                    + (f" · {len(also)} more passed every filter, tracked below" if also else ""))
        cards = "".join(rec_card(r, profile, open_=True) for r in recs)
    else:
        headline = "No recommendations this run." + (f" {len(also)} candidates passed every filter, tracked below." if also else "")
        cards = f'<section class="block"><p>{e(data.get("no_recommendation_reason"))}</p></section>' \
            if data.get("no_recommendation_reason") else ""
    also_html = ""
    if also:
        also_html = ('<p class="group-title">Also passed every filter — not the bucket\'s pick, tracked for the '
                     'evaluator</p><div class="also">' + "".join(rec_card(r, profile, open_=False) for r in also) + "</div>")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><style>{CSS}</style></head>
<body><main>
<h1>{e(title)}</h1>
<p class="muted">{meta}</p>
{''.join(banners)}
<p class="headline">{headline}</p>
{funnel(data)}
{cards}
{also_html}
{market(data)}
{listing('Not pursued or rejected', data.get('not_pursued') or [])}
{listing('Conflicts', data.get('conflicts') or [])}
{listing('Data gaps that mattered', data.get('data_gaps') or [])}
{listing('Errors', data.get('errors') or [], 'errors')}
<footer class="page">Full report: <code>workspace/runs/{e(data.get('run_id'))}/report.md</code> ·
every figure comes from the agents' analyses; their raw data is in each analysis folder's <code>raw/</code>.</footer>
</main></body></html>
"""


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: render_report.py workspace/runs/<run_id>/report.json", file=sys.stderr)
        return 2
    src = Path(argv[1])
    if "decisions" in src.resolve().parts:
        print("refusing to render from workspace/decisions/", file=sys.stderr)
        return 2
    data = json.loads(src.read_text())
    out = src.with_name("report.html")
    out.write_text(render(data))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
