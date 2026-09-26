# Sequence diagrams

How a run moves between agents. The **middleware agent** (the slash commands) launches
each subagent with a brief, never fetches data itself, and moves results along through
the analysis folders in `workspace/`. Each subagent fetches its own data from
Equibles; a hook saves every response to the agent's `raw/` folder. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the principles and
[prompt-subagents-design.md](prompt-subagents-design.md) for the mechanics.

## 1. Pipeline run (`/run`)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant MW as Middleware agent
    participant A0 as market-scanner
    participant A1 as sector-deep-dive (×N)
    participant A2 as company-deep-dive (×M)
    participant A3 as technical-analysis (×M)
    participant EQ as Equibles MCP
    participant WS as workspace/

    User->>MW: /run [--max-sectors N] [--shortlist N]
    MW->>WS: run.md, profile.json (copy)
    MW->>A0: brief (run_id, as_of, analysis folder)
    A0->>WS: claim.md
    A0->>EQ: ETF prices, macro, VIX, calendar (one batch)
    EQ-->>A0: responses (prices as statistics)
    Note over WS: hook saves every response to raw/
    A0->>WS: output.md (sector calls)
    A0-->>MW: done <path>
    Note over MW: drop downside calls if no shorts;<br/>keep the N most confident
    par one per pursued sector
        MW->>A1: brief (sector, direction, upstream = scanner folder)
        A1->>WS: read scanner output + raw/
        A1->>EQ: holdings, screen, prices, filings, events
        A1->>WS: companies/*.md, output.md (ranked shortlist)
    end
    Note over MW: passed, best score first, cap per sector;<br/>record duplicates and conflicts
    par one per candidate
        MW->>A2: brief (ticker, direction, upstream = scanner + sector)
        A2->>EQ: fundamentals, filings, guidance, estimates, insiders...
        A2->>WS: output.md (verdict, catalyst checks)
    end
    par one per candidate that passed
        MW->>A3: brief (ticker, upstream = company, profile)
        A3->>EQ: prices (statistics + levels), quote, earnings
        A3->>WS: output.md (plan + rule results)
    end
    Note over MW: recompute price order, max loss,<br/>reward:risk; a mismatch blocks it
    MW->>WS: report.md
    MW-->>User: report
    User->>MW: /decide <candidate_id> accept|reject
    MW->>WS: decisions/<id>.md (middleware only);<br/>positions/<id>/position.md on accept
```

## 2. Follow-up, evaluation and feedback

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant MW as Middleware agent
    participant A5 as follow-up (×positions)
    participant EV as stage-evaluator
    participant FB as stage-feedback
    participant WS as workspace/

    User->>MW: /follow-up (or cron)
    par one per open position
        MW->>A5: brief (position, last check, cooldown state)
        A5->>WS: read position, plan, earlier analyses
        Note over A5: tripwires: entry, stop, targets, trail,<br/>checkpoints, max hold, events; news with 12h cooldown;<br/>full re-review on alert or on the trade type's cadence
        A5->>WS: output.md
    end
    MW->>WS: position state, alerts.md
    MW-->>User: alerts, ACTION NEEDED when a level is hit or exit advised
    User->>MW: /trade <id> exited <price>
    User->>MW: /evaluate
    par one per (run, agent)
        MW->>EV: brief (agent, run, eval date)
        EV->>WS: evaluations/<run>--<date>/output.md
    end
    MW->>WS: decisions/reviews/ (your decision vs outcome)
    MW-->>User: agent grades; your decision review in chat only
    User->>MW: /feedback <agent>
    MW->>FB: brief (agent, evaluations)
    FB->>WS: feedback/<proposal>.md (pending)
    User->>MW: /approve <agent> <proposal>
    MW->>MW: append to prompts/<agent>/lessons.md, git commit
```

## 3. Backtest stage (`/backtest`)

```mermaid
sequenceDiagram
    autonumber
    participant MW as Middleware agent
    participant GK as gatekeeper
    participant AU as pit-auditor
    participant ST as <agent>-backtest
    participant WS as workspace/runs/<run>/

    MW->>WS: lessons/<agent>.md (as committed before as_of)
    MW->>GK: stage, subject, as_of, pack folder
    GK->>WS: packs/.../data/ (filtered to as_of), gaps, manifest
    Note over WS: raw responses go to .gatekeeper/ (hidden from the others);<br/>prices copied with later bars removed
    MW->>AU: pack, as_of
    AU->>WS: audit.md (clean | leaks)
    MW->>ST: brief + pack + lessons (no data tools)
    ST->>WS: output.md (+ requests.md if it needs more)
    opt requests (at most 2 rounds)
        MW->>GK: extend the pack
        MW->>AU: re-audit
        MW->>ST: rerun with the draft
    end
```
