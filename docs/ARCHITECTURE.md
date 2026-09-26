# Multi-Agent Trading Pipeline: Architecture

This is the design the pipeline implements: its principles, rules and decisions. Read
it before changing any agent, prompt or command. **How** it is implemented (Claude
Code subagents, prompts, hooks, the workspace) is in
[`prompt-subagents-design.md`](prompt-subagents-design.md). The original design summary
is kept in [`architecture-summary.html`](architecture-summary.html).

All market data comes from **Equibles** (see §6). It is a
**research and decision-support system**. It never places orders. A human makes
every go/no-go call.

## 1. Overview

The pipeline is a chain of independent agents. Each one handles one stage of
trade research and feeds the next stage. Agents within a stage run in parallel,
one per candidate and independently, to avoid correlated bias. Every agent
outputs structured reasoning with its verdict, not just pass/fail, so the
retrospective feedback loop can trace where judgment broke down.

```mermaid
flowchart TD
    A0["Agent 0 - Market Scanner<br/>market → sectors with upside/downside potential"]
    A1["Agent 1 - Sector Deep Dive<br/>per sector → shortlist of ~10-30 companies"]
    A2["Company Deep Dive<br/>per company → worthiness, scrutinize catalysts"]
    A3["Technical Analysis<br/>per company → chart viability, entry/exit/stop, can reject"]
    MW["Middleware<br/>reports to user; user makes the real call"]
    A5["Agent 5 - Follow-Up Loop<br/>tripwires + periodic full re-review"]
    OUT["Outcomes Agent<br/>real financial results, no judgment"]
    PROC["Process Agent<br/>reasoning quality per stage, incl. foreseeable risk"]

    A0 -->|sectors + raw data| A1
    A1 -->|shortlist + raw data| A2
    A2 -->|survivors + raw data| A3
    A3 -->|surviving picks| MW
    MW -->|accepted positions| A5
    A5 -.-> OUT
    A5 -.-> PROC
    A0 & A1 & A2 & A3 -.reasoning log.-> PROC
    OUT -.-> PROC
    PROC -.improvement signal.-> A0
```

Step-by-step runtime flow (sequence diagrams): [`sequence-diagrams.md`](sequence-diagrams.md).

## 2. Stage responsibilities

| Stage | Agent (prompts in `prompts/<agent>/`) | Runs | Input | Output |
|---|---|---|---|---|
| Agent 0: Market Scanner | `market-scanner` | once per run | sector ETF performance + macro data | sectors with upside/downside potential |
| Agent 1: Sector Deep Dive | `sector-deep-dive` | one per sector, in parallel | sector call + **bulk screen of the sector's companies** (ratios, size, prices, recent filings/events) + breadth, FDA, earnings | shortlist **ranked by potential score** |
| Company Deep Dive | `company-deep-dive` | one per company, in parallel | shortlist entry + market/sector/macro data + **full company data** (fundamentals, filings, guidance, estimates, transcripts, insider and short data) | worthiness verdict; catalysts checked |
| Technical Analysis | `technical-analysis` | one per company, in parallel, **no cross-comparison** | candidate + **investor profile** + price statistics, swing levels and weekly bars for the trade type's charts + earnings dates to the max hold | chart verdict + a **time-bound plan** (trade type, setup, entry and tranches, stop, targets with scale-out, trailing stop, entry expiry, checkpoints, max hold, event plan), or rejection; then the **profile's rules** |
| Middleware | the commands in `.claude/commands/` | orchestrates | | report to the user; records the user's decisions |
| Agent 5: Follow-Up | `follow-up` | on a schedule, per accepted position | position + profile + fresh data + every earlier analysis | tripwire checks (entry, stop, targets, trailing stop, checkpoints, max hold, events; **material** news with a **12h cooldown**), plus a full re-review on alert or on the trade type's cadence |
| Evaluation | `stage-evaluator` | per agent and past run | the agent's analyses + prices since | **outcome facts** (no judgment), then **reasoning-quality grades** with an attribution per miss |
| Feedback | `stage-feedback` | per agent, on request | the agent's evaluations | proposed lessons; added to prompts only after the user approves |

## 3. Design principles (non-negotiable)

1. **Sequential between stages, parallel and independent within a stage.** Each
   candidate gets its own unbiased pass. The technical stage never compares
   candidates with each other.
