"""Agent 1 — per sector, shortlists ~10-30 companies via fundamentals, news, FDA, earnings."""

from __future__ import annotations

from ..data.base import RawDataBundle
from ..schemas import SectorCall, SectorDeepDiveOutput, Stage
from .base import StageAgent, report_view


class SectorDeepDive(StageAgent):
    stage = Stage.SECTOR_DEEP_DIVE
    role = """\
Agent 1, Sector Deep Dive. Examine one sector and produce a shortlist of roughly 10-30
companies worth a company-level deep dive, using fundamentals, news, FDA events,
earnings and other catalysts in the raw data. For EVERY company you evaluate, give both
a potential_score (0-100, relative within this sector) and a pass/fail flag, and
list the catalysts with the source snapshot each came from. Include notable companies
you reject (passed=false) so the reasoning log shows what was filtered out and why."""

    async def run(self, sector: SectorCall, bundle: RawDataBundle, *, show_confidence: bool) -> SectorDeepDiveOutput:
        prompt = (
            f"As of {bundle.as_of.isoformat()}.\n\n"
            f"<upstream_report stage=\"market_scan\">\n{report_view(sector, show_confidence=show_confidence)}\n</upstream_report>\n\n"
            f"<raw_data>\n{bundle.to_prompt()}\n</raw_data>"
        )
        return await self._ask(prompt, SectorDeepDiveOutput)
