"""Pipeline configuration. See docs/ARCHITECTURE.md > Implementation decisions."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel


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

    # Running confidence score is an open decision: recorded for attribution, but
    # gates nothing unless set, and hidden from downstream agents to avoid anchoring.
    confidence_gate: float | None = None
    show_upstream_confidence: bool = False

    # Max concurrent LLM calls within a stage.
    max_parallel: int = 8

    # Agent 5 cadence.
    full_review_interval: timedelta = timedelta(days=14)

    # Backtests must not tune on data at/after this date (overfitting guard).
    holdout_start: date | None = None
