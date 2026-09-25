# Multi-Agent Trading Pipeline: Architecture

This is the design this codebase implements. Read it before changing any agent,
schema, or the middleware. The original design summary is kept in
[`architecture-summary.html`](architecture-summary.html). This file restates it
and adds the implementation decisions made during scaffolding (see
[Implementation decisions](#implementation-decisions)).

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

| Stage | Module | Runs | Input | Output |
|---|---|---|---|---|
| Agent 0: Market Scanner | `agents/market_scanner.py` | once per run | raw market and sector data | sectors with upside/downside potential |
| Agent 1: Sector Deep Dive | `agents/sector_deep_dive.py` | one per sector, in parallel | sector call + **bulk screen of every company in the sector** (key ratios, size, recent filings/events) + sector breadth, news, FDA, earnings | shortlist of ~10-30 companies, **ranked by potential score** |
| Company Deep Dive | `agents/company_deep_dive.py` | one per company, in parallel | shortlist entry + market/sector data + **full company data** (fundamentals, filings, company news) | worthiness verdict; catalysts checked |
| Technical Analysis | `agents/technical_analysis.py` | one per company, in parallel, **no cross-comparison** | candidate + **investor profile** + price/indicator/pivot data **for each chart timeframe the investor's horizons need** + earnings calendar | chart verdict + entry / exit / stop-loss / horizon / chart timeframe, or rejection; then **deterministic rules** check the plan |
| Middleware | `middleware.py` | orchestrates | | report to the user |
| Agent 5: Follow-Up | `agents/follow_up.py` | on a schedule, per accepted position | position + investor profile + fresh data | cheap tripwire checks (price vs stop/target, **material** news only) with a **12h alert cooldown**, plus a deep full re-review on alert or at an interval |
| Outcomes Agent | `agents/outcomes.py` | per closed/marked position | price history | financial results only; **deterministic, no LLM, no judgment** |
| Process Agent | `agents/process_review.py` | per position | every stage's reasoning trail + outcome | per-stage reasoning-quality grades, foreseeable-risk check, improvement signals |

## 3. Design principles (non-negotiable)

1. **Sequential between stages, parallel and independent within a stage.** Each
   candidate gets its own unbiased pass. The technical stage never compares
   candidates with each other.
2. **Raw-data pass-through.** Each agent receives the prior agent's report
   **and** the raw data behind it, so a bad upstream filter can't fully blind
   the next stage. In code, every stage input carries the upstream report plus a
   `RawDataBundle`. Stages add to the bundle as it moves forward. **Scope:** a
   company's prompts carry market-level data plus everything about that company and
   its sector, but not other companies' rows (`RawDataBundle.filter`). Nothing about
   the company itself is ever dropped.
3. **Two independent filters.** Fundamental worthiness and technical
   tradeability are uncorrelated. Rejecting a fundamentally strong company on
   chart grounds is a normal outcome, not an error.
4. **Structured reasoning, not just verdicts.** Every agent logs what pushed it
   toward or away from its conclusion (`StageReasoning`). This log is the
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

**Investor profile** (`profile.py`, `PipelineConfig.profile`, example in
`profile.example.json`): who the pipeline works for, including risk tolerance, allowed
holding horizons, whether shorts are allowed, maximum loss per trade, minimum
reward:risk, target return, how stop/target hits are detected (`level_trigger`), and
free-text notes. It is the user's *preferences*, set up
front, not a decision, so showing it to agents does not break the one-way middleware
principle. The technical agent and Agent 5's full review read it, and the rules
enforce it.

**Horizons and chart timeframes.** Each horizon has its own charts; the technical
agent reads levels from the primary chart and trend from the context chart, and the
middleware fetches every timeframe the profile's horizons need.

| Horizon | Typical hold | Primary chart | Context chart | Earnings flag window |
|---|---|---|---|---|
| `short_term` | days to ~2 weeks | 1h, 30 days | 1d, 6 months | 14 days |
| `swing` | weeks to ~3 months | 1d, 1 year | 1w, 2 years | 45 days |
| `long_term` | months to years | 1w, 5 years | 1d, 1 year | 30 days |

Day trading is **not** supported: it conflicts with principle 7 (intraday data goes
stale while the pipeline runs). Adding it would need a decision to change that principle.

**Deterministic rules** (`rules.py`). Rules never make judgment calls: they catch
mechanical errors, enforce the profile and flag known risks. Every result is logged on
the stage record (`StageRecord.rules`), so the process agent can tell a rule veto from a
judgment failure. `reject` removes the candidate; `flag` warns the user in the report.

| Rule | Outcome | When |
|---|---|---|
| `plan_price_order` | reject | long needs stop < entry < target; short the reverse |
| `profile_horizon` | reject | plan horizon not in the profile's horizons |
| `chart_timeframe` | flag | plan levels not read from the horizon's primary chart |
| `profile_short` | reject | short plan (or downside sector call at Agent 1) when shorts are not allowed |
| `max_loss` | reject | stop further from entry than `max_loss_per_trade_pct` |
| `reward_to_risk` | reject | reward:risk below `min_reward_to_risk` |
| `stale_entry` | reject | price already more than `stale_entry_max_drift_pct` (3%) past the entry, or through the stop. Live runs use the live quote; backtests use the last close at `as_of`. A price that hasn't reached the entry yet is fine. |
| `upcoming_earnings` | flag | earnings inside the horizon's window, or the date is unknown |

**Conflicts** (`Conflict`, `PipelineReport.conflicts`): when the same ticker comes from
more than one sector call, it is **always recorded**, as `direction_conflict` (opposite
directions) or `duplicate`. The first surfacing advances; the record is stored and shown
in the report.

**Stop and target hits** follow the profile's `level_trigger`: `close` (default) counts
a hit only when a bar *closes* beyond the level; `intraday` counts it as soon as the bar's
low/high touches it. Agent 5's alerts and the outcomes agent share one function
(`rules.levels_hit`), so they always agree.

**Alerts** (Agent 5). A tripwire fires on price hitting the stop or target (per
`level_trigger`), or on **material** news. `rules.is_material` keeps SEC 8-Ks with material
items (e.g. 1.01, 2.02, 5.02), earnings, guidance, FDA, M&A, rating changes, offerings,
legal and leadership news, and drops price-action chatter, reiterations and listicles.
Each alert triggers a full re-review. After an alert, further alerts for the same
position are **held for 12 hours** (`alert_cooldown`). Anything that trips meanwhile is
recorded and delivered with the next alert, so nothing material is lost.

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
| Duplicate decisions | **Blocked.** A second accept/reject for the same candidate raises an error. |
| Cost | Not a concern for now; no budgets or caching work yet. |

**Open:**

- **Backtesting and forward (paper) testing.** Being researched: what options, tools,
  apps and plugins exist (see `testing-research.md` once written). Known constraints:
  only dates after every model's training cutoff are honest evidence; prices should be
  survivorship-free and fundamentals point-in-time; a simulated decision policy must be
  stored apart from real user decisions; any broker paper-trading integration would
  relax the no-orders rule and needs an explicit decision.

**Future enhancements (not planned now):**

- **Day trading** as a horizon (would need principle 7 changed).
- **More rules:** liquidity floor, sector concentration across recommendations.
- **Own snapshots of scheduled-event calendars** (earnings, FDA). Not needed if Equibles
  keeps the dates *as they were expected at the time*; worth revisiting if backtests
  show it doesn't.
- **Cost controls:** token/cost tracking, per-run budgets, prompt caching, condensing
  long price histories in prompts.
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

**Vendor: Equibles** (hosted MCP at `https://mcp.equibles.com/mcp`, plus REST). Anything
it doesn't provide is **deferred**. Agents still depend only on the provider interfaces
in `data/base.py`, so this stays swappable.

| Need | Equibles source | Adapter | Notes |
|---|---|---|---|
| Company fundamentals | `GetFinancialFact` (SEC XBRL with filing dates) | **Built** (`EquiblesFundamentals`) | Point-in-time; see below |
| Daily price history | `GetStockPrices` | To build | Weekly bars derived from daily. History comes from Yahoo (self-hosted docs); delisted coverage unconfirmed |
| Intraday (1h) bars, live quotes | Paid plans (Plus: 15-min delayed, Pro: real-time) | To build | Needed for `short_term` and the stale-entry check |
| Indicators, support/resistance | Equibles has Bollinger, Stochastic, ATR, OBV | To build | Other indicators and pivots computed locally from Equibles prices |
| Sector screen | Cloud screener | To build | Tool reference needed |
| Sector breadth | Derived from Equibles prices + industry classification | To build | |
| SEC filings / 8-Ks | `ListFilings`, `SearchDocuments` | To build | Main catalyst and alert source; 8-K items feed the news filter |
| FDA | `GetFdaAdvisoryCommitteeMeetings` | To build | Advisory meetings only; PDUFA dates **deferred** |
| Macro | FRED tools (`GetEconomicIndicator`, ...) | To build | Latest revised values only; point-in-time vintages **deferred** |
| Earnings calendar | Unconfirmed | To confirm | Deferred if not provided |
| Earnings transcripts, guidance | Cloud plans | Later | Useful for the company deep dive |
| General news headlines | Not provided | **Deferred** | Filings stand in for news |
| Analyst ratings | Not provided | **Deferred** | |

**Fundamentals connector:** for each concept it asks `GetFinancialFact` for both the
originally reported and the latest restated values, each carrying its filing date, and
keeps only rows filed on an earlier US/Eastern day than `as_of`. For each period the latest
such filing wins, so a restatement counts only after it was filed. (Only a middle
restatement of a period restated twice can be missed.) Caveats:
- Equibles adjusts per-share values to today's share basis. In backtests that reveals
  future splits, so those values are dropped and noted.
- The hosted tool resolves tickers to today's company, so a reused ticker can point at the
  wrong company in old backtests. The payload names the company so this is visible.
- 2 calls per concept (28 per ticker by default), so real runs need the Plus plan.
`EquiblesPostgresFundamentals` is the exact, self-hosted alternative.

Background research that led here: [`data-sources-research.md`](data-sources-research.md),
[`live-prices-research.md`](live-prices-research.md),
[`equibles-evaluation.md`](equibles-evaluation.md).

Gaps are modeled as provider interfaces with `Unavailable*` implementations.
Their snapshots carry `is_gap=True`, so agents are told the data is missing
rather than silently seeing nothing, and the process agent can separate "bad
reasoning" from "no data".

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

## Implementation decisions

Choices made while scaffolding. Each one is easy to revisit.

| Topic | Decision | Where |
|---|---|---|
| Language / LLM | Python 3.11+, the official `anthropic` SDK, structured outputs via `client.beta.messages.parse` with Pydantic models, adaptive thinking, server-side refusal fallbacks (`fallbacks="default"`). Model and effort are set in config. | `llm.py`, `config.py` |
| Agent 1 format (**decided: ranked**) | The schema records **both** a `potential_score` (0-100) and a `passed` flag per company, so both are always logged. `PipelineConfig.shortlist_mode` defaults to `"ranked"`; `"pass_fail"` remains available. | `schemas.py`, `middleware.py` |
| Confidence score (**decided: attribution only**) | Every stage emits a 0-1 `confidence` for each candidate. It is stored as a trajectory on the `Candidate` (`confidence_trajectory`) and used for attribution. **It gates nothing by default** (`confidence_gate=None`), and **downstream agents don't see upstream confidence numbers by default** (`show_upstream_confidence=False`) to avoid anchoring. | `schemas.py`, `middleware.py` |
| Agent 1 bulk screen | `SectorDataProvider.sector_screen` returns one `screen` snapshot per company (subject = ticker). The company deep dive filters the sector bundle to market + sector + its own ticker before adding full company data. | `data/base.py`, `middleware.py` |
| Investor profile & rules | `InvestorProfile` in config; `rules.py` holds all deterministic checks as pure functions; results are logged per stage record and shown as flags in the report. | `profile.py`, `rules.py`, `middleware.py` |
| Alerts | Material-news filter plus 12h per-position cooldown with held reasons delivered later. | `rules.py`, `agents/follow_up.py` |
| Point-in-time data | Every provider call takes `as_of`. `RawDataBundle.add` rejects a snapshot dated after the run's `as_of`, which guards against look-ahead in backtests. | `data/base.py` |
| Data access | The middleware fetches data through provider interfaces, not the agents. All adapters are Equibles (§6). MCP calls go through `HttpMcpClient`, which only calls allowlisted tools. Any quotes/account adapter must have **no order methods**. | `data/base.py`, `data/mcp.py`, `data/equibles.py` |
| User decisions | Stored in a separate table. `Store.review_trail()` (what the process agent reads) never includes them. One decision per candidate; a second is rejected. | `store.py`, `middleware.py` |
| Outcomes agent | Plain deterministic code, no LLM, so "no judgment" holds by construction. | `agents/outcomes.py` |
| Process → Agent 0 improvement | Improvement signals are stored as `ImprovementNote`s with `approved=False`. Only human-approved notes are injected into stage prompts. This guards against the loop overfitting to recent outcomes. | `agents/process_review.py`, `agents/base.py` |
| Follow-up scheduling | Agent 5 exposes `tick(now)`. Every tick runs the cheap tripwire check; a full re-review runs when an alert is raised (subject to the 12h cooldown) or `full_review_interval` has passed. An external scheduler (cron, etc.) calls it. | `agents/follow_up.py` |

## Remaining work

**Blocking a first real run (all Equibles adapters, §6):**
1. Prices: daily history, intraday bars, live quotes, plus locally computed indicators
   and support/resistance levels.
2. Sector screen and derived sector breadth (Agent 1's input).
3. Filings/8-Ks as the catalyst and alert source; FDA advisory meetings; earnings
   calendar if Equibles has one.
4. A way to run and operate the system: CLI for runs, decisions, closing positions,
   reviews and approving improvement notes, plus a scheduled Agent 5 tick.

**Design gaps to close:**
5. Macro data: no agent receives any yet, although agents are told to weigh macro
   exposure and the process agent penalizes missing it. Add a macro interface fed by
   Equibles' FRED tools.
6. Filings interface for the company deep dive (the design lists filings as its input).
7. Agent 1 input: add FDA/earnings events for the sector (design lists them).
8. `holdout_start` is defined but unused (belongs to the testing harness).
9. The look-ahead guard checks snapshot dates, not payload contents: every real adapter
   needs tests proving it filters by `as_of`.
10. Agent 5 could prompt the user to close and review a position when a stop or target
    is hit (today closing and reviewing are manual).

**Research in progress:** backtesting and forward-testing options (§5).

**Future enhancements:** see §5.
