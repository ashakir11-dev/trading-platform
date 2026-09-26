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