2. **Raw-data pass-through.** Each agent receives the prior agent's report
   **and** the raw data behind it, so a bad upstream filter can't fully blind
   the next stage. Every Equibles response an agent receives is saved to its analysis
   folder's `raw/`, and the next agent reads the upstream analysis and its `raw/`.
   **Scope:** a company's agents read market-level data plus everything about that
   company and its sector, but not other companies' files. Nothing about the company
   itself is ever dropped.
3. **Two independent filters.** Fundamental worthiness and technical
   tradeability are uncorrelated. Rejecting a fundamentally strong company on
   chart grounds is a normal outcome, not an error.
4. **Structured reasoning, not just verdicts.** Every agent logs what pushed it
   toward or away from its conclusion (factors with evidence, risks weighed, data gaps,
   confidence; `prompts/shared.md`). This log is the
   backbone of the feedback loop.
5. **The middleware reports in one direction only.** It reports pipeline output
   to the user. The user's manual accept/reject **never** feeds back into the
   system as if it were the system's own judgment. User decisions are stored
   apart from stage records, and the process agent cannot read them. The
   decision only controls whether a position enters the follow-up watch list.
6. **Split meta-review.** The outcomes agent (pure P&L, no judgment) and the
   process agent (reasoning quality) are decoupled. A well-reasoned trade that
   loses to a genuine black swan must not be penalized like a missed,
   foreseeable risk such as macro exposure.
7. **Swing or long-term horizons only, never day trading.** Cross-stage data
   staleness is therefore not a concern.

## 4. Investor profile, horizons and rules

**Investor profile** (`workspace/profile.json`, example in `profile.example.json`): who the pipeline works for, including risk tolerance, allowed
holding horizons, whether shorts are allowed, maximum loss per trade, minimum
reward:risk, target return, how stop/target hits are detected (`level_trigger`), and
free-text notes. It is the user's *preferences*, set up
front, not a decision, so showing it to agents does not break the one-way middleware
principle. The technical agent and Agent 5's full review read it, and the rules
enforce it.

**Trade types, horizons and chart timeframes.** The profile allows *horizons*; the
technical agent picks one of four *trade types* within them. Each has its own charts and
clocks; the agent reads levels from the primary chart and trend from the context chart.
Sessions are NYSE trading days (1 week = 5 sessions).

| Trade type | Typical hold | Horizon | Primary chart | Context chart | Entry valid | Max hold | Re-review every |
|---|---|---|---|---|---|---|---|
| `short_swing` | 3-15 sessions | `swing` | 1d, 6 months | 1w, 1 year | 5 sessions | 15 sessions | 3 sessions |
| `swing` | 2-8 weeks | `swing` | 1d, 1 year | 1w, 2 years | 10 sessions | 40 sessions | 5 sessions |
| `long_swing` | 2-6 months | `swing` if max hold ≤ 65 sessions, else `long_term` | 1w, 2 years | 1w, 5 years | 20 sessions | 130 sessions | 10 sessions |
| `investment` | 6 months and more | `long_term` | 1w, 5 years | 1M, 10 years | 40 sessions | 260 sessions | 20 sessions |

**No trade is open-ended.** Every plan carries an entry expiry (`entry_valid_until`),
progress checkpoints (sessions after the fill, each with the action if it fails), a max
hold (exit at that close; only a new plan extends it) and an event plan for every
earnings report up to the max hold. Targets are one to three levels with the fraction
sold at each; what is left after them rides a trailing stop. Mean-reversion setups
exit fully at T1. The research behind the defaults is in
`prompts/technical-analysis/playbook/` (not read by the agent).

Day trading is **not** supported: it conflicts with principle 7 (intraday data goes
stale while the pipeline runs). Adding it would need a decision to change that principle.

**Rules** (`prompts/technical-analysis/role.md`). Rules never make judgment calls: they
catch mechanical errors, enforce the profile and flag known risks. The technical agent
applies every rule to its own plan and records each result with its numbers, and the
middleware recomputes price order, max loss and reward:risk before recommending (a
mismatch blocks the recommendation). The evaluator can therefore tell a rule veto from
a judgment failure. `reject` removes the candidate; `flag` warns the user in the report.

