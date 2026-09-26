# Backtest runs (middleware agent)

A backtest runs the same stages and forwarding rules as a live run, as of a past
moment, with one difference: **stage agents get no data**. For every stage agent you
launch, you first have its data pack built and audited.

## Setup (in addition to the usual)

- `as_of`: a date means that day's 16:00 New York close (e.g. `2026-06-01` →
  `2026-06-01T20:00:00Z` in summer, `21:00Z` in winter). Refuse a future `as_of`.
- `run.md`: `mode: backtest`, `point_in_time: pending`, and the options (including
  `allow_current_constituents`).
- **Lessons as of the date.** For each stage agent: find the last commit before `as_of`
  that touched its lessons (`git log -1 --before=<as_of> --format=%h --
  prompts/<agent>/lessons.md`). If there is one, read the file at that commit (`git show
  <commit>:prompts/<agent>/lessons.md`) and write it with the Write tool to
  `workspace/runs/<run_id>/lessons/<agent>.md`; if none, write "(no lessons before
  <as_of>)". Stage briefs point to that file.

## For every stage agent: pack → audit → agent

1. **Gatekeeper:** launch `gatekeeper` with: `stage`, `subject`, `as_of`, `run_id`,
   `pack: workspace/runs/<run_id>/packs/<stage>/<subject>`, the upstream analysis folders
   the stage agent will get, and `allow_current_constituents` for the sector stage.
2. **Audit:** launch `pit-auditor` with the pack and `as_of`. On `verdict: leaks`,
   relaunch the gatekeeper once with the audit attached (it must rebuild the pack
   without the leaks), then audit again. Still leaking: record the pack under "Errors"
   and mark the run `point_in_time: leaks-found`; you may still run the stage (the
   report must say so).
3. **Stage agent:** launch `<agent>-backtest` with the usual brief plus
   `mode: backtest`, `pack: <pack folder>` and `lessons: workspace/runs/<run_id>/lessons/<agent>.md`.
4. **Requests** (at most 2 rounds): if the agent left `<analysis_folder>/requests.md`,
   relaunch the gatekeeper for the same pack with the requests (extension round), audit
   again, then relaunch the stage agent with the same brief plus
   `draft: <analysis_folder>/output.md`.

Launch packs, audits and agents for the subjects of one stage **in parallel** (all
gatekeepers, then all auditors, then all stage agents), always in the foreground.

## Finishing

- `point_in_time: audited` if every pack ended clean, else `leaks-found` with the list.
- The report's first line says **BACKTEST as of <as_of>**, the `point_in_time` label,
  and the limits: price levels split-adjusted to today, macro values latest-revised,
  and whether current constituents were used (survivorship bias).
- Suggest `/evaluate --run <run_id> --min-days 0`: outcomes after `as_of` are already
  known, so a backtest can be graded immediately.
