# Market Scanner: evaluation criteria

Read `prompts/evaluation.md` first.

**Subjects:** each sector call in `calls`, plus the market summary.

**Outcome facts** from `as_of` to `eval_as_of`, for every sector ETF (called or not)
and SPY:
- the ETF's return, and its return minus SPY's (relative return);
- a call `worked` if an upside call beat SPY, or a downside call lagged SPY.

**Summary metrics:** `hit_rate` (calls that worked / calls), `avg_relative_return` of
the calls in their direction (upside: relative return; downside: its negative), and
`missed_movers`: sectors not called whose relative return was among the 3 largest in
absolute size.

**Reasoning:** was each thesis backed by the numbers it cited? Did the market summary
weigh the macro and event risk visible at `as_of` (e.g. a scheduled release that later
moved the sector)? Were the missed movers visible in the data at `as_of`?
