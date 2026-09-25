# trading-platform

A multi-agent research pipeline for US equities. Independent AI agents narrow the
whole market down to a few trade ideas, each backed by structured, checkable
reasoning. You make every decision. **The system never places orders.**

> **Status: built, not yet run live.** The pipeline, agents, rules, feedback loop,
> Equibles data connectors and CLI are built and tested offline. The first run against
> the live Equibles and Anthropic APIs is still to come (see [Status](#status)).
> Nothing here is financial advice.

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
return, whether a stop/target counts as hit on the close or intraday (`level_trigger`),
and free-text preferences. The technical agent plans around it and the rules
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
  "level_trigger": "close",
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

```bash
pip install -e '.[equibles]'
export EQUIBLES_API_KEY=...        # market data
export ANTHROPIC_API_KEY=...       # the agents
export TRADING_PROFILE=~/.trading-platform/profile.json   # optional; copy profile.example.json
```

Other settings (database path, model and effort overrides) are in
[`docs/operations.md`](docs/operations.md).

### Using it

```bash
trading-pipeline check                            # pre-flight: every data source, no LLM
trading-pipeline run --max-sectors 1 --shortlist 3  # a small first run
trading-pipeline run                              # after the close; prints the report
trading-pipeline decide CANDIDATE_ID accept       # or reject, with --note
trading-pipeline positions
trading-pipeline follow-up                        # Agent 5; schedule it with cron
trading-pipeline close POSITION_ID --price 123.45 # after you exit
trading-pipeline review POSITION_ID               # outcome + process review
trading-pipeline notes                            # improvement suggestions
trading-pipeline approve-note NOTE_ID             # only approved notes reach prompts
```

`trading-pipeline run --as-of DATE --backtest` runs as of a past close. The full
workflow, cron examples and where data is stored are in
[`docs/operations.md`](docs/operations.md).

The tests (`tests/test_pipeline.py`, `tests/test_cli.py`) run the complete flow end to
end with a scripted LLM and fixture data.

## Data sources

All data comes from **[Equibles](https://equibles.com)** (hosted MCP), through one
read-only client that can only call the tools the connectors declare. Anything Equibles
doesn't provide is deferred. Agents depend only on the provider interfaces in
`src/trading_pipeline/data/base.py`, never on the vendor.

| Category | State |
|---|---|
| Company fundamentals (point-in-time by filing date) | Built |
| Daily/weekly prices, indicators, support/resistance | Built (computed locally from Equibles prices) |
| Quotes | Built: live on Equibles Plus/Pro, last close otherwise |
| Sector performance, sector screen and breadth | Built (sector ETFs and their holdings, with tickers) |
| SEC filings, 8-K events, company press releases, FDA advisory meetings | Built |
| Earnings date | Built: announced date on live runs, estimate from past filings otherwise |
| Macro (FRED series, VIX, put/call, release calendar) | Built |
| Screener ratios, guidance, analyst estimates, transcripts | Available in Equibles; not yet wired |
| Third-party news, FDA decision dates | Deferred (not in Equibles) |

All connectors are verified against real Equibles responses. Run
`trading-pipeline check` before a run to confirm your account returns every data type.

Details and backtest caveats are in
[`docs/ARCHITECTURE.md` §6](docs/ARCHITECTURE.md#6-data-requirements).

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
  cli.py, app.py       trading-pipeline command and provider wiring
  data/base.py         provider interfaces, point-in-time RawDataBundle
  data/equibles*.py    Equibles connectors: fundamentals, prices, sectors, events, macro
  data/technicals.py   indicators and support/resistance computed from price bars
  data/mcp.py          allowlisted MCP client + skeleton vendor adapters
  data/gaps.py         explicit placeholders for missing data
tests/                 scripted-LLM + fixture tests
docs/                  architecture, operations guide, sequence diagrams, research
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
investor profile, rules, conflict recording, follow-up alerts (news filter, cooldown,
"action needed" prompts), outcomes and process review with human-approved improvements,
all Equibles connectors, and the `trading-pipeline` CLI.

**Next:** the first live run against Equibles and Anthropic; Equibles Cloud tools (live
quotes, intraday bars, screener ratios) once their reference is available; and
backtesting/forward testing, planned in [`docs/testing-research.md`](docs/testing-research.md).
The full list is in
[`docs/ARCHITECTURE.md` → Remaining work](docs/ARCHITECTURE.md#remaining-work).

## Disclaimer

This is a research project. Its output is not financial advice, early versions are
expected to be wrong often, and whether the approach makes money is unknown. You are
responsible for every trade you make.
