"""Agent 0 — scans the overall market and outputs sectors with upside/downside potential."""

from __future__ import annotations

from ..data.base import RawDataBundle
from ..schemas import MarketScanOutput, Stage
from .base import StageAgent


class MarketScanner(StageAgent):
    stage = Stage.MARKET_SCAN
    role = """\
Agent 0, Market Scanner. From the market-wide raw data, identify the sectors with the
most meaningful upside or downside potential over a swing / long-term horizon. Output
only sectors you can support from the data; an empty list is acceptable. Give each
sector its own thesis and its own structured reasoning."""

    async def run(self, bundle: RawDataBundle) -> MarketScanOutput:
        prompt = f"As of {bundle.as_of.isoformat()}.\n\n<raw_data>\n{bundle.to_prompt()}\n</raw_data>"
        return await self._ask(prompt, MarketScanOutput)
