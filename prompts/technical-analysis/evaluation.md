# Technical Analysis: evaluation criteria

Read `prompts/evaluation.md` first.

**Subjects:** each candidate analysed in the run, passed or rejected — including the
eligible candidates the middleware listed under "Also passed" (they are graded exactly
like the recommendations; the comparison between the two groups is what tests the
pick rule, so add `picked: true|false` per subject from `run.md`).

**Scale-out plans:** with several `targets`, "target first" means the *first* target;
also record which targets were hit in order, the size-weighted realised return using
the fractions (unhit remainder marked at the exit or the mark), and whether the later
targets were ever reached. An entry that never triggered before `entry_valid_until`
is "expired", `worked: null`, and counts as not filled.

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
- **Chart read**, for every subject, from `as_of` to `eval_as_of` (or to the exit):
  - `rs_vs_market_pp`, `rs_vs_sector_pp`: the stock's return minus SPY's and minus the
    sector ETF's (the `vs_sector.etf` in the analysis), and the ETF's minus SPY's.
  - `rs_read_held`: a `rising`/`new_high` read held if the stock outperformed that
    benchmark, a `falling`/`new_low` read if it underperformed; `flat` is not graded.
    Per benchmark (SPY, sector ETF).
  - `trend_read_held`: for an `up` trend read, no close below the last higher low the
    analysis named (mirrored for `down`) before the exit or `eval_as_of`.
  - `with_context`: the plan traded with its stage, its sector (leader in a leading group
    for a long) and the regime (`market_regime` passed), or against one of them (say
    which).

**Summary metrics:** `plans`, `filled`, `expired`, `target_first`, `stop_first`, `open`,
`avg_realised_rr`, `rejected_that_ran` (rejected setups that rose more than the plan's
would-be target distance, if a plan was sketched), and `picked_vs_also_passed`: mean
direction-adjusted return of the picked candidates minus the "also passed" ones (the
pick rule is doing its job when this is positive). Chart read: `rs_read_held` (held /
graded, per benchmark), `trend_read_held` (held / graded), and the mean direction-adjusted
return of plans `with_context` minus those against it, and of plans without a
`market_regime` flag minus those with one (the method is doing its job when both are
positive).

**Reasoning:** did the analysis follow "How to read the chart" in order, and is every
stage, level, volume, volatility and relative-strength claim traceable to a number in its
`raw/` (a claimed pattern the statistics don't show is unsound)? Were failure modes the
numbers showed at `as_of` (extended entry, weak-volume breakout, overhead supply, lower
highs under a flat MA, a long below a falling SMA200, a laggard RS line, climax or
divergence) missed or under-weighted? A plan that failed through one of them is a
`foreseeable_miss`. Was the stop sane in ATRs (not inside 1 ATR of noise)? Did the
regime or chart volatility leak into the risk bucket or its limits (it must not)? Were
the stop and target at levels the chart justified (swing points, zones, ATR) or placed
to fit the rules? Was event risk (earnings) weighed? Was a plan sitting
right at its `risk_bucket`'s rule limit (reward:risk within 0.1 of the bucket's minimum,
max loss within 0.5 points of the bucket's maximum)? That is a warning sign worth
recording. Also note whether the bucket's reward shape actually played out (did a
`speculative` pick's realised move match its bigger target, or did it behave like a
`core` one) — that's a signal for the sector deep dive's bucket calls, not just the
technical plan.
