# Follow-Up: evaluation criteria

Read `prompts/evaluation.md` first.

**Subjects:** each follow-up analysis in the run (one per position).

**Outcome facts** from the check's `as_of` to `eval_as_of`:
- **Alerts:** was each alert real (the stop, target, trailing-stop or entry cross is
  visible in the bars; the checkpoint test really failed; the session count or date
  really reached the max hold, entry expiry or event; the news item is material by the
  role's list)? Was a real event missed (a cross, a due clock or a material filing in
  the checked window with no alert)? How many days after the event was it raised? Was
  a price or clock alert wrongly held by the cooldown?
- **Recommendations** (full reviews): after `hold`, `adjust_plan` or `exit`, what did the
  price do? `exit` worked if the position would have done worse by holding (the price
  moved against it or hit the stop); `hold` worked if it didn't hit the stop in the next
  10 trading days.

**Summary metrics:** `alerts`, `false_alerts`, `missed_events`, `avg_alert_lag_days`,
`missed_clocks` (checkpoints, max holds, entry expiries or events due with no alert),
`recommendation_hit_rate`.

**Reasoning:** were materiality calls correct and explained? Did the full review check
the original catalysts against new information? Did any updated plan pass the rules,
and did it extend a losing trade's time or risk (it must not)?
