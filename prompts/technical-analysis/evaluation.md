# Technical Analysis: evaluation criteria

Read `prompts/evaluation.md` first.

**Subjects:** each candidate analysed in the run, passed or rejected.

**Outcome facts** from `as_of` to `eval_as_of`, from daily bars, per the profile's
`level_trigger` (`close`: closes decide; `intraday`: lows/highs decide). Walk each plan
forward session by session, exactly as written:
- **Entry:** was the entry condition met by `entry_valid_until` (first date and price;
  per tranche if there are tranches)? Not met: the outcome is "not filled (expired
  <date>)", `worked: null`, and say where the price went. A fill above the `stale_cap`
  (long) counts as not filled.
- **After the fill**, the first of these ends each part of the position:
  - the stop (then the `trailing_stop` for what is left after T1) → exit at the stop;
  - each target in turn → its `exit_fraction` exits there;
  - a failed checkpoint → its `if_failed` action on that session's close ("sell half"
    = half the remaining position; "stop to entry" moves the stop);
  - an `event_plan` action on its date;
  - `max_hold_sessions` after the fill → **time exit** of everything left, at that
    session's close.
  The same bar reaching both the stop and a target counts as the stop (conservative).
- **Per plan:** realised R = Σ (fraction × (exit − E)) / (E − s), E = the blended entry
  of the filled tranches, s = the initial stop; how it ended (`stop`, `targets`,
  `trail`, `checkpoint`, `time_exit`, `event`); sessions from the fill to T1 against
  `expected_sessions_to_t1`; MFE and MAE (best and worst move from E, in % and in R);
  give-back (peak open R minus realised R).
- **Still open** at `eval_as_of` (neither ended nor past `max_hold_sessions`): the
  mark-to-market R, MFE and MAE, and which clock comes next.
- `worked`: realised R > 0 → true; ≤ 0 → false; not filled or still open → null.
- **Rejected setups:** what the price did (return and range). Note when a rejected
  setup would clearly have worked; that isn't automatically a miss, since the rules may
  have required the rejection.
- For positions the user actually entered, use the actual fills and exits from the
  position file alongside the planned ones (trade facts only).

**Summary metrics:** `plans`, `filled`, `expired_unfilled`, `open`, and among closed
plans: `ended_by` counts (stop, targets, trail, checkpoint, time_exit, event),
`avg_realised_r`, `avg_mfe_r`, `avg_mae_r`, `avg_give_back_r`, `t1_on_time` (T1
reached within `expected_sessions_to_t1`), and `by_setup` and `by_trade_type` (plans,
closed, avg_realised_r each). Also `rejected_that_ran` (rejected setups that rose more
than the plan's would-be T1 distance, if a plan was sketched).

**Reasoning:** the agent's method is `prompts/technical-analysis/playbook/cheat-sheet.md`:
did it follow it (procedure, setup criteria, entry and exit rules), and where it
deviated, was that justified? Were the stop and targets at levels the chart justified (swing points,
ATR) or placed to fit the rules? Was the trade type right for the chart, and was the
timeline (entry validity, checkpoints, max hold, expected time to T1) realistic? Was
event risk weighed and planned for? Was a plan sitting right at a rule limit
(reward:risk within 0.1 of the minimum, max loss within 0.5 points, reachability k
within 0.1 of 1.5)? That is a warning sign worth recording.
