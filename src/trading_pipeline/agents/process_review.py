"""Process agent — judges reasoning quality per stage, independent of outcome.

It sees every stage's structured reasoning, the raw data those stages had, and the
outcome report. It never sees the user's accept/reject decision.
"""

from __future__ import annotations

import json

from ..data.base import DataSnapshot
from ..schemas import OutcomeReport, ProcessReviewOutput, StageRecord
from .base import StageAgent


class ProcessReviewer(StageAgent):
    role = """\
Process Review. You audit the pipeline's reasoning on one position, stage by stage.
Grade each stage's reasoning quality on its own merits, independent of how the trade
turned out: a well-reasoned call that lost to a genuine black swan is good process; a
winning call built on unverified catalysts is bad process.

For every risk that materialized (or nearly did), decide whether it was foreseeable
from the data the stage actually had at the time (see the raw data provided and each
snapshot's as_of). Missing macro exposure that was visible in the data is a foreseeable
miss. A risk that depended on data marked UNAVAILABLE is a data_gap, not a reasoning
failure. Attribute the outcome, name the stage most responsible if any, and propose
concrete, general improvements (not rules that would only have fixed this one trade)."""

    async def run(self, ticker: str, trail: list[StageRecord], raw: list[DataSnapshot],
                  outcome: OutcomeReport) -> ProcessReviewOutput:
        trail_json = json.dumps([r.model_dump(mode="json", exclude={"output"}) for r in trail], indent=1)
        raw_json = json.dumps([s.prompt_view() for s in raw], indent=1, default=str)
        prompt = (
            f"Position: {ticker}.\n\n"
            f"<reasoning_trail>\n{trail_json}\n</reasoning_trail>\n\n"
            f"<raw_data_available_to_stages>\n{raw_json}\n</raw_data_available_to_stages>\n\n"
            f"<outcome>\n{outcome.model_dump_json(indent=1)}\n</outcome>"
        )
        return await self._ask(prompt, ProcessReviewOutput)
