# Workspace formats

All run data lives in `workspace/` at the repository root (git-ignored). Prompts and
lessons live in `prompts/` (versioned).

```
workspace/
  profile.json                              investor profile (optional; else profile.example.json)
  runs/<run_id>/
    run.md                                  run manifest (middleware agent)
    profile.json                            the profile used by this run
    report.md                               the report shown to the user
    lessons/<agent>.md                      backtests: each agent's lessons as of as_of
    packs/<stage>/<subject>/                backtests: audited data pack (claim, data/, gaps, manifest, audit)
    .gatekeeper/<stage>/<subject>/raw/      backtests: the gatekeeper's unfiltered responses (hook-protected)
  agents/<agent>/analyses/<run_id>/<subject>/
    claim.md                                written first by the agent
    raw/NNN-<Tool>.json                     every Equibles response, saved by a hook
    output.md                               the agent's analysis
    companies/<TICKER>.md                   sector-deep-dive only: one file per company
  agents/<agent>/evaluations/<run_id>--<YYYYMMDD>/
    claim.md, raw/, output.md               one evaluation of the agent's work in a run
  agents/<agent>/feedback/<proposal_id>.md  proposed lessons (pending | approved | rejected)
  positions/<position_id>/position.md       accepted trades being watched
  positions/<position_id>/alerts.md         follow-up alert log
  decisions/<candidate_id>.md               the user's decisions: middleware agent only
  decisions/reviews/<candidate_id>--<YYYYMMDD>.md   your decision vs the outcome (D0)
  .state/                                   hook bookkeeping; don't touch
```

## Identifiers

| Id | Format | Example |
|---|---|---|
| `run_id` | UTC time of the run start, `YYYYMMDDTHHMMSSZ` | `20260925T213314Z` |
| subject | lowercase, spaces → `-`; tickers upper case | `market`, `information-technology`, `XOM` |
| `candidate_id` | `<run_id>-<TICKER>` | `20260925T213314Z-XOM` |
| `position_id` | same as the `candidate_id` it came from | `20260925T213314Z-XOM` |

## claim.md

```markdown
---
agent: sector-deep-dive
run_id: 20260925T213314Z
mode: default                 # default | isolation
subject: energy
as_of: 2026-09-25T21:33:14Z
started_at: 2026-09-25T21:35:02Z
---
```

## output.md (common frontmatter)

Every agent's `output.md` starts with these fields, then the agent-specific fields
its role lists:

```yaml
agent: <agent>
run_id: <run_id>
mode: default | isolation
subject: <subject>
as_of: <ISO timestamp>
prompt_commit: <from the brief>
upstream: [<folders read>]
confidence: <0.0-1.0>
```

## run.md (middleware agent)

```markdown
---
run_id: 20260925T213314Z
mode: live                    # live | isolation | follow-up | evaluation | backtest
as_of: 2026-09-25T21:33:14Z
prompt_commit: 174a3ea
options: {max_sectors: 1, shortlist: 3}
status: running               # running | complete | failed
---
## Stages
| stage | subject | agent | status | analysis |
|---|---|---|---|---|
| market-scanner | market | market-scanner | done | workspace/agents/market-scanner/analyses/<run_id>/market |

## Not pursued
- <sector or ticker>: <stage>: <reason>

## Conflicts
- <ticker>: <duplicate | direction_conflict>: first <sector, direction>, also <sector, direction>

## Forwarded
- <candidate_id>: <sector>, <long|short>, potential_score <n>

## Recommendations
- <candidate_id>: <trade_type, setup / entry / stop / targets / entry valid until / max hold until>   (from the technical-analysis stage)

## Errors
- <agent> <subject>: <what failed>
```

## decisions/<candidate_id>.md (middleware agent only)

```markdown
---
candidate_id: 20260925T213314Z-XOM
run_id: 20260925T213314Z
ticker: XOM
decision: accept              # accept | reject
decided_at: 2026-09-26T14:05:00-04:00
position_id: 20260925T213314Z-XOM   # accept only
---
## Why
<the user's note, verbatim; "(none given)" if empty>

## Trade log
| date | action | price | size |
|---|---|---|---|

## Afterwards
```

## positions/<position_id>/position.md

Trade facts only: no decision text, notes or reasoning of the user. The plan fields are
copied from the technical analysis's `plan` when the position is created.

```markdown
---
position_id: 20260925T213314Z-XOM
ticker: XOM
direction: long
trade_type: swing
setup: base_breakout
horizon: swing
level_trigger: close
status: open                  # open | closed
opened: null                  # the date of the user's first fill
planned_entry: 118.40
entry: null                   # blended price of the user's fills, once traded
entry_tranches: null
entry_valid_until: 2026-10-09
stale_cap: 118.66
stop: 111.00                  # the initial stop
stop_in_force: 111.00         # after trailing or checkpoint actions (from follow-up)
targets:
  - {price: 134.00, exit_fraction: 0.5}
  - {price: 142.00, exit_fraction: 0.25}
targets_hit: []               # e.g. [T1], from follow-up
trailing_stop: "after T1: stop to 118.40; then daily close below EMA21"
checkpoints:
  - {after_sessions: 10, test: "best close since fill >= 122.10 (e + 0.5R)", if_failed: "sell half; stop to the last higher low"}
  - {after_sessions: 20, test: "close >= 125.80 (e + 1R) or a new swing high", if_failed: "stop to 118.40, or exit"}
max_hold_sessions: 40
max_hold_until: 2026-12-07
event_plan:
  - {date: 2026-10-30, event: "Q3 earnings (confirmed, before the open)", action: "..."}
fills: []                     # [{date, price, fraction}] fraction of the full planned size
exits: []                     # [{date, price, fraction}]
closed: null
exit_price: null              # blended price of all exits, once closed
plan: workspace/agents/technical-analysis/analyses/<run_id>/XOM
last_check: null              # follow-up state, kept by the middleware agent
last_full_review: null
last_alert_at: null           # last delivered material-news alert (the cooldown)
held_alerts: []
---
```

Positions created before these fields existed have a single `target`, no trade type
and no clocks; treat `target` as T1 with `exit_fraction: 1` and use a 14-day re-review.

`positions/<position_id>/alerts.md`: one line per alert,
`- <as_of> <delivered|held> <kind>: <detail> (run <run_id>)`.
