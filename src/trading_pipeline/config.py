"""Pipeline configuration. See docs/ARCHITECTURE.md > Implementation decisions."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel

from .profile import InvestorProfile


class LLMConfig(BaseModel):
    model: str = "claude-opus-5"
    effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"
    max_tokens: int = 16000
    # Server-side refusal fallbacks ("default" routes by refusal category). Set to None to disable.
    fallbacks: Literal["default"] | None = "default"


class PipelineConfig(BaseModel):
    llm: LLMConfig = LLMConfig()

    # Agent 1 output format is an open decision; both score and pass flag are always
    # recorded, this only controls what is forwarded to the company deep dive.
    shortlist_mode: Literal["ranked", "pass_fail"] = "ranked"
    shortlist_max_per_sector: int = 30
    # Cap on sectors pursued after Agent 0 (highest-confidence first). None = no cap.
    # Useful for small first runs; the other sector calls are still logged.
    max_sectors: int | None = None

    # Running confidence score is an open decision: recorded for attribution, but
    # gates nothing unless set, and hidden from downstream agents to avoid anchoring.
    confidence_gate: float | None = None
    show_upstream_confidence: bool = False

    # Max concurrent LLM calls within a stage.
    max_parallel: int = 8

    # Who the pipeline works for (risk, horizons, directions); used by the technical
    # agent, the plan rules and Agent 5.
    profile: InvestorProfile = InvestorProfile()

    # Rules. A plan is stale when price has already run past its entry by more than this
    # (or is already through its stop) when the report is produced.
    stale_entry_max_drift_pct: float = 3.0

    # Agent 5 cadence. After an alert, further alerts for that position are held for
    # alert_cooldown; anything that trips meanwhile is delivered once it expires.
    full_review_interval: timedelta = timedelta(days=14)
    alert_cooldown: timedelta = timedelta(hours=12)

    # Backtests must not tune on data at/after this date (overfitting guard).
    holdout_start: date | None = None
