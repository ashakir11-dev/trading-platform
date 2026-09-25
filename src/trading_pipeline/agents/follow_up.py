"""Agent 5 — follow-up loop over accepted positions.

Each ``tick`` runs cheap tripwire checks (deterministic: price vs stop/target, new
catalyst events) on every open position, and a deep LLM full re-review when a tripwire
fires or ``full_review_interval`` has elapsed. An external scheduler calls ``tick``.
It flags; it never closes or trades — the user acts.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel

from ..config import PipelineConfig
from ..data.base import DataProviders, DataSnapshot, PriceBar, RawDataBundle
from ..schemas import FullReviewOutput, Position, Stage, StageRecord, TripwireResult
from ..store import Store
from .base import StageAgent


def check_tripwires(position: Position, bars: list[PriceBar], news: DataSnapshot | None,
                    now: datetime) -> TripwireResult:
    plan = position.plan
    reasons: list[str] = []
    last = bars[-1].close if bars else None
    if last is not None:
        long = plan.direction == "long"
        if (last <= plan.stop_loss) if long else (last >= plan.stop_loss):
            reasons.append(f"price {last} crossed stop {plan.stop_loss}")
        if (last >= plan.target_price) if long else (last <= plan.target_price):
            reasons.append(f"price {last} reached target {plan.target_price}")
    if news is not None and not news.is_gap and news.payload:
        reasons.append("new news/catalyst events since last check")
    return TripwireResult(position_id=position.id, checked_at=now, tripped=bool(reasons),
                          reasons=reasons, last_price=last)


class FullReviewer(StageAgent):
    stage = Stage.FOLLOW_UP_FULL_REVIEW
    role = """\
Follow-Up Full Re-Review. A position the user accepted is open. Re-examine it from
scratch with fresh data: is the original thesis still intact, does the technical plan
still hold? Recommend hold, adjust_plan (with an updated plan), or exit. You advise;
the user decides and executes."""

    async def run(self, position: Position, original: list[StageRecord], tripwire: TripwireResult,
                  bundle: RawDataBundle) -> FullReviewOutput:
        trail = "\n".join(r.model_dump_json(exclude={"output"}) for r in original)
        prompt = (
            f"As of {bundle.as_of.isoformat()}. Position: {position.ticker}, opened "
            f"{position.opened_at.isoformat()}.\n\n"
            f"<current_plan>\n{position.plan.model_dump_json(indent=1)}\n</current_plan>\n\n"
            f"<original_reasoning>\n{trail}\n</original_reasoning>\n\n"
            f"<tripwire_check>\n{tripwire.model_dump_json(indent=1)}\n</tripwire_check>\n\n"
            f"<raw_data>\n{bundle.to_prompt()}\n</raw_data>"
        )
        return await self._ask(prompt, FullReviewOutput)


class FollowUpEvent(BaseModel):
    position_id: str
    ticker: str
    tripwire: TripwireResult
    review: FullReviewOutput | None = None


class FollowUpLoop:
    def __init__(self, reviewer: FullReviewer, data: DataProviders, store: Store, config: PipelineConfig) -> None:
        self._reviewer = reviewer
        self._data = data
        self._store = store
        self._config = config

    async def tick(self, now: datetime) -> list[FollowUpEvent]:
        events = []
        for position in self._store.open_positions():
            events.append(await self._check(position, now))
        return events

    async def _check(self, position: Position, now: datetime) -> FollowUpEvent:
        prev = self._store.last_tripwire(position.id)
        since = prev.checked_at if prev else position.opened_at
        bars = await self._data.prices.bars(position.ticker, position.opened_at.date(), now)
        news = await self._data.news.events(position.ticker, since, now)

        tripwire = check_tripwires(position, bars, news, now)
        self._store.save_tripwire(tripwire)
        event = FollowUpEvent(position_id=position.id, ticker=position.ticker, tripwire=tripwire)

        last_full = position.last_full_review_at or position.opened_at
        if tripwire.tripped or now - last_full >= self._config.full_review_interval:
            event.review = await self._full_review(position, tripwire, news, now)
        return event

    async def _full_review(self, position: Position, tripwire: TripwireResult, news: DataSnapshot,
                           now: datetime) -> FullReviewOutput:
        bundle = RawDataBundle(as_of=now)
        lookback = (now - timedelta(days=365)).date()
        bundle.extend([
            await self._data.prices.ohlcv(position.ticker, lookback, now),
            await self._data.prices.indicators(position.ticker, now),
            await self._data.prices.pivots(position.ticker, now),
            await self._data.fundamentals.fundamentals(position.ticker, now),
            news,
        ])
        self._store.save_snapshots(bundle.snapshots)

        original = self._store.stage_records(candidate_id=position.candidate_id)
        review = await self._reviewer.run(position, original, tripwire, bundle)
        self._store.save_stage_record(StageRecord(
            run_id=position.run_id, stage=Stage.FOLLOW_UP_FULL_REVIEW, subject=position.ticker,
            position_id=position.id, verdict=review.action, reasoning=review.reasoning,
            output=review.model_dump(mode="json"), raw_data_ids=bundle.ids, as_of=now,
        ))
        position.last_full_review_at = now
        self._store.save_position(position)
        return review
