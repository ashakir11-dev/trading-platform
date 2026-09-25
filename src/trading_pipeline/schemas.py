"""Typed contracts between stages.

Two kinds of models live here:

* **Agent outputs** (``*Output``): what an LLM stage returns, parsed via structured
  outputs. Every one carries a ``StageReasoning``, never a bare verdict.
* **Records** (``StageRecord``, ``Candidate``, ``Position``, ...): what the middleware
  persists and passes around.

Keep agent-output models to plain types (str / int / float / bool / Literal / nested
models / lists) so they translate cleanly to JSON schema for structured outputs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def new_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Stage(str, Enum):
    MARKET_SCAN = "market_scan"
    SECTOR_DEEP_DIVE = "sector_deep_dive"
    COMPANY_DEEP_DIVE = "company_deep_dive"
    TECHNICAL = "technical"
    FOLLOW_UP_TRIPWIRE = "follow_up_tripwire"
    FOLLOW_UP_FULL_REVIEW = "follow_up_full_review"


Direction = Literal["long", "short"]


# --------------------------------------------------------------------------------------
# Structured reasoning (shared by every stage)
# --------------------------------------------------------------------------------------


class ReasoningFactor(BaseModel):
    """One thing that pushed the agent toward or away from its conclusion."""

    direction: Literal["toward", "away"]
    factor: str
    weight: Literal["low", "medium", "high"]
    evidence: str = Field(description="The specific raw data point(s) this factor rests on.")


class RiskAssessment(BaseModel):
    risk: str
    category: Literal["macro", "sector", "company", "technical", "liquidity", "regulatory", "event", "other"]
    assessment: str = Field(description="How the risk was weighed and why it does or doesn't change the verdict.")


class StageReasoning(BaseModel):
    summary: str
    factors: list[ReasoningFactor]
    risks_considered: list[RiskAssessment]
    data_gaps: list[str] = Field(description="Data that was missing or marked unavailable and would have mattered.")
    confidence: float = Field(description="0.0-1.0 confidence in this stage's conclusion for this subject.")


# --------------------------------------------------------------------------------------
# Agent 0 — Market Scanner
# --------------------------------------------------------------------------------------


class SectorCall(BaseModel):
    sector: str
    direction: Literal["upside", "downside"]
    thesis: str
    reasoning: StageReasoning


class MarketScanOutput(BaseModel):
    market_summary: str
    sectors: list[SectorCall]


# --------------------------------------------------------------------------------------
# Agent 1 — Sector Deep Dive
# --------------------------------------------------------------------------------------


class Catalyst(BaseModel):
    kind: Literal["earnings", "fda", "analyst_action", "product", "regulatory", "macro", "m_and_a", "other"]
    description: str
    expected_date: str | None = Field(description="ISO date if known, else null.")
    source: str = Field(description="Which raw data snapshot or source this came from.")


class ShortlistEntry(BaseModel):
    ticker: str
    company_name: str
    # Both are always recorded; PipelineConfig.shortlist_mode picks which drives forwarding.
    potential_score: int = Field(description="0-100 relative upside/downside potential within this sector.")
    passed: bool
    catalysts: list[Catalyst]
    reasoning: StageReasoning


class SectorDeepDiveOutput(BaseModel):
    sector: str
    sector_view: str
    shortlist: list[ShortlistEntry]


# --------------------------------------------------------------------------------------
# Company Deep Dive
# --------------------------------------------------------------------------------------


class CatalystCheck(BaseModel):
    catalyst: str
    status: Literal["verified", "unverified", "contradicted"]
    notes: str


class CompanyDeepDiveOutput(BaseModel):
    ticker: str
    verdict: Literal["pass", "reject"]
    thesis: str
    catalyst_checks: list[CatalystCheck]
    reasoning: StageReasoning


# --------------------------------------------------------------------------------------
# Technical Analysis
# --------------------------------------------------------------------------------------


class TradePlan(BaseModel):
    direction: Direction
    entry_price: float
    entry_condition: str = Field(description="What must be true on the chart to enter, e.g. 'daily close above 42.10'.")
    target_price: float
    stop_loss: float
    horizon: Literal["swing", "long_term"]
    invalidation: str


class TechnicalOutput(BaseModel):
    ticker: str
    verdict: Literal["pass", "reject"]
    setup: str
    plan: TradePlan | None = Field(description="Required when verdict is 'pass', null when 'reject'.")
    reasoning: StageReasoning


# --------------------------------------------------------------------------------------
# Agent 5 — Follow-up full re-review
# --------------------------------------------------------------------------------------


class FullReviewOutput(BaseModel):
    ticker: str
    action: Literal["hold", "adjust_plan", "exit"]
    thesis_intact: bool
    updated_plan: TradePlan | None
    reasoning: StageReasoning


# --------------------------------------------------------------------------------------
# Process review
# --------------------------------------------------------------------------------------


class StageGrade(BaseModel):
    stage: Stage
    grade: int = Field(description="1 (poor) to 5 (excellent) reasoning quality, independent of outcome.")
    reasoning_sound: bool
    missed_foreseeable_risks: list[str]
    notes: str


class ImprovementSuggestion(BaseModel):
    target_stage: Stage
    suggestion: str


class ProcessReviewOutput(BaseModel):
    ticker: str
    stage_grades: list[StageGrade]
    outcome_attribution: Literal["not_a_loss", "foreseeable_miss", "black_swan", "normal_variance", "data_gap"]
    primary_stage_at_fault: Stage | None
    attribution_reasoning: str
    improvements: list[ImprovementSuggestion]


# --------------------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------------------


class StageRecord(BaseModel):
    """One agent invocation's structured reasoning log (the feedback loop's backbone)."""

    id: str = Field(default_factory=new_id)
    run_id: str
    stage: Stage
    subject: str  # sector name or ticker
    candidate_id: str | None = None
    position_id: str | None = None
    verdict: str
    reasoning: StageReasoning
    output: dict[str, Any]
    raw_data_ids: list[str]
    as_of: datetime
    created_at: datetime = Field(default_factory=utcnow)


class ConfidencePoint(BaseModel):
    stage: Stage
    confidence: float


class Candidate(BaseModel):
    """A company travelling through the pipeline. Carries the running confidence trajectory."""

    id: str = Field(default_factory=new_id)
    run_id: str
    ticker: str
    company_name: str
    sector: str
    direction: Direction
    shortlist: ShortlistEntry
    confidence_trajectory: list[ConfidencePoint] = []
    status: Literal["active", "rejected", "recommended"] = "active"
    rejected_at: Stage | None = None

    def record_confidence(self, stage: Stage, confidence: float) -> None:
        self.confidence_trajectory.append(ConfidencePoint(stage=stage, confidence=confidence))

    def reject(self, stage: Stage) -> None:
        self.status = "rejected"
        self.rejected_at = stage


class Recommendation(BaseModel):
    candidate: Candidate
    company: CompanyDeepDiveOutput
    technical: TechnicalOutput
    live_quote: float | None = None


class Rejection(BaseModel):
    ticker: str
    stage: Stage
    summary: str


class PipelineReport(BaseModel):
    run_id: str
    as_of: datetime
    market: MarketScanOutput
    recommendations: list[Recommendation]
    rejections: list[Rejection]


class UserDecision(BaseModel):
    """The human's go/no-go. Stored apart from stage records; never shown to review agents."""

    id: str = Field(default_factory=new_id)
    candidate_id: str
    accepted: bool
    note: str = ""
    decided_at: datetime = Field(default_factory=utcnow)


class Position(BaseModel):
    id: str = Field(default_factory=new_id)
    run_id: str
    candidate_id: str
    ticker: str
    sector: str
    plan: TradePlan
    opened_at: datetime
    status: Literal["open", "closed"] = "open"
    last_full_review_at: datetime | None = None
    closed_at: datetime | None = None
    exit_price: float | None = None


class TripwireResult(BaseModel):
    position_id: str
    checked_at: datetime
    tripped: bool
    reasons: list[str]
    last_price: float | None


class OutcomeReport(BaseModel):
    """Pure financial facts. No judgment."""

    position_id: str
    ticker: str
    direction: Direction
    entry_price: float
    last_price: float
    return_pct: float
    max_adverse_excursion_pct: float
    max_favorable_excursion_pct: float
    hit_stop: bool
    hit_target: bool
    holding_days: int
    closed: bool


class ImprovementNote(BaseModel):
    """Process-agent suggestion. Only human-approved notes reach stage prompts."""

    id: str = Field(default_factory=new_id)
    source_position_id: str
    target_stage: Stage
    text: str
    approved: bool = False
    created_at: datetime = Field(default_factory=utcnow)
