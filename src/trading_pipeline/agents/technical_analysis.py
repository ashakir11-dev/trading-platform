"""Technical analysis — per company, independently: chart viability, entry/exit/stop-loss. Can reject."""

from __future__ import annotations

from ..data.base import RawDataBundle
from ..schemas import Candidate, CompanyDeepDiveOutput, Stage, TechnicalOutput
from .base import StageAgent, report_view


class TechnicalAnalyst(StageAgent):
    stage = Stage.TECHNICAL
    role = """\
Technical Analysis. Judge whether this one company's chart offers a clean, tradeable
setup in the stated direction for a swing or long-term horizon. If it does, give a
concrete plan: entry price and entry condition, target, stop-loss, horizon, and what
would invalidate the setup. If there is no clean setup, reject. Rejecting a
fundamentally strong company on chart grounds is a normal, correct outcome. Evaluate
this chart on its own merits only."""

    async def run(self, candidate: Candidate, company: CompanyDeepDiveOutput, bundle: RawDataBundle, *,
                  show_confidence: bool) -> TechnicalOutput:
        prompt = (
            f"As of {bundle.as_of.isoformat()}. Company: {candidate.ticker}. Direction: {candidate.direction}.\n\n"
            f"<upstream_report stage=\"company_deep_dive\">\n{report_view(company, show_confidence=show_confidence)}\n</upstream_report>\n\n"
            f"<raw_data>\n{bundle.to_prompt()}\n</raw_data>"
        )
        return await self._ask(prompt, TechnicalOutput)
