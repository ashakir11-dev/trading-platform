"""Investor profile and holding-horizon definitions.

The profile describes the person the pipeline works for: risk tolerance, loss
limits, return targets, which holding horizons and directions they trade. It is
the user's *preferences*, set up front. It is not a decision, so it does not
conflict with the one-way middleware principle: it may be shown to agents.

Each horizon maps to the chart timeframes the technical agent must read.
Day trading is intentionally absent: it conflicts with design principle 7
(swing or long-term only), because intraday data goes stale while the pipeline runs.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

Horizon = Literal["short_term", "swing", "long_term"]


class ChartSpec(BaseModel):
    interval: Literal["1h", "1d", "1w"]
    lookback: timedelta
    role: Literal["primary", "context"]


class HorizonSpec(BaseModel):
    label: str
    typical_hold: str
    holding_window: timedelta
    charts: list[ChartSpec]
    earnings_flag_window: timedelta  # flag earnings that fall within this window from as_of


HORIZONS: dict[str, HorizonSpec] = {
    "short_term": HorizonSpec(
        label="Short-term trade", typical_hold="a few days to ~2 weeks",
        holding_window=timedelta(days=14),
        charts=[ChartSpec(interval="1h", lookback=timedelta(days=30), role="primary"),
                ChartSpec(interval="1d", lookback=timedelta(days=180), role="context")],
        earnings_flag_window=timedelta(days=14),
    ),
    "swing": HorizonSpec(
        label="Swing trade", typical_hold="a few weeks to ~3 months",
        holding_window=timedelta(days=90),
        charts=[ChartSpec(interval="1d", lookback=timedelta(days=365), role="primary"),
                ChartSpec(interval="1w", lookback=timedelta(days=730), role="context")],
        earnings_flag_window=timedelta(days=45),
    ),
    "long_term": HorizonSpec(
        label="Long-term investment", typical_hold="many months to years",
        holding_window=timedelta(days=365),
        charts=[ChartSpec(interval="1w", lookback=timedelta(days=5 * 365), role="primary"),
                ChartSpec(interval="1d", lookback=timedelta(days=365), role="context")],
        earnings_flag_window=timedelta(days=30),
    ),
}


class InvestorProfile(BaseModel):
    """Who the pipeline is working for. Load from JSON with ``InvestorProfile.load``."""

    name: str = "default"
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "moderate"
    horizons: list[Horizon] = Field(default_factory=lambda: ["swing", "long_term"],
                                    description="Holding horizons this investor trades.")
    allow_short: bool = Field(False, description="If False, downside sector calls are not pursued.")
    max_loss_per_trade_pct: float = Field(10.0, description="Max stop distance from entry, in percent.")
    min_reward_to_risk: float = Field(2.0, description="Minimum (target - entry) / (entry - stop).")
    target_return_pct: float | None = Field(None, description="Typical return the investor aims for per trade.")
    level_trigger: Literal["close", "intraday"] = Field(
        "close", description="When a stop or target counts as hit: on a closing price beyond it ('close'), "
                             "or as soon as the bar's low/high touches it ('intraday'). Used by alerts and outcomes.")
    notes: str = Field("", description="Free-text preferences, e.g. sectors to avoid.")

    def charts(self) -> list[ChartSpec]:
        """Union of chart timeframes for the allowed horizons, longest lookback per interval."""
        best: dict[str, ChartSpec] = {}
        for h in self.horizons:
            for c in HORIZONS[h].charts:
                cur = best.get(c.interval)
                if cur is None:
                    best[c.interval] = c
                else:
                    role = "primary" if "primary" in (cur.role, c.role) else "context"
                    best[c.interval] = ChartSpec(interval=c.interval, lookback=max(cur.lookback, c.lookback), role=role)
        return list(best.values())

    def prompt_view(self) -> str:
        horizons = {h: {"label": HORIZONS[h].label, "typical_hold": HORIZONS[h].typical_hold,
                        "charts": [f"{c.interval} ({c.role})" for c in HORIZONS[h].charts]}
                    for h in self.horizons}
        data = self.model_dump(mode="json", exclude={"horizons"})
        data["allowed_horizons"] = horizons
        return json.dumps(data, indent=1)

    @classmethod
    def load(cls, path: str | Path) -> InvestorProfile:
        return cls.model_validate_json(Path(path).read_text())
