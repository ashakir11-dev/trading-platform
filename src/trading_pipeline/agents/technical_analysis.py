"""Technical analysis — per company, independently: chart viability, entry/exit/stop-loss. Can reject."""

from __future__ import annotations

from ..data.base import RawDataBundle
from ..profile import InvestorProfile
from ..schemas import Candidate, CompanyDeepDiveOutput, Stage, TechnicalOutput
from .base import StageAgent, report_view


class TechnicalAnalyst(StageAgent):
    stage = Stage.TECHNICAL
    role = """\
Technical Analysis. Judge whether this one company's chart offers a clean, tradeable
setup in the stated direction, for this investor. If it does, give a concrete plan:
entry price and entry condition, target, stop-loss, horizon, the chart timeframe the
levels come from, and what would invalidate the setup. If there is no clean setup,
reject. Rejecting a fundamentally strong company on chart grounds is a normal, correct
outcome. Evaluate this chart on its own merits only.

Fit the plan to the investor profile:
- Choose the horizon from the investor's allowed horizons that this setup actually
  suits. Read levels from that horizon's primary chart (short_term: 1h, swing: 1d,
  long_term: 1w) and use its context chart for trend. Set chart_timeframe to the
  primary chart's interval. Data for each timeframe is in the raw data as "ohlcv:<interval>".
- The stop must be a level the chart justifies, not an arbitrary percentage. If the
  chart-justified stop is further from entry than max_loss_per_trade_pct, or the
  target cannot give at least min_reward_to_risk, reject rather than force a plan.
- Respect allow_short and any free-text notes.
- An upcoming earnings date (see the earnings calendar in the raw data) is event risk
  for the holding window; weigh it and say how."""

    async def run(self, candidate: Candidate, company: CompanyDeepDiveOutput, bundle: RawDataBundle, *,
                  profile: InvestorProfile, show_confidence: bool) -> TechnicalOutput:
        prompt = (
            f"As of {bundle.as_of.isoformat()}. Company: {candidate.ticker}. Direction: {candidate.direction}.\n\n"
            f"<investor_profile>\n{profile.prompt_view()}\n</investor_profile>\n\n"
            f"<upstream_report stage=\"company_deep_dive\">\n{report_view(company, show_confidence=show_confidence)}\n</upstream_report>\n\n"
            f"<raw_data>\n{bundle.to_prompt()}\n</raw_data>"
        )
        return await self._ask(prompt, TechnicalOutput)
