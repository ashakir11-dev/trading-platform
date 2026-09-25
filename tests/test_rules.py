from datetime import datetime, timedelta, timezone

from trading_pipeline.data.base import DataSnapshot
from trading_pipeline.profile import InvestorProfile
from trading_pipeline.rules import check_earnings, check_plan, check_stale_entry, is_material

from .fakes import plan

AS_OF = datetime(2026, 6, 1, 20, tzinfo=timezone.utc)
PROFILE = InvestorProfile()  # moderate: swing + long_term, long only, max loss 10%, R:R >= 2


def outcomes(results):
    return {r.rule: r.outcome for r in results}


def test_good_plan_passes():
    assert set(outcomes(check_plan(plan(), PROFILE)).values()) == {"pass"}


def test_misordered_plans_rejected():
    assert outcomes(check_plan(plan(stop=105), PROFILE)) == {"plan_price_order": "reject"}
    bad_short = plan(entry=100, target=110, stop=95, direction="short")
    assert outcomes(check_plan(bad_short, PROFILE))["plan_price_order"] == "reject"


def test_profile_limits():
    assert outcomes(check_plan(plan(stop=85, target=140), PROFILE))["max_loss"] == "reject"  # 15% stop
    assert outcomes(check_plan(plan(target=115), PROFILE))["reward_to_risk"] == "reject"  # 1.5:1
    short = plan(entry=100, target=80, stop=105, direction="short")
    assert outcomes(check_plan(short, PROFILE))["profile_short"] == "reject"
    assert "profile_short" not in outcomes(check_plan(short, PROFILE.model_copy(update={"allow_short": True})))


def test_horizon_and_timeframe():
    p = plan().model_copy(update={"horizon": "short_term", "chart_timeframe": "1h"})
    assert outcomes(check_plan(p, PROFILE))["profile_horizon"] == "reject"
    wrong_chart = plan().model_copy(update={"chart_timeframe": "1w"})  # swing reads the 1d chart
    assert outcomes(check_plan(wrong_chart, PROFILE))["chart_timeframe"] == "flag"


def test_stale_entry():
    p = plan()  # long, entry 100, stop 90
    assert check_stale_entry(p, 98, 3.0, source="live").outcome == "pass"  # not reached yet: fine
    assert check_stale_entry(p, 102.9, 3.0, source="live").outcome == "pass"
    assert check_stale_entry(p, 104, 3.0, source="live").outcome == "reject"
    assert check_stale_entry(p, 89, 3.0, source="live").outcome == "reject"  # through the stop
    short = plan(entry=100, target=80, stop=105, direction="short")
    assert check_stale_entry(short, 96, 3.0, source="live").outcome == "reject"
    assert check_stale_entry(short, 101, 3.0, source="live").outcome == "pass"
    assert check_stale_entry(p, None, 3.0, source="live").outcome == "flag"


def earnings(when):
    return DataSnapshot(kind="earnings_calendar", source="t", subject="AAA", as_of=AS_OF,
                        payload={"next_earnings_date": when, "confirmed": False})


def test_earnings_flag():
    assert check_earnings(plan(), earnings("2026-06-20"), AS_OF).outcome == "flag"  # 19d, swing window 45d
    assert check_earnings(plan(), earnings("2026-09-01"), AS_OF).outcome == "pass"
    assert check_earnings(plan(), earnings(None), AS_OF).outcome == "pass"
    gap = DataSnapshot(kind="earnings_calendar", source="u", subject="AAA", as_of=AS_OF, is_gap=True)
    assert check_earnings(plan(), gap, AS_OF).outcome == "flag"


def test_news_materiality():
    material = [
        {"headline": "Acme files 8-K", "sec_form": "8-K", "sec_items": ["2.02"]},
        {"headline": "Acme reports Q2 earnings, raises guidance"},
        {"headline": "FDA approves Acme's lead drug"},
        {"headline": "Acme CEO steps down"},
        {"headline": "Anything", "category": "m_and_a"},
    ]
    noise = [
        {"headline": "Acme files 8-K", "sec_form": "8-K", "sec_items": ["7.01"]},
        {"headline": "Why Acme stock is up today"},
        {"headline": "Acme shares are trading higher"},
        {"headline": "Analyst maintains Buy rating on Acme"},
        {"headline": "Acme to present at healthcare conference"},
        {"headline": "Acme earnings beat", "category": "price_action"},
    ]
    assert all(is_material(e)[0] for e in material)
    assert not any(is_material(e)[0] for e in noise)


def test_profile_chart_union():
    charts = {c.interval: (c.role, c.lookback.days) for c in PROFILE.charts()}
    assert charts == {"1d": ("primary", 365), "1w": ("primary", 5 * 365)}
    short = InvestorProfile(horizons=["short_term"])
    assert {c.interval for c in short.charts()} == {"1h", "1d"}
    assert timedelta(days=30) in {c.lookback for c in short.charts()}


def test_example_profile_loads():
    from pathlib import Path

    p = InvestorProfile.load(Path(__file__).parent.parent / "profile.example.json")
    assert p.horizons == ["swing", "long_term"] and p.max_loss_per_trade_pct == 8.0
