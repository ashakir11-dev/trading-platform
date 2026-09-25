# Sequence diagrams

How data moves between agents at runtime. Agents never call each other: the
**Middleware** fetches data, builds each prompt from the upstream report plus the
relevant raw data, validates the structured reply, logs it, and hands it on. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the principles behind each step.

Notes marked **Rule** are deterministic checks in code (no LLM).

## 1. Pipeline run (one `as_of` date)

Rendered: [diagrams/sequence-pipeline-run.png](diagrams/sequence-pipeline-run.png)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant MW as Middleware
    participant Data as Data providers
    participant Store as Store (SQLite)
    participant A0 as Agent 0<br/>Market Scanner
    participant A1 as Agent 1<br/>Sector Deep Dive
    participant A2 as Company Deep Dive
    participant A3 as Technical Analysis

    User->>MW: run(as_of)
    MW->>Store: load approved improvement notes (lessons per stage)

    MW->>Data: market_overview(as_of)
    Data-->>MW: market snapshots
    Note over MW: Rule: reject any snapshot dated after as_of (look-ahead guard)
    MW->>Store: save snapshots
    MW->>A0: raw market data
    A0-->>MW: MarketScanOutput (sector calls + structured reasoning)
    MW->>Store: log one StageRecord per sector call

    par one independent pass per sector
        MW->>Data: sector_screen, sector_breadth, sector news (as_of)
        Data-->>MW: bulk screen (one row per company) + sector data
        MW->>Store: save snapshots
        MW->>A1: Agent 0's sector call (confidence hidden) + market + sector raw data
        A1-->>MW: SectorDeepDiveOutput (every company: score, pass/fail, catalysts, reasoning)
    end
    Note over MW: Rule: forward passing companies, ranked by score, capped per sector,<br/>dedupe tickers across sectors
    MW->>Store: log forwarded and not-forwarded entries, create Candidates

    par one independent pass per company
        Note over MW: Rule: filter raw data to market + sector + this company only
        MW->>Data: fundamentals(ticker, as_of), company news
        Data-->>MW: point-in-time financials + news (or explicit data-gap snapshots)
        MW->>A2: Agent 0 + Agent 1 reports (confidence hidden) + filtered raw data
        A2-->>MW: CompanyDeepDiveOutput (verdict, catalyst checks, reasoning)
    end
    Note over MW: Rule: advance only on verdict "pass", record confidence for attribution
    MW->>Store: log verdicts, rejected candidates stop here

    par one independent pass per surviving company (no cross-comparison)
        MW->>Data: ohlcv, indicators, pivots (as_of)
        Data-->>MW: price data
        MW->>A3: company deep dive report + company raw data + price data
        A3-->>MW: TechnicalOutput (verdict, setup, trade plan, reasoning)
    end
    Note over MW: Rule: "pass" without a plan is treated as reject
    MW->>Store: log verdicts, save Candidates

    opt live run (not a backtest)
        MW->>Data: quote(ticker) for each recommendation
        Data-->>MW: live price (display only)
    end
    MW-->>User: PipelineReport (recommendations, rejections, confidence trajectories)
```

## 2. User decision, follow-up loop, and review

Rendered: [diagrams/sequence-followup-review.png](diagrams/sequence-followup-review.png)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Sched as Scheduler (cron)
    participant MW as Middleware
    participant Data as Data providers
    participant Store as Store (SQLite)
    participant A5 as Agent 5<br/>Follow-Up
    participant OUT as Outcomes<br/>(deterministic)
    participant PROC as Process Review

    User->>MW: record_decision(candidate, accept/reject)
    MW->>Store: save UserDecision (separate table, never shown to agents)
    alt accepted
        MW->>Store: create Position from the technical plan
    end
    Note over User,MW: The user trades manually, the system never places orders

    loop every scheduled tick, for each open position
        Sched->>A5: tick(now)
        A5->>Data: price bars since open, news since last check
        Data-->>A5: bars, events
        Note over A5: Rule (tripwire): close beyond stop or target, or any new news event
        A5->>Store: save TripwireResult
        alt tripwire fired OR full-review interval elapsed
            A5->>Store: load original reasoning trail
            A5->>Data: fresh prices, indicators, pivots, fundamentals
            A5->>A5: LLM full re-review (hold / adjust plan / exit)
            A5->>Store: log StageRecord, update last_full_review_at
            A5-->>User: flag (advice only)
        end
    end

    User->>MW: close_position(exit price, date)
    User->>MW: review_position(position)
    MW->>Data: price bars over the holding period
    MW->>OUT: position + bars
    OUT-->>MW: OutcomeReport (return, drawdown, hit stop/target), no judgment
    MW->>Store: review_trail(position) (stage records + snapshots, NO user decisions)
    MW->>PROC: reasoning trail + raw data each stage had + outcome
    PROC-->>MW: per-stage grades, foreseeable vs black-swan attribution, improvements
    MW->>Store: save review and ImprovementNotes (unapproved)
    User->>Store: approve_improvement(note)
    Note over Store: Rule: only approved notes are injected into future stage prompts
```
