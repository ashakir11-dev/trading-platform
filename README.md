# trading-platform

A multi-agent research pipeline for US equities. Independent AI agents narrow the
whole market down to a few trade ideas, each backed by structured, checkable
reasoning. You make every decision. **The system never places orders.**

> **Status: early scaffold.** The pipeline, agents, rules and feedback loop are built
> and tested, but they run against test fixtures. Most real data connectors still have
> to be wired up (see [Status](#status)). Nothing here is financial advice.

## How it works

```
Agent 0          Agent 1              Company             Technical           Middleware
Market scanner → Sector deep dive  →  deep dive        →  analysis         →  report to you
(market →        (per sector →        (per company →      (per company →      │
 sectors)         ranked shortlist)    worthiness,         chart setup,       ▼
                                       catalysts checked)  entry/stop/target)  YOU decide
                                                                               │ accepted
                                                                               ▼
                           Outcomes agent  ◄──  Agent 5: follow-up loop  ◄─────┘
                           (P&L, no judgment)   (alerts + periodic re-review)
                                  │
                                  ▼
                           Process-review agent (grades each stage's reasoning,
                           separates foreseeable misses from black swans)
                                  │
                                  ▼
                           Improvement notes → applied to prompts only after you approve
```

Detailed step-by-step flows are in the
[sequence diagrams](docs/sequence-diagrams.md).

| Stage | What it does |
|---|---|
| **Agent 0: market scanner** | Reads market-wide data and names sectors with upside or downside potential. |
| **Agent 1: sector deep dive** | One agent per sector screens every company from bulk data and returns a shortlist ranked by a 0-100 potential score. |
| **Company deep dive** | One agent per company checks fundamentals and verifies each claimed catalyst against the data. |
| **Technical analysis** | One agent per company reads the charts for your holding horizon and proposes entry, stop, target and horizon, or rejects the setup. |
| **Rules** | Deterministic checks on every plan: price order, your maximum loss, minimum reward:risk, stale entries, upcoming earnings. |
| **Middleware** | Runs the stages, fetches all data, logs everything and reports to you. |
| **Agent 5: follow-up** | Watches accepted positions: alerts on stop/target crossings and material news (12h cooldown), with LLM re-reviews. |
| **Outcomes + process review** | After a trade: plain P&L facts, then a separate review of how good each stage's reasoning was. |

## Design principles

The full design and its decisions are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
The essentials:

- **Decision support only.** No order-placing code exists. Broker connections must be
  read-only, and MCP tools are only callable from an explicit allowlist.
- **Independent agents.** Stages run in sequence; within a stage, each candidate gets its
  own agent that never sees the others, which avoids correlated bias.
- **Raw data travels with the reports.** Each agent receives the previous agent's report
  *and* the data behind it, so it can disagree with a bad upstream call.
- **Structured reasoning, not bare verdicts.** Every agent lists the factors for and
  against, the evidence, the risks it weighed, data gaps and its confidence. This log
  drives the feedback loop.
- **Your decisions stay out of the loop.** Your accept/reject is stored separately and
  never shown to any agent, so the system doesn't learn your biases as its own judgment.
- **No look-ahead.** Every data access takes an `as_of` date, and nothing dated later can
  reach an agent. Financial statements count only from the day after they were filed.
- **Missing data is explicit.** Unavailable data is labelled as a gap in the prompt,
  never silently empty.
- **Swing and long-term horizons only.** No day trading.

## Investor profile

The pipeline works for a specific investor. The profile sets risk tolerance, allowed
horizons, whether shorts are allowed, maximum loss per trade, minimum reward:risk, target
return and free-text preferences. The technical agent plans around it and the rules
enforce it.

```json
{
  "name": "example",
  "risk_tolerance": "moderate",
  "horizons": ["swing", "long_term"],
  "allow_short": false,
  "max_loss_per_trade_pct": 8.0,
  "min_reward_to_risk": 2.0,
  "target_return_pct": 15.0,
  "notes": "Avoid tobacco and weapons. Prefer companies with positive free cash flow."
}
```

Each horizon uses its own charts:

| Horizon | Typical hold | Primary chart | Context chart |
|---|---|---|---|
| `short_term` | days to ~2 weeks | 1-hour | daily |
| `swing` | weeks to ~3 months | daily | weekly |
| `long_term` | months to years | weekly | daily |

## Getting started

Requires Python 3.11+.

```bash
git clone https://github.com/ashakir11-dev/trading-platform.git
cd trading-platform
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest
```

Optional extras:

```bash
pip install -e '.[equibles]'           # hosted Equibles MCP (fundamentals)
pip install -e '.[equibles-postgres]'  # self-hosted Equibles database
```

### Configuration

| Setting | Where |
|---|---|
| Anthropic API key | `ANTHROPIC_API_KEY` environment variable (or an `ant auth login` profile) |
| Model, effort | `PipelineConfig.llm` (default `claude-opus-5`, effort `high`) |
| Investor profile | copy `profile.example.json`, load with `InvestorProfile.load(path)` |
| Rule limits, alert cooldown, review interval | `PipelineConfig` in `src/trading_pipeline/config.py` |
| Equibles API key | pass as a `Bearer` header to `HttpMcpClient` |

### Wiring a run

There is no CLI yet. A run is wired in Python. The data providers below are the ones
that exist today; the price provider still needs a real adapter before a live run works.

```python
import asyncio
from datetime import datetime, timezone

from trading_pipeline import Middleware, PipelineConfig, Store, render_report
from trading_pipeline.data import DataProviders
from trading_pipeline.data.equibles import EQUIBLES_MCP_URL, FACT_TOOL, EquiblesFundamentals
from trading_pipeline.data.gaps import UnavailableNews, UnavailableSectorData
from trading_pipeline.data.mcp import HttpMcpClient
from trading_pipeline.llm import AnthropicLLM
from trading_pipeline.profile import InvestorProfile


async def main(equibles_key: str, prices, quotes):
    config = PipelineConfig(profile=InvestorProfile.load("my-profile.json"))
    async with HttpMcpClient(EQUIBLES_MCP_URL, allowed_tools={FACT_TOOL},
                             headers={"Authorization": f"Bearer {equibles_key}"}) as mcp:
        data = DataProviders(prices=prices, quotes=quotes,
                             sectors=UnavailableSectorData(), news=UnavailableNews(),
                             fundamentals=EquiblesFundamentals(mcp))
        mw = Middleware(config, AnthropicLLM(config.llm), data, Store("pipeline.sqlite3"))
        report = await mw.run(datetime.now(timezone.utc))
        print(render_report(report))
        # Your decision; only accepted candidates enter the follow-up loop:
        # mw.record_decision(candidate_id, accepted=True)
```

The tests (`tests/test_pipeline.py`) run the complete flow end to end with a scripted
LLM and fixture data, which is the best reference for how the pieces fit.

## Data sources

Agents depend only on the provider interfaces in `src/trading_pipeline/data/base.py`,
never on a vendor. Research and decisions:

| Category | Current state |
|---|---|
| Company fundamentals | **Equibles** (hosted MCP), point-in-time by filing date |
| Price history, indicators, pivots | Adapter skeleton only (Massive); Sharadar or Norgate recommended for backtests |
| Live quotes | Adapter skeleton only; Alpaca free tier recommended |
| Sector screen and breadth | Gap: to be derived from prices |
| News, catalysts, earnings calendar | Gap |

See [`docs/data-sources-research.md`](docs/data-sources-research.md),
[`docs/live-prices-research.md`](docs/live-prices-research.md) and
[`docs/equibles-evaluation.md`](docs/equibles-evaluation.md).

## Project layout

```
src/trading_pipeline/
  middleware.py        runs the stages, carries data forward, logs reasoning, user boundary
  agents/              one module per agent (scanner, sector, company, technical,
                       follow-up, outcomes, process review)
  schemas.py           stage outputs (structured reasoning), records, positions
  profile.py           investor profile, horizon -> chart timeframes
  rules.py             deterministic rules (plan checks, stale entry, earnings, news filter)
  config.py            PipelineConfig / LLMConfig
  llm.py               Claude access via structured outputs
  store.py             SQLite: reasoning logs, snapshots, positions, reviews, user decisions
  data/base.py         provider interfaces, point-in-time RawDataBundle
  data/equibles.py     Equibles fundamentals (hosted MCP or self-hosted Postgres)
  data/mcp.py          allowlisted MCP client + skeleton vendor adapters
  data/gaps.py         explicit placeholders for missing data
tests/                 scripted-LLM + fixture tests
docs/                  architecture, sequence diagrams, data research
profile.example.json   example investor profile
```

## Testing

```bash
pytest
```

Everything runs offline with a scripted LLM and fixture data. The self-hosted Equibles
SQL tests also run when `EQUIBLES_TEST_DSN` points at a scratch UTF-8 Postgres database.

## Status

**Built:** all agents, middleware, structured reasoning log, point-in-time data guard,
investor profile, rules module, conflict recording, follow-up alerts with a news filter and
cooldown, outcomes and process review with human-approved improvements, Equibles
fundamentals.

**Next:**
- Real adapters for prices, live quotes, news/filings and an earnings calendar.
- A CLI or UI for the report and your decisions.
- Backtesting and forward (paper) testing. Only results after the model's training
  cutoff count as honest evidence, so forward testing will be the main measure.

Open design questions are tracked in
[`docs/ARCHITECTURE.md` §5](docs/ARCHITECTURE.md#5-design-decisions).

## Disclaimer

This is a research project. Its output is not financial advice, early versions are
expected to be wrong often, and whether the approach makes money is unknown. You are
responsible for every trade you make.
