"""Deterministic rules: mechanical checks that sit beside the LLM agents.

Rules never make judgment calls; they catch mechanical errors, enforce the investor
profile's limits and warn about known risks. Every result is a ``RuleResult`` that is
logged on the stage record, so the process-review agent can tell a rule veto from a
judgment failure.

* ``reject`` removes the candidate.
* ``flag`` keeps it but warns the user in the report.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from .data.base import DataSnapshot, PriceBar
from .profile import HORIZONS, InvestorProfile
from .schemas import RuleResult, TradePlan


def _r(rule: str, outcome: str, message: str) -> RuleResult:
    return RuleResult(rule=rule, outcome=outcome, message=message)


# --------------------------------------------------------------------------------------
# Trade plan vs investor profile
# --------------------------------------------------------------------------------------


def check_plan(plan: TradePlan, profile: InvestorProfile) -> list[RuleResult]:
    """Price ordering, profile horizon/direction, max loss and minimum reward:risk."""
    out: list[RuleResult] = []
    long = plan.direction == "long"
    e, s, t = plan.entry_price, plan.stop_loss, plan.target_price

    ordered = (s < e < t) if long else (t < e < s)
    if not ordered:
        want = "stop < entry < target" if long else "target < entry < stop"
        out.append(_r("plan_price_order", "reject",
                      f"{plan.direction} plan needs {want}; got stop {s}, entry {e}, target {t}"))
        return out  # the ratios below are meaningless for a mis-ordered plan
    out.append(_r("plan_price_order", "pass", "stop, entry and target are correctly ordered"))

    if plan.horizon not in profile.horizons:
        out.append(_r("profile_horizon", "reject",
                      f"horizon {plan.horizon} is not one the investor trades ({', '.join(profile.horizons)})"))
    else:
        primary = next(c.interval for c in HORIZONS[plan.horizon].charts if c.role == "primary")
        if plan.chart_timeframe != primary:
            out.append(_r("chart_timeframe", "flag",
                          f"{plan.horizon} plans should be read from the {primary} chart; plan used {plan.chart_timeframe}"))

    if not long and not profile.allow_short:
        out.append(_r("profile_short", "reject", "investor profile does not allow short positions"))

    risk_pct = abs(e - s) / e * 100
    if risk_pct > profile.max_loss_per_trade_pct:
        out.append(_r("max_loss", "reject",
                      f"stop is {risk_pct:.1f}% from entry; profile allows at most {profile.max_loss_per_trade_pct}%"))

    rr = abs(t - e) / abs(e - s)
    if rr < profile.min_reward_to_risk:
        out.append(_r("reward_to_risk", "reject",
                      f"reward:risk is {rr:.2f}; profile requires at least {profile.min_reward_to_risk}"))
    return out


# --------------------------------------------------------------------------------------
# Stop / target hits (shared by Agent 5 alerts and the outcomes agent)
# --------------------------------------------------------------------------------------


def levels_hit(plan: TradePlan, bar: PriceBar, trigger: str) -> tuple[bool, bool]:
    """(stop_hit, target_hit) for one bar, per the profile's ``level_trigger``."""
    long = plan.direction == "long"
    if trigger == "intraday":
        adverse, favorable = (bar.low, bar.high) if long else (bar.high, bar.low)
    else:
        adverse = favorable = bar.close
    stop = adverse <= plan.stop_loss if long else adverse >= plan.stop_loss
    target = favorable >= plan.target_price if long else favorable <= plan.target_price
    return stop, target


# --------------------------------------------------------------------------------------
# Stale entry
# --------------------------------------------------------------------------------------


def check_stale_entry(plan: TradePlan, price: float | None, max_drift_pct: float, *, source: str) -> RuleResult:
    """Reject if price already ran past the entry by more than max_drift_pct, or is through the stop.

    A price that has not reached the entry yet is fine (the entry may be a breakout level).
    """
    if price is None:
        return _r("stale_entry", "flag", "no current price available to check whether the entry is stale")
    long = plan.direction == "long"
    if (price <= plan.stop_loss) if long else (price >= plan.stop_loss):
        return _r("stale_entry", "reject", f"{source} price {price} is already through the stop {plan.stop_loss}")
    drift = (price - plan.entry_price) / plan.entry_price * 100 * (1 if long else -1)
    if drift > max_drift_pct:
        return _r("stale_entry", "reject",
                  f"{source} price {price} is {drift:.1f}% past the entry {plan.entry_price} "
                  f"(limit {max_drift_pct}%); the entry has been missed")
    return _r("stale_entry", "pass", f"{source} price {price} is within {max_drift_pct}% of the entry")


# --------------------------------------------------------------------------------------
# Upcoming earnings
# --------------------------------------------------------------------------------------


