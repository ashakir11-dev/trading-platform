# trading-platform

A multi-agent research pipeline for US equities, built as Claude Code subagents.
Independent AI agents narrow the whole market down to a few trade ideas, each backed by
structured, checkable reasoning. You make every decision. **The system never places
orders.**

> **Status: running live.** Full runs work end to end against Equibles and Claude
> (about 14 minutes for one sector and three candidates). Follow-up, evaluation,
> feedback and backtests are built; see [Status](#status). Nothing here is financial
> advice.

## How it works

```
Middleware agent (orchestrates; the only one that talks to you and reads your decisions)
 │
 ├─ market-scanner ──► sector-deep-dive ×N ──► company-deep-dive ×M ──► technical-analysis ×M
 │   market → sectors   sector → ranked         company → worthiness,     chart → entry/stop/target,
 │                      shortlist               catalysts checked         your profile's rules
 │                                                                              │
 │                                                            report ──► YOU decide (/decide)
 │                                                                              │ accepted
 ├─ follow-up (Agent 5) ◄───────────────────────────────────────────────────────┘
 │   stop/target and material-news alerts, periodic re-review
 │
 ├─ stage-evaluator: grades each agent's past calls against what happened
 └─ stage-feedback:  proposes lessons from those grades → added to prompts only after you approve
```

Each agent is a subagent (`.claude/agents/`) that fetches its own data from the
Equibles MCP server and writes its analysis to a folder in `workspace/`. The next agent
reads that folder, including every raw data response, so it can disagree with a bad
upstream call.

| Agent | What it does |
|---|---|
| **market-scanner** | Reads sector ETF performance and macro data; names sectors with upside or downside potential. |
| **sector-deep-dive** | One per sector: screens the sector's largest companies into a shortlist ranked by a 0-100 potential score. |
| **company-deep-dive** | One per candidate: checks fundamentals and verifies each claimed catalyst against filings and news. |
| **technical-analysis** | One per candidate: reads the charts for your horizon, proposes entry, stop, target and horizon, applies your profile's rules, or rejects. |
| **middleware** | Runs the stages, applies the forwarding rules, re-checks each plan's numbers, reports to you, records your decisions. |
| **follow-up** | Watches accepted positions: stop/target and material-news alerts (12h cooldown), full re-review on alert or every 14 days. |
| **stage-evaluator / stage-feedback** | Grade each agent's past calls (outcome facts and, separately, reasoning quality) and propose lessons. |
| **gatekeeper / pit-auditor** | Backtests only: build and audit point-in-time data packs. |

## Design principles

The full design is in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (principles and
decisions) and [`docs/prompt-subagents-design.md`](docs/prompt-subagents-design.md)
(how the subagents implement them). The essentials:

- **Decision support only.** Nothing places orders. Agents can only call read-only
  Equibles tools listed in their definition; the account-changing tools are denied.
- **Independent agents.** Stages run in sequence; within a stage, each candidate gets its
  own agent that never sees the others, which avoids correlated bias.
- **Raw data travels with the reports.** Every Equibles response an agent receives is
  saved to its folder automatically, and the next agent reads it.
- **Structured reasoning, not bare verdicts.** Every agent lists the factors for and
  against with their evidence, the risks it weighed, data gaps and its confidence. This
  record drives evaluation and feedback.
- **Your decisions stay out of the loop.** Your accept/reject and notes live in
  `workspace/decisions/`, which a hook blocks every agent from reading, so the system
  doesn't learn your biases as its own judgment.
- **No look-ahead.** Every run has an `as_of`. Backtests use a gatekeeper agent that
  filters data to what was public then, and an auditor that checks it.
- **Missing data is explicit.** Anything unavailable or not checked is listed as a gap.
- **Swing and long-term horizons only.** No day trading.

## Investor profile

The pipeline works for a specific investor. The profile sets risk tolerance, allowed
horizons, whether shorts are allowed, maximum loss per trade, minimum reward:risk, target
return, whether a stop/target counts as hit on the close or intraday (`level_trigger`),
and free-text preferences. The technical agent plans around it and applies its rules;
the middleware re-checks the numbers.

Copy [`profile.example.json`](profile.example.json) to `workspace/profile.json` and edit
it; without one, the example is used.

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

## Run it now

**In Claude Code on the web** (nothing to install):

1. Open [claude.ai/code](https://claude.ai/code) and start a new session on this
   repository, in a cloud environment that has `EQUIBLES_API_KEY` set as an environment
   variable (and network access to `mcp.equibles.com`). No Anthropic key is needed: the
   agents run on the session's own model access.
2. Type `/run --max-sectors 1 --shortlist 3` (a small run, about 15 minutes), or `/run`
   for every sector the scanner calls.
3. The report appears in the chat and in `workspace/runs/<run_id>/report.md`.
4. Record a decision with `/decide <candidate_id> accept "note"` (or `reject`).

To use your own profile, ask the session to write it to `workspace/profile.json`
before `/run`; otherwise `profile.example.json` is used.

> Each cloud session starts with an empty `workspace/`, so runs, positions and
> decisions from one session are not there in the next. Fine for trying it; for
> follow-up and evaluation over days, run it on your own machine (below) until the
> workspace is persisted.

## Getting started (your own machine)

Requires the [Claude Code](https://code.claude.com) CLI (terminal or desktop app), an
Anthropic API key or a Claude Code login, and an Equibles API key (Plus plan or better:
a full run makes a few hundred data calls).

```bash
git clone https://github.com/ashakir11-dev/trading-platform.git
cd trading-platform
export ANTHROPIC_API_KEY=...   # or be logged in to Claude Code
export EQUIBLES_API_KEY=...
claude          # once: accept the trust dialog and the "equibles" MCP server
```

### Using it

Inside `claude` in the repository:

| Command | What it does |
|---|---|
| `/run --max-sectors 1 --shortlist 3` | A small live run; `/run` for a full one (after the close) |
| `/run-agent <agent> <subject> [--as-of DATE]` | One agent on its own, e.g. `/run-agent company-deep-dive NVDA` |
| `/decide <candidate_id> accept\|reject [note]` | Record your decision; accept opens a watched position |
| `/trade <position_id> entered\|exited <price> [date]` | Record your actual entry or exit |
| `/follow-up` | One follow-up tick over open positions (schedule it) |
| `/evaluate [--run ID] [--agent A]` | Grade past runs; your own decision reviews shown in chat |
| `/feedback <agent>` | Propose lessons from an agent's evaluations |
| `/approve <agent> <proposal_id> [reject]` | Add a lesson to the agent's prompt (a git commit) |
| `/backtest --as-of DATE [...]` | The pipeline as of a past date, with audited data |

Headless (cron):

```bash
CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 \
  claude -p "/run" --model claude-sonnet-5 --effort low \
  --mcp-config .mcp.json --permission-mode acceptEdits
```

Everything a run produces is in `workspace/` (git-ignored): the report in
`workspace/runs/<run_id>/report.md`, each agent's analysis and raw data in
`workspace/agents/<agent>/analyses/<run_id>/`. More in
[`docs/operations.md`](docs/operations.md).

## Data

All data comes from **[Equibles](https://equibles.com)** through its hosted MCP server
(`.mcp.json`). Each agent may call only the read-only tools listed in its definition;
anything Equibles doesn't provide is deferred, not sourced elsewhere. Covered: prices
(returned to agents as computed statistics), sector ETF holdings and screens,
fundamentals, SEC filings and documents, press releases, guidance, estimates, earnings
calls, insider and short data, FDA advisory meetings, macro series, VIX and put/call.
Not covered: third-party news, FDA decision dates, macro vintages.

## Project layout

```
prompts/                  what every agent does
  shared.md, formats.md     rules and file formats for all agents
  <agent>/                  role, default, isolation, evaluation, feedback, lessons
  middleware/               orchestration, report, backtest relay
  gatekeeper/, pit-auditor/ backtest data packs
.claude/
  agents/                   subagent definitions (tools, model, effort)
  commands/                 the slash commands above (the middleware agent)
  hooks/                    decisions firewall, read-only tools, raw-data capture,
                            price statistics, backtest data filter
  settings.json             permissions and hook wiring
.mcp.json                 the Equibles MCP server
workspace/                run data (git-ignored)
tests/                    tests for the hooks
docs/                     architecture, subagent design, operations, research
profile.example.json      example investor profile
```

## Testing

```bash
pip install pytest && pytest
```

Tests cover the hooks: the decisions firewall, the read-only tool rule, raw-data
capture, the price statistics and the backtest data filter.

## Status

**Built and run live:** market scanner, sector deep dive, company deep dive, technical
analysis, middleware and report; a one-stage backtest (gatekeeper → auditor → backtest
agent).

**Built, not yet exercised end to end:** `/follow-up`, `/trade`, `/evaluate`, `/feedback`,
`/approve` (they need accepted positions or runs at least a week old), and a full
four-stage backtest.

**Open:** see [`docs/ARCHITECTURE.md` → Remaining work](docs/ARCHITECTURE.md#remaining-work).

## Disclaimer

This is a research project. Its output is not financial advice, early versions are
expected to be wrong often, and whether the approach makes money is unknown. You are
responsible for every trade you make.