| Rule | Outcome | When |
|---|---|---|
| `plan_price_order` | reject | long needs stop < entry < T1 < T2 < T3 (tranches above the stop); short the reverse |
| `profile_horizon` | reject | the trade type's horizon not in the profile's horizons |
| `chart_timeframe` | flag | plan levels not read from the trade type's primary chart |
| `profile_short` | reject | short plan when shorts are not allowed; downside sector calls are then not pursued |
| `max_loss` | reject | stop further from entry than `max_loss_per_trade_pct`, in any tranche fill state |
| `reward_to_risk` | reject | reward:risk to **T1** below `min_reward_to_risk`, in any tranche fill state |
| `scale_out` | reject | exit fractions not > 0 or summing past 1; a remainder without a trailing stop; a mean-reversion setup keeping a runner |
| `stale_entry` | reject | price through the stop, or past the entry and either above the **stale cap** (the highest fill at which max loss and reward:risk still pass) or further than the trade type's ATR distance (0.5-1 ATR). Live runs use the live quote; backtests use the last close at `as_of`. A price that hasn't reached the entry yet is fine. |
| `time_limits` | reject | entry expiry, checkpoints or max hold missing or beyond the trade type's limits, or expected time to T1 above ⅔ of the max hold |
| `reachability` | reject | T1 too far for the time: (T1 − entry) / (0.63 × ATR × √max-hold) > 1.5 |
| `liquidity` | reject | `short_swing`/`swing` with 20-day average dollar volume below $5M |
| `upcoming_earnings` | flag / reject | reject a report before the max hold with no event-plan entry, or any report inside a `short_swing` hold; otherwise flag each report up to the max hold and any unknown or estimated date |

**Conflicts:** when the same ticker comes from
more than one sector call, it is **always recorded**, as `direction_conflict` (opposite
directions) or `duplicate`. The first surfacing advances; the record is stored and shown
in the report.

**Stop and target hits** follow the profile's `level_trigger`: `close` (default) counts
a hit only when a bar *closes* beyond the level; `intraday` counts it as soon as the bar's
low/high touches it. The follow-up agent and the evaluator use the same definition.

**Alerts** (Agent 5). Tripwires fire on price (entry triggered, missed or expired; the
stop in force; each target; the trailing stop; the next tranche), on clocks (a failed
checkpoint, the max hold, an event-plan date two sessions ahead) and on **material**
news. The follow-up agent keeps SEC 8-Ks with material items (e.g. 1.01, 2.02, 5.02),
earnings, guidance, FDA, M&A, rating changes, offerings, legal and leadership news, and
drops price-action chatter, reiterations and listicles. Price and clock alerts carry an
action on a price or a date and are **always delivered at once**. After a delivered news
alert, further news alerts for the same position are **held for 12 hours**, recorded,
and delivered with the next alert, so nothing material is lost. Each delivered alert
triggers a full re-review; otherwise the re-review runs on the trade type's cadence. A
re-review never extends a losing trade's time or risk: a longer max hold or a wider stop
is a new plan, checked against every rule from the current price.

## 5. Design decisions

**Decided (2026-09-25):**

| Decision | Choice | Why |
|---|---|---|
| Agent 1 output format | **Ranked by potential score (0-100)**; passing companies are forwarded best-first, capped per sector. Pass/fail is still recorded. | Gives the feedback loop a gradient ("scored 85 and failed" teaches more than "passed and failed") and lets later stages triage. |
| Running confidence score | **Attribution only.** Recorded at every stage as a trajectory; gates nothing; hidden from downstream agents. | Traces where doubt entered without anchoring later agents or trusting uncalibrated scores. Revisit gating once testing shows calibration. |
| Agent 1 data | **Bulk screen at Agent 1, deep data later.** Agent 1 screens every company in the sector from cheap bulk data; full per-company fundamentals are fetched only for the shortlist. | Full fundamentals for a whole sector cost ~28 Equibles calls per company. |
| Raw-data pass-through scope | **Relevant subset**: market + sector + the company's own data. | Keeps the principle (no stage blinded by an upstream filter) at a fraction of the token cost of repeating every company's data in ~30 prompts. |

**Decided (2026-09-25, second round):**

| Decision | Choice |
|---|---|
| Data vendor | **Equibles for all data.** Anything Equibles doesn't provide is deferred, not sourced elsewhere. |
| Stop/target definition | **Customizable in the investor profile** (`level_trigger`: `close` or `intraday`), shared by alerts and outcomes. |
| Duplicate decisions | **Blocked.** A second accept/reject for the same candidate is refused. |
| Cost | Not a concern for now; no budgets or caching work yet. |

