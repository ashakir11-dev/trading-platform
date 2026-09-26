---
description: One follow-up tick over every open position (for cron)
argument-hint: "[position_id]"
model: claude-sonnet-5
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Run one follow-up tick. Arguments: $ARGUMENTS (optional: a single position_id; then
use `mode: isolation`, which forces a full re-review).

1. Set up a run as usual with `mode: follow-up` in `run.md`.
2. Find open positions: `workspace/positions/*/position.md` with `status: open` (or
   just the one given). None: say so, set `status: complete`, stop.
3. Launch one `follow-up` agent per position, in parallel. Subject: the position_id.
   Upstream: the position folder and the `plan:` folder. Profile: the run's profile.
   Put the position's `last_check`, `last_full_review`, `last_alert_at` and
   `held_alerts` (from `position.md`) in the brief.
4. For each result, update `position.md`: `last_check` = as_of; `last_full_review` =
   as_of if `full_review: true`; `last_alert_at` = as_of if a `material_news` alert was
   delivered; `held_alerts` = the `held` list (delivered ones are cleared);
   `stop_in_force` and `targets_hit` from the result. Append each delivered and held
   alert to `workspace/positions/<id>/alerts.md` with the run id. If the agent
   recommended `adjust_plan`, do **not** change the plan: the user decides. After
   `entry_expired` (the position was never opened), set `status: closed` with
   `closed` = the date and `exit_price: null`: the plan is void.
5. Report, per position: price vs entry, stop in force and targets, sessions held and
   the next clock (checkpoint, max hold or event, with its date), alerts, the
   recommendation. When `action_needed: true`, start that position's section with
   **ACTION NEEDED**, say what to do (e.g. sell 0.5 at T1, exit at the max-hold close,
   cancel the untriggered entry) and give the commands:
   `/trade <position_id> entered <price> [date] [fraction]` after an entry or tranche,
   `/trade <position_id> exited <price> [date] [fraction]` after a full or partial exit,
   then `/evaluate --run <run_id>` once closed. Write the report to
   `workspace/runs/<run_id>/report.md`.
