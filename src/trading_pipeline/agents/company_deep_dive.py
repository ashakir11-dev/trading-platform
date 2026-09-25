"""Company deep dive — per company, evaluates worthiness and scrutinizes stated catalysts."""

from __future__ import annotations

from ..data.base import RawDataBundle
from ..schemas import CompanyDeepDiveOutput, SectorCall, ShortlistEntry, Stage
from .base import StageAgent, report_view


class CompanyDeepDive(StageAgent):
    stage = Stage.COMPANY_DEEP_DIVE
    role = """\
Company Deep Dive. Decide whether this one company is fundamentally worth pursuing in
the stated direction. Scrutinize every catalyst the sector stage cited: mark it
verified, unverified (no supporting data) or contradicted (data says otherwise) against
the raw data. Unverified catalysts must not carry the thesis. Do not consider the chart;
technical tradeability is judged separately by another agent."""

    async def run(self, entry: ShortlistEntry, sector: SectorCall, bundle: RawDataBundle, *,
                  show_confidence: bool) -> CompanyDeepDiveOutput:
        prompt = (
            f"As of {bundle.as_of.isoformat()}. Company: {entry.ticker} ({entry.company_name}). "
            f"Sector direction: {sector.direction}.\n\n"
            f"<upstream_report stage=\"market_scan\">\n{report_view(sector, show_confidence=show_confidence)}\n</upstream_report>\n\n"
            f"<upstream_report stage=\"sector_deep_dive\">\n{report_view(entry, show_confidence=show_confidence)}\n</upstream_report>\n\n"
            f"<raw_data>\n{bundle.to_prompt()}\n</raw_data>"
        )
        return await self._ask(prompt, CompanyDeepDiveOutput)