**Decided (2026-09-25/26, the subagent build):**

| Decision | Choice |
|---|---|
| Architecture | **Prompt-based Claude Code subagents** that fetch their own data; the Python pipeline was removed on 2026-09-26. Details, and decisions D0-D5, in [`prompt-subagents-design.md`](prompt-subagents-design.md). |
| Your trade in evaluation (D0) | Evaluation grades agents against the market; the comparison with your decisions goes to `decisions/reviews/` and is shown to you only, never to an agent. |
| Backtests (D1) | A gatekeeper agent builds point-in-time data packs, an auditor checks them, and backtest agents have no data tools. |
| Rules and outcomes (D3) | In prompts; the middleware recomputes the plan arithmetic. |
| Forward testing | Every live run is graded by the evaluators as outcomes arrive, including candidates nobody traded: the "shadow ledger" of [`testing-research.md`](testing-research.md), Phase 0. |
| Models (D5, revisited) | Per agent, in `.claude/agents/` (design doc §11). |

**Decided (2026-09-26, time-bound plans):**

| Decision | Choice |
|---|---|
| Trade types | **Four trade types** (`short_swing`, `swing`, `long_swing`, `investment`) inside the profile's `swing` / `long_term` horizons, each with its charts and clocks. |
| Plan format | Trade type, setup label, optional entry tranches, **one to three targets with exit fractions** and a trailing stop for the rest, entry expiry, checkpoints, max hold and an event plan. `reward_to_risk` is checked on T1. |
| Rules | `stale_entry` uses the plan's stale cap and an ATR distance instead of a fixed 3%; `upcoming_earnings` scans to the max hold; new `scale_out`, `time_limits`, `reachability` and `liquidity` rules. The middleware recomputes all the arithmetic ones. |
| Follow-up | Price and clock alerts bypass the 12h cooldown (news only); re-review cadence by trade type; positions record partial fills and exits (`/trade ... [fraction]`). |
| Evaluation | Plans are walked forward as written: entries expire, targets and trailing stops exit their fractions, checkpoints act, and whatever is left closes at the max hold as a time exit with realised R; graded by setup and trade type. |

**Open:**

- **Plan margins.** Recommendations have repeatedly sat right at the profile's limits
  (e.g. max loss 7.8% vs 8%, reward:risk 2.03 vs 2.0). Whether plans should keep a
  margin from the limits is the user's call.
- **Broker paper trading** would relax the no-orders rule and needs an explicit decision.

**Future enhancements (not planned now):**

- **Day trading** as a horizon (would need principle 7 changed).
- **More rules:** liquidity floor, sector concentration across recommendations.
- **Own snapshots of scheduled-event calendars** (earnings, FDA). Not needed if Equibles
  keeps the dates *as they were expected at the time*; worth revisiting if backtests
  show it doesn't.
- **Cost controls:** token/cost tracking and per-run budgets.
- **Real-model evaluation:** test prompt quality against the real model with an
  evaluation set, once the system is complete.

## 6. Data requirements

Every category needs a **live** version (to run the system) and a **deep
historical, point-in-time** version (to backtest it honestly):

- Price and volume
- Sector-level performance and breadth
- News and catalyst events (earnings, FDA, analyst actions)
- Company fundamentals (financials, filings, ownership, valuation)
- Macro data (rates, inflation, FX), for the foreseeable-risk checks

**Vendor: Equibles** (hosted MCP at `https://mcp.equibles.com/mcp`, configured in
`.mcp.json`). Anything it doesn't provide is **deferred**. Each agent may call only the
read-only tools listed in its definition (`.claude/agents/`); the account tools
(portfolios, lots, watches, reports) are denied for everyone.