def check_earnings(plan: TradePlan, earnings: DataSnapshot | None, as_of: datetime) -> RuleResult:
    """Flag earnings that fall inside the horizon's earnings window (or an unknown date)."""
    if earnings is None or earnings.is_gap or not isinstance(earnings.payload, dict):
        return _r("upcoming_earnings", "flag", "next earnings date unknown (no earnings calendar data)")
    raw = earnings.payload.get("next_earnings_date")
    if not raw:
        return _r("upcoming_earnings", "pass", "no upcoming earnings date on record")
    when = date.fromisoformat(str(raw)[:10])
    window = HORIZONS[plan.horizon].earnings_flag_window
    days = (when - as_of.date()).days
    confirmed = "confirmed" if earnings.payload.get("confirmed") else "estimated"
    if 0 <= days <= window.days:
        return _r("upcoming_earnings", "flag",
                  f"earnings on {when.isoformat()} ({confirmed}) in {days} days, inside the "
                  f"{window.days}-day window for a {plan.horizon} trade")
    return _r("upcoming_earnings", "pass", f"next earnings {when.isoformat()} is outside the {window.days}-day window")


# --------------------------------------------------------------------------------------
# News materiality (alerts)
# --------------------------------------------------------------------------------------

MATERIAL_CATEGORIES = {
    "earnings", "guidance", "fda", "clinical_trial", "m_and_a", "analyst_rating_change",
    "offering", "dividend_change", "buyback", "legal", "regulatory", "bankruptcy",
    "delisting", "management_change", "restatement",
}
NOISE_CATEGORIES = {
    "price_action", "market_movers", "listicle", "technical_commentary", "sponsored",
    "rating_reiteration", "options_activity", "opinion",
}
# 8-K items that signal real change: agreements, bankruptcy, cybersecurity incidents,
# results, impairments, delisting, auditor changes/non-reliance, leadership changes,
# charter amendments. Items 7.01 (Reg FD) and 8.01 (other events) are not on the list:
# they carry some real news (e.g. biotech trial results) but mostly routine releases,
# and the item number alone can't tell them apart.
MATERIAL_8K_ITEMS = {"1.01", "1.02", "1.03", "1.05", "2.01", "2.02", "2.03", "2.05", "2.06",
                     "3.01", "3.03", "4.01", "4.02", "5.01", "5.02", "5.03"}

_NOISE = re.compile(
    r"shares? (are |is )?(trading|moving|trade) (higher|lower|up|down)|stocks? (moving|to watch)|"
    r"\btop \d+\b|why .{0,40}(stock|shares) (is|are) (up|down|moving|falling|rising)|"
    r"price target (maintained|reiterated)|\breiterat|\bmaintains?\b.{0,40}\brating|"
    r"unusual options|options activity|52-week (high|low)|technical (analysis|outlook)|"
    r"mid-day movers|pre-market movers|after-hours movers",
    re.IGNORECASE)
_MATERIAL = re.compile(
    r"\bearnings\b|\bresults\b|\bguidance\b|\boutlook\b|\bEPS\b|\brevenue\b|"
    r"\bFDA\b|approv|complete response|\bCRL\b|PDUFA|phase (1|2|3|i{1,3})\b|\btrial\b|topline|"
    r"acqui|merger|buyout|takeover|tender offer|"
    r"upgrade|downgrade|initiat\w* coverage|"
    r"offering|dilut|private placement|convertible|"
    r"bankrupt|chapter 11|delist|going concern|restat|"
    r"SEC (charges|investigation|probe)|subpoena|lawsuit|settle|recall|"
    r"\bCEO\b|\bCFO\b|resign|appoint|step(s|ping)? down|"
    r"dividend|buyback|repurchase|layoff|restructur|impairment|guidance (cut|raise)",
    re.IGNORECASE)


def is_material(event: dict[str, Any]) -> tuple[bool, str]:
    """Classify one news event as material (worth an alert) or noise. Default: noise."""
    category = str(event.get("category") or "").lower()
    headline = str(event.get("headline") or "")
    if category in MATERIAL_CATEGORIES:
        return True, f"category {category}"
    if category in NOISE_CATEGORIES:
        return False, f"category {category}"
    items = {str(i) for i in event.get("sec_items") or []}
    if str(event.get("sec_form") or "").upper().startswith("8-K"):
        hit = sorted(items & MATERIAL_8K_ITEMS)
        return (True, f"8-K item {', '.join(hit)}") if hit else (False, "8-K with no material items")
    if _NOISE.search(headline):
        return False, "noise headline pattern"
    if _MATERIAL.search(headline):
        return True, "material headline keyword"
    return False, "no material signal"


def material_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for e in events if is_material(e)[0]]
