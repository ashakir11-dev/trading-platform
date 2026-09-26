# Technical Analysis: evaluation criteria

Read `prompts/evaluation.md` first.

**Subjects:** each candidate analysed in the run, passed or rejected.

**Outcome facts** from `as_of` to `eval_as_of`, from daily bars, per the profile's
`level_trigger` (`close`: closes decide; `intraday`: lows/highs decide):
- **Plans:**
  - `filled`: was the entry condition met (first date and price)? Never filled: the
    outcome is "not filled", `worked: null`, and say where the price went.
  - After the fill: which came **first**, the stop or the target (dates)? The same bar
    reaching both counts as the stop (conservative).
  - Neither yet: the mark-to-market return from the entry and the maximum adverse
    excursion (worst move against the position, in % and as a multiple of the risk
    e − s).
  - Realised reward:risk: (exit − entry) / (entry − stop) for a closed outcome.
  - `worked`: target first → true; stop first → false; open → null.
- **Rejected setups:** what the price did (return and range). Note when a rejected
  setup would clearly have worked; that isn't automatically a miss, since the rules may
  have required the rejection.
- For positions the user actually entered, use the actual entry from the position file
  alongside the planned one (trade facts only).

**Summary metrics:** `plans`, `filled`, `target_first`, `stop_first`, `open`,
`avg_realised_rr`, `rejected_that_ran` (rejected setups that rose more than the plan's
would-be target distance, if a plan was sketched).

**Reasoning:** were the stop and target at levels the chart justified (swing points,
ATR) or placed to fit the rules? Was event risk (earnings) weighed? Was a plan sitting
right at a rule limit (reward:risk within 0.1 of the minimum, max loss within 0.5
points)? That is a warning sign worth recording.
