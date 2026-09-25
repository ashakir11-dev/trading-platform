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
  agents/<agent>/analyses/<run_id>/<subject>/
    claim.md                                written first by the agent
    raw/NNN-<Tool>.json                     every Equibles response, saved by a hook
    analysis.md                             the agent's analysis
    companies/<TICKER>.md                   sector-deep-dive only: one file per company
  positions/<position_id>/position.md       accepted trades being watched
  decisions/<candidate_id>.md               the user's decisions: middleware agent only
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

## analysis.md (common frontmatter)

Every agent's `analysis.md` starts with these fields, then the agent-specific fields
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
mode: live                    # live | isolation
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
- <candidate_id>: <entry / stop / target / horizon>   (from the technical-analysis stage)

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

Trade facts only: no decision text, notes or reasoning of the user.

```markdown
---
position_id: 20260925T213314Z-XOM
ticker: XOM
direction: long
opened: 2026-09-26            # the user's entry date, once known
entry: 118.40                 # planned, then the actual price once traded
stop: 111.00
target: 134.00
horizon: swing
level_trigger: close
status: open                  # open | closed
closed: null
exit_price: null
plan: workspace/agents/technical-analysis/analyses/<run_id>/XOM
---
```
