"""Tests for scripts/render_report.py (the report.html showcase page)."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("render_report", ROOT / "scripts" / "render_report.py")
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)


def example() -> dict:
    """The report.json example documented in prompts/middleware/report.md."""
    text = (ROOT / "prompts" / "middleware" / "report.md").read_text()
    return json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))


def test_documented_example_renders():
    html = rr.render(example())
    assert html.startswith("<!doctype html>")
    assert "XOM" in html and "Exxon Mobil Corp" in html
    assert "/decide 20260925T213314Z-XOM accept|reject" in html
    assert "upcoming_earnings" in html
    assert "<svg" in html


def test_plan_metrics_long_and_short():
    long = rr.plan_metrics({"entry": 118.40, "stop": 111.00, "target": 134.00,
                            "current_price": {"price": 117.10}})
    assert long["risk_pct"] == pytest.approx(6.25, abs=0.01)
    assert long["reward_pct"] == pytest.approx(13.18, abs=0.01)
    assert long["rr"] == pytest.approx(15.6 / 7.4)
    assert long["vs_entry_pct"] == pytest.approx(-1.10, abs=0.01)
    short = rr.plan_metrics({"entry": 250, "stop": 265, "target": 215})
    assert short["risk_pct"] == pytest.approx(6.0)
    assert short["rr"] == pytest.approx(35 / 15)
    assert short["vs_entry_pct"] is None


def test_missing_numbers_do_not_crash():
    assert rr.plan_metrics({"entry": None, "stop": 1, "target": 2})["rr"] is None
    assert rr.plan_metrics({"entry": 10, "stop": 10, "target": 12})["rr"] is None
    assert rr.ladder_svg({"entry": 10}) == ""
    rr.render({"recommendations": [{"ticker": "X"}]})


def test_agent_text_is_escaped():
    data = example()
    data["recommendations"][0]["thesis"] = "<script>alert(1)</script>"
    html = rr.render(data)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_no_recommendations_shows_reason():
    data = example()
    data["recommendations"] = []
    data["no_recommendation_reason"] = "None: every candidate failed reward_to_risk."
    html = rr.render(data)
    assert "No recommendations this run." in html
    assert "every candidate failed reward_to_risk" in html


def test_backtest_banner():
    data = example()
    data["backtest"] = {"point_in_time": "audited", "limits": ["price levels split-adjusted to today"]}
    html = rr.render(data)
    assert "BACKTEST as of 2026-09-25T21:33:14Z" in html
    assert "split-adjusted" in html


def test_page_loads_nothing_from_the_network():
    html = rr.render(example())
    assert not re.search(r"""(src|href)\s*=\s*["']?(https?:)?//""", html)
    assert "@import" not in html and "url(" not in html


def test_cards_are_collapsible_and_recommendations_open():
    html = rr.render(example())
    assert '<details class="card" id="XOM" open>' in html
    assert "<summary" in html and "341" not in html  # no stray numbers
    assert "at most one per bucket" in html


def test_multiple_targets_show_in_ladder_and_tiles():
    data = example()
    rec = data["recommendations"][0]
    assert rec["targets"] and len(rec["targets"]) == 2
    html = rr.render(data)
    assert "T1 128.00" in html and "T2 140.00" in html          # ladder labels
    assert "128.00 (50%) / 140.00 (50%)" in html                 # tile text
    assert "size-weighted" in html
    # a plain single target still renders as before
    del rec["targets"]
    html = rr.render(data)
    assert "TARGET 134.00" in html and "T1 128.00" not in html


def test_also_passed_listed_collapsed_after_recommendations():
    data = example()
    extra = dict(data["recommendations"][0], ticker="CVX", candidate_id="20260925T213314Z-CVX", pick_score=0.3)
    data["also_passed"] = [extra]
    html = rr.render(data)
    assert '<details class="card" id="CVX">' in html              # not open
    assert html.index('id="XOM"') < html.index("Also passed every filter") < html.index('id="CVX"')
    assert "1 more passed every filter" in html


def _bars_json(path, n=60):
    from datetime import date, timedelta
    rows, d, c = [], date(2026, 1, 5), 100.0
    for i in range(n):
        while d.weekday() >= 5:
            d += timedelta(days=1)
        c += 0.5
        rows.append(f"| {d} | {c - 0.2:.2f} | {c + 1:.2f} | {c - 1:.2f} | {c:.2f} | 1,000 |")
        d += timedelta(days=1)
    text = ("Daily prices for XOM (Exxon):\n\n| Date | Open | High | Low | Close | Volume |\n|---|---|---|---|---|---|\n"
            + "\n".join(rows))
    path.write_text(json.dumps({"tool": "GetStockPrices", "response": [{"type": "text", "text": text}]}))


def test_chart_is_drawn_from_raw_bars_and_skipped_when_missing(tmp_path):
    data = example()
    rec = data["recommendations"][0]
    rec["chart"] = {"bars": str(tmp_path / "missing.json"), "timeframe": "1d"}
    assert '<svg class="chart"' not in rr.render(data)
    raw = tmp_path / "006-GetStockPrices.json"
    _bars_json(raw)
    rec["chart"] = {"bars": str(raw), "timeframe": "1d"}
    html = rr.render(data)
    assert '<svg class="chart"' in html and 'class="sma20"' in html and 'class="sma50"' in html
    assert "ENTRY 118.40" in html and "STOP 111.00" in html and "T1 128.00" in html
    rec["chart"]["timeframe"] = "1w"
    assert "Weekly bars" in rr.render(data)
    rr.render({"recommendations": [{"ticker": "X", "chart": {"bars": str(tmp_path / "x.json")}}]})  # no crash


def test_main_writes_report_html(tmp_path):
    src = tmp_path / "report.json"
    src.write_text(json.dumps(example()))
    assert rr.main(["render_report.py", str(src)]) == 0
    assert "XOM" in (tmp_path / "report.html").read_text()


def test_main_refuses_decisions(tmp_path):
    src = tmp_path / "decisions" / "report.json"
    src.parent.mkdir()
    src.write_text(json.dumps(example()))
    assert rr.main(["render_report.py", str(src)]) == 2
    assert not (src.parent / "report.html").exists()
