"""Outcomes agent — tracks real financial results. Deterministic code, no LLM, no judgment."""

from __future__ import annotations

from datetime import datetime

from ..data.base import PriceBar
from ..rules import levels_hit
from ..schemas import OutcomeReport, Position


def compute_outcome(position: Position, bars: list[PriceBar], now: datetime,
                    trigger: str = "close") -> OutcomeReport:
    """``trigger`` is the investor profile's ``level_trigger``, so outcomes agree with alerts."""
    plan = position.plan
    entry = plan.entry_price
    held = [b for b in bars if b.ts >= position.opened_at]
    if position.closed_at is not None:
        held = [b for b in held if b.ts <= position.closed_at]
    if not held and position.exit_price is None:
        raise ValueError(f"no price bars since {position.opened_at.isoformat()} for {position.ticker}")

    long = plan.direction == "long"
    sign = 1.0 if long else -1.0
    last = position.exit_price if position.exit_price is not None else held[-1].close

    lows = [b.low for b in held] or [last]
    highs = [b.high for b in held] or [last]
    worst = min(lows) if long else max(highs)
    best = max(highs) if long else min(lows)

    def pct(price: float) -> float:
        return sign * (price - entry) / entry * 100.0

    end = position.closed_at or now
    return OutcomeReport(
        position_id=position.id,
        ticker=position.ticker,
        direction=plan.direction,
        entry_price=entry,
        last_price=last,
        return_pct=pct(last),
        max_adverse_excursion_pct=min(0.0, pct(worst)),
        max_favorable_excursion_pct=max(0.0, pct(best)),
        hit_stop=any(levels_hit(plan, b, trigger)[0] for b in held),
        hit_target=any(levels_hit(plan, b, trigger)[1] for b in held),
        holding_days=(end - position.opened_at).days,
        closed=position.status == "closed",
    )