| Need | Equibles tools | Used by | Notes |
|---|---|---|---|
| Daily prices, indicators, support/resistance | `GetStockPrices` (daily only, ≤500 rows per call), `GetAverageTrueRange`, `GetBollingerBands`, `GetStochasticOscillator`, `GetOnBalanceVolume` | scanner, sector, technical, follow-up, evaluator | For the scanner, sector and technical agents a hook replaces each price response with computed statistics (returns, 20/50/200-day averages, 52-week range, ATR14, dollar volume; swing levels and weekly bars for the technical agent). A bar counts from 16:00 New York on its date. **Backtest caveat:** Equibles restates history after each split and exposes no split events, so past absolute levels reflect later splits (percent moves are unaffected). |
| Quotes | `GetLiveQuote`, `GetLatestClosingPrices` | technical, follow-up | Live quote on Plus (15-min delayed) or Pro; last close otherwise. Never in backtests. |
| Sector performance | `GetStockPrices` on SPY + the 11 sector ETFs | scanner | |
| Sector constituents, screen and breadth | `GetEtfHoldings`, `ScreenStocks` (up to 200 tickers per call), `GetValuationMultiples`, `GetStockPrices` | sector | Constituents = the sector ETF's top 25 holdings, usable once public (period + 60 days). Only the latest holdings report is served, so older backtests get a gap (or survivorship-biased current holdings). |
| Fundamentals | `GetFinancialFact`, `GetFinancialStatement`, `GetValuationMultiplesHistory` | company | A figure counts from the day after its filing; as-reported values preferred. Per-share values are on today's share basis (dropped in backtests). |
| Filings and documents | `ListFilings`, `SearchDocument`, `ReadDocumentLines` | sector, company, follow-up | 10-K/10-Q/8-K; 8-K item numbers say what happened. |
| Company news and events | `GetInvestorRelationsNews`, `GetUpcomingInvestorEvents`, `GetFdaAdvisoryCommitteeMeetings` | sector, company, follow-up | Press releases from IR sites (partial coverage); announced earnings dates (live only); FDA advisory meetings visible 15 days ahead. |
| Expectations | `GetGuidance`, `GetAnalystEstimates`, `GetEarningsCallTranscript` | company | Estimates are "now only" (never in backtests). |
| Ownership and risk | `GetInsiderTransactions`, `GetShortInterest`, `GetDebtProfile`, `GetGoingConcernStatus` | company | |
| Macro | `GetEconomicIndicator`, `GetLatestEconomicIndicators`, `GetEconomicCalendar`, `GetVixHistory`, `GetPutCallRatios` | scanner (others read its `raw/`) | 13 FRED series; a value counts after its period ends plus the publication lag. Latest-revised values (no vintages). |
| Third-party news, PDUFA dates, macro vintages, FOMC dates | Not provided | | **Deferred** |

Backtests replace direct access with the gatekeeper's data packs; the per-tool
point-in-time rules are in `prompts/gatekeeper/role.md`.

Background research that led here: [`data-sources-research.md`](data-sources-research.md),
[`live-prices-research.md`](live-prices-research.md),
[`equibles-evaluation.md`](equibles-evaluation.md).

**Gaps are explicit.** A tool that fails or returns nothing is recorded as
`UNAVAILABLE`, and data an agent was asked for but didn't fetch as `NOT CHECKED`, so the
evaluator can separate "bad reasoning" from "no data".

## 7. Overall assessment (from the design discussion)

- The architecture is sound. Whether it makes money is **unknown and must not
  be assumed**. The design's value is that it is honest and falsifiable.
- **Overfitting risk:** keep a held-out validation period that the system was
  never tuned against (`PipelineConfig.holdout_start`). Weight the process
  agent's reasoning-quality signal, not only outcomes.
- **The model already knows the past.** Any backtest dated before an LLM's training
  cutoff can leak outcomes that no point-in-time data fixes. Only results from dates
  after the training cutoff of every model used count as honest evidence, so set
  `holdout_start` accordingly.
- Expect early versions to be mediocre or to lose money. That is the system
  surfacing weak reasoning.

## Implementation

Implemented as Claude Code subagents: see
[`prompt-subagents-design.md`](prompt-subagents-design.md) for the layout (prompts,
subagents, commands, hooks, workspace), how each principle above is enforced, the
backtest mode and the per-agent models, and [`operations.md`](operations.md) for
running it.

## Remaining work

**Built and run live:** the four research stages, the middleware and report, the
decisions firewall and raw-data capture (hooks), price statistics, a one-stage backtest.

**Built, not yet exercised end to end:** follow-up (`/follow-up`, `/trade`), evaluation
and feedback (`/evaluate`, `/feedback`, `/approve`), a full four-stage backtest.

**Still open:**
- **Plan margins** (§5).
- **Sector screen stability:** the sector agent's ranking moved between runs at low
  effort (e.g. NVDA scored 88, 88, then 71); consider medium effort.
- **News filter for biotech 8-Ks** filed under items 7.01/8.01 (the follow-up agent reads
  the text, but the rule is untested).

**Future enhancements:** see §5.
