# Multi-Agent Trading Pipeline: Architecture

This is the design this codebase implements. Read it before changing any agent,
schema, or the middleware. The original design summary is kept in
[`architecture-summary.html`](architecture-summary.html). This file restates it
and adds the implementation decisions made during scaffolding (see
[Implementation decisions](#implementation-decisions)).

The design started as an extension of the dual-MCP stock agent (Massive.com + Robinhood),
but **those providers are not locked in** (see §6). It is a
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
reward:risk, target return, and free-text notes. It is the user's *preferences*, set up
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

**Alerts** (Agent 5). A tripwire fires on price crossing the stop or target (on the
daily close), or on **material** news. `rules.is_material` keeps SEC 8-Ks with material
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

**Open:**

- **Backtesting and forward (paper) testing.** Deferred. Known constraints for when we
  pick it up: only dates after every model's training cutoff are honest evidence;
  prices must be survivorship-free and fundamentals point-in-time; a simulated decision
  policy must be stored apart from real user decisions; any broker paper-trading
  integration would relax the no-orders rule and needs an explicit decision.
- **Day trading** as a horizon: needs a decision to change principle 7.
- **Stop definition:** Agent 5 alerts on the daily *close* crossing the stop, while the
  outcomes agent counts a stop as hit on the intraday *low*. These should be unified.
- **Proposed rules:** liquidity floor, sector concentration across recommendations.
- **Proposed, not decided:** keep our own daily snapshots of scheduled-event calendars
  (earnings, FDA), since no affordable source records past expected dates; and add new
  8-K filings (e.g. items 2.02, 5.02, 1.01) as an Agent 5 tripwire.

## 6. Data requirements

Every category needs a **live** version (to run the system) and a **deep
historical, point-in-time** version (to backtest it honestly):

- Price and volume
- Sector-level performance and breadth
- News and catalyst events (earnings, FDA approvals, analyst actions)
- Company fundamentals (financials, filings, ownership, valuation)

**Providers are not decided.** Massive.com and Robinhood are what the original
stock agent used, and they are the current *candidates*, not requirements. We are free
to choose better sources per category. Because each category sits behind its own
provider interface (`data/base.py`), switching providers means writing one adapter,
with no changes to the agents.

**Candidate coverage today (from the original stock agent):**
- Massive.com MCP: historical OHLCV, technical indicators, pivot
  support/resistance. Would feed the Technical Analysis agent.
- Robinhood MCP: live quotes, account data, positions. Would feed the middleware's
  visibility layer. **Read-only use only.**

**Research:** [`data-sources-research.md`](data-sources-research.md) compares vendors
across every category and recommends a stack. No stack has been chosen yet. [`live-prices-research.md`](live-prices-research.md)
compares live-price options in more depth. [`equibles-evaluation.md`](equibles-evaluation.md)
evaluates Equibles (self-hosted SEC/FRED/FDA data and cheap Cloud prices).

**Chosen so far:**
- **Fundamentals: Equibles, hosted MCP** (`data/equibles.py`, `EquiblesFundamentals`),
  at `https://mcp.equibles.com/mcp` with an API key. No database to run. For each concept
  it asks `GetFinancialFact` for both the originally reported and the latest restated
  values, each carrying its filing date, and keeps only rows filed on an earlier
  US/Eastern day than `as_of`. For each period the latest such filing wins, so a
  restatement counts only after it was filed. (Only a middle restatement of a period
  restated twice can be missed.) Two caveats:
  - Equibles adjusts per-share values to today's share basis. In backtests that
    reveals future splits, so those values are dropped and noted.
  - The hosted tool resolves tickers to today's company, so a reused ticker can point
    at the wrong company in old backtests. The payload names the company so this is
    visible.
  Budget: 2 calls per concept (28 per ticker by default), so real runs need the Plus
  plan (10,000 calls/day). `EquiblesPostgresFundamentals` is the exact, self-hosted
  alternative (reads Equibles' Postgres, resolves tickers by listing dates).

**Criteria for choosing providers:**
- **Point-in-time history.** Data must be retrievable as it was known on a past
  date, for honest backtests. This matters most for news/catalysts and
  fundamentals (restatements).
- **Survivorship-free universes.** Include delisted tickers, or sector
  screens will backtest too well.
- Coverage of every category above, ideally with fewer vendors.
- Programmatic access (API or MCP), reasonable rate limits, cost, and license
  terms that allow storing data locally.
- A brokerage is **not** required. The system never trades, so account data is
  only a convenience for the visibility layer.

**Open gaps:**
- Live and historical sector-level screening and breadth data.
- A historical news and catalyst archive tied to specific dates. This is the
  hardest to source and the most important for honestly backtesting Agent 1's
  catalyst-based picks.
- *(Found while scaffolding)* The summary listed neither a source for company
  fundamentals nor one for **live** news/catalysts. Fundamentals are now covered by
  Equibles (see "Chosen so far"); live news is still a gap.

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
| Data access | The middleware fetches data through provider interfaces, not the agents. Vendors are not decided (§6). `data/mcp.py` holds skeleton adapters for the original candidates (Massive, Robinhood) behind a small `McpToolCaller` protocol; the tool-name mapping is TODO. Any other vendor is a new adapter that implements the same protocols. Any quotes/account adapter must have **no order methods**. | `data/base.py`, `data/mcp.py` |
| User decisions | Stored in a separate table. `Store.review_trail()` (what the process agent reads) never includes them. | `store.py` |
| Outcomes agent | Plain deterministic code, no LLM, so "no judgment" holds by construction. | `agents/outcomes.py` |
| Process → Agent 0 improvement | Improvement signals are stored as `ImprovementNote`s with `approved=False`. Only human-approved notes are injected into stage prompts. This guards against the loop overfitting to recent outcomes. | `agents/process_review.py`, `agents/base.py` |
| Follow-up scheduling | Agent 5 exposes `tick(now)`. It runs the cheap tripwire check every tick and the full re-review when `full_review_interval` has passed. An external scheduler (cron, etc.) calls it. | `agents/follow_up.py` |

**Not built yet:** data-provider selection and real adapters, the backtest
harness (replay over a date range with holdout enforcement), and a CLI or UI for
the middleware report.
