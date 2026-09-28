# Congress Analyst: evaluation criteria

Read `prompts/evaluation.md` first.

**Subjects:** each candidate the congress-analyst scored in the run (whether or not the
candidate was ultimately recommended).

**Outcome facts**, from `as_of` to `eval_as_of`:
- The candidate's own price return over the window (same as the technical-analysis
  evaluation would compute), so the sign of `congress_adjustment` can be compared with
  what actually happened.
- Did `congress_adjustment`'s **sign** agree with the candidate's realized direction of
  outperformance vs. its sector ETF? (Not raw price direction — a market-wide move isn't
  what this signal claims to predict.)
- Was the **magnitude** informative: did candidates with a larger `|congress_adjustment|`
  show a stronger relationship (either way) than ones near zero?

**Summary metrics:** `candidates_scored`, `adjustment_sign_agreement_rate` (share where
the sign matched outperformance direction), `avg_abs_adjustment`.

**Reasoning:** was `member_score` applied correctly from the scorecard in effect at the
run's `as_of` (check `scorecard_as_of` predates the run, and the arithmetic in the
"Congressional activity" table)? Were unscored members correctly excluded rather than
silently zeroed? Flag any case where a member with very few resolved trades in the
scorecard seemed to swing the number — that is a sample-size problem in the scorecard,
not this agent's reasoning, and belongs in feedback for the `rankings` mode rather than
a lesson for candidate-signal mode.
