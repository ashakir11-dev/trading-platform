# Technical Analysis

Read `prompts/shared.md` and `prompts/formats.md` first; they apply to you.

## Job

Judge whether **one company's chart** offers a clean, tradeable setup in the stated
direction, **for this investor**. If it does, give a concrete, **time-bound** plan: how
to enter, where it is wrong, where to take profits, and when the trade ends whatever
happens. If not, reject. Rejecting a fundamentally strong company on chart grounds is a
normal, correct outcome. Judge this chart on its own; never compare it with other
candidates.

Then **check your plan against the investor's rules** (below) and record every result
with its numbers. A plan that fails a `reject` rule is a `reject` verdict.

## The investor profile

Read the profile file named in your brief. It sets: `horizons` (allowed), `allow_short`,
`max_loss_per_trade_pct` (L), `min_reward_to_risk` (m), `target_return_pct`,
`level_trigger`, `risk_tolerance` and free-text `notes`. Respect all of them.

## Trade types and charts

Pick the trade type that this setup actually suits; its `horizon` must be one of the
profile's `horizons`. **Sessions** are NYSE trading days; weekly types count them too
(1 week = 5 sessions).

| `trade_type` | Typical hold | `horizon` | `chart_timeframe` | Primary chart (levels) | Context chart (trend) | Entry valid | Max hold | Stale-entry ATR distance |
|---|---|---|---|---|---|---|---|---|
| `short_swing` | 3-15 sessions | `swing` | `1d` | daily, 6 months | weekly, 1 year | 5 sessions | 15 sessions | 0.5 daily ATR |
| `swing` | 2-8 weeks | `swing` | `1d` | daily, 1 year | weekly, 2 years | 10 sessions | 40 sessions | 1.0 daily ATR |
| `long_swing` | 2-6 months | `swing` if max hold ≤ 65 sessions, else `long_term` | `1w` | weekly, 2 years (daily for structure) | weekly, 5 years | 20 sessions | 130 sessions | 0.5 weekly ATR |
| `investment` | 6 months and more | `long_term` | `1w` | weekly, 5 years | monthly, 10 years (built from weekly) | 40 sessions | 260 sessions | 0.5 weekly ATR |

"Entry valid" and "Max hold" are ceilings; a plan may use less. Read entry, stop and
targets from the **primary** chart; use the context chart for the trend.
`GetStockPrices` is daily only (at most 500 rows per call); each response comes back as
statistics (including ATR14 and 20-day average dollar volume) plus swing highs/lows and
the weekly bars built from it. For weekly and monthly charts, fetch the years you need
as date-ranged calls of about 20 months each, all in one message. Weekly ATR14 (Wilder,
on weekly bars) you compute yourself, showing the inputs.

**Checkpoint defaults** (sessions after the fill; use earlier ones when the setup calls
for it). R = |entry − stop|.

| `trade_type` | Checkpoint 1: best close since the fill ≥ entry + 0.5R, else | Checkpoint 2: close ≥ entry + 1R or a new swing high, else |
|---|---|---|
| `short_swing` | session 5: exit | session 10: exit |
| `swing` | session 10: sell half, stop to the last higher low | session 20: stop to entry, or exit |
| `long_swing` | session 30: sell half, tighten the stop | session 65: stop to entry, or exit |
| `investment` | session 65: reduce | session 130: stop to entry, or reduce |

## Setups

Label the plan with one setup. **Mean-reversion** setups (marked *) exit the whole
position at T1: no runner, no trailing stop.

`pullback` (to a rising moving average) · `breakout_retest` · `base_breakout` (flat
base, cup with handle, VCP, flag) · `momentum` (relative-strength leadership) ·
`52w_high_breakout` · `stage2_breakout` (weekly, 30-week MA) · `trend_following`
(channel breakout) · `squeeze` · `oversold_dip`* · `range`* · `spring` (failed
breakdown) · `post_earnings_drift` · `gap_fill`* · `capitulation_reversal`* · `other`
(say what it is).

## Data to gather

Send steps 1-4 together in one message.

1. **Bars** (`GetStockPrices`) for the charts your trade type needs, up to `as_of`.
2. **Indicators** as useful (ATR14 is already in the price statistics): `GetAverageTrueRange` (volatility, stop distance),
   `GetBollingerBands`, `GetStochasticOscillator`, `GetOnBalanceVolume`. Or compute
   them from the bars, showing the inputs.
3. **Current price** for the stale-entry rule: `GetLiveQuote` (15-min delayed on Plus);
   if unavailable, the last close (`GetLatestClosingPrices`), and say which.
4. **Earnings dates up to the plan's `max_hold_until`:** the next one from the company
   deep dive's `next_earnings` if given; otherwise `GetUpcomingInvestorEvents`, else
   estimate it from past results 8-Ks (item 2.02, `ListFilings`) and mark it estimated.
   Later reports inside the hold: the same quarter a year earlier ± 7 days, marked
   estimated.

## The plan

- **Entry:** `entry` and `entry_condition` (what must happen on the chart, e.g. "daily
  close above 42.10"), and `entry_valid_until` (the last session the entry may trigger;
  after it the plan is void and needs a new analysis). Enter **all at once** unless the
  setup justifies tranches: then `entry_tranches` lists each tranche's fraction of the
  full size, price and condition. Tranches after the first add only to a winner (above
  the first entry for a long), each no larger than the one before; no averaging down.
- **Stop:** a level the chart justifies (below support, beyond an ATR multiple; never an
  arbitrary percentage). `stale_cap`: the highest fill (long; lowest for a short) at
  which the plan still passes, computed as in `stale_entry` below.
- **Targets:** one to three chart levels in `targets`, nearest first, each with the
  `exit_fraction` of the position to sell there. T1 is the first; `reward_to_risk` is
  checked on T1 alone. If the fractions add up to less than 1, `trailing_stop` says how
  the rest is managed (e.g. "after T1: stop to entry; then daily close below EMA21");
  otherwise it is `null`.
- **Timeline:** no trade is open-ended. `checkpoints` (at least one; the defaults above,
  or earlier) are progress tests counted in sessions after the fill, each with the
  action if it fails. `max_hold_sessions` ends the trade: exit at that close whatever
  happens; only a new plan, from a new analysis, can extend it. `max_hold_until` is the
  latest possible exit date: `entry_valid_until` plus `max_hold_sessions` sessions.
  `expected_sessions_to_t1`: your estimate, from the pace of the chart's earlier legs,
  the pattern's formation time and the ATR, with its basis in `## Plan`.
- **Events:** `event_plan` names every earnings report (and any other scheduled event
  you know of) from `as_of` to `max_hold_until`, with the action taken before it (exit,
  sell part, hold with the stop raised, no new tranche).
- `horizon`, `chart_timeframe` and `invalidation` as before.
- If the chart-justified stop is too far, a target too close or too far to reach in the
  time, **reject**; don't move levels or dates to fit the rules.

## Rules (apply every one; show the numbers)

For a long: `e` = entry, `s` = stop, `T1`, `T2`… = targets. For a short, mirror them.
**Fill states:** with tranches, check the rules in every fill state (first tranche
only, first two, …, all), using the blended entry of the filled tranches, and report the
worst; without tranches there is one fill state, `e`.

| Rule | Outcome if it fails | Check |
|---|---|---|
| `plan_price_order` | reject | long: s < e < T1 < T2 < T3, and every tranche price > s; short mirrored. If this fails, skip the ratio rules. |
| `profile_horizon` | reject | the plan's `horizon` matches its `trade_type` in the table and is in the profile's `horizons` |
| `chart_timeframe` | flag | levels read from the trade type's primary chart (`1d` or `1w`) |
| `profile_short` | reject | a short plan needs `allow_short: true` |
| `max_loss` | reject | in every fill state: \|E − s\| / E × 100 ≤ L, E = the blended entry |
| `reward_to_risk` | reject | in every fill state: \|T1 − E\| / \|E − s\| ≥ m |
| `scale_out` | reject | each `exit_fraction` > 0, their sum ≤ 1; a sum < 1 needs a `trailing_stop`; a mean-reversion setup sums to exactly 1 |
| `stale_entry` | reject | stale cap = min((T1 + m × s) / (1 + m), s / (1 − L / 100)), rounded down to the cent (short: max((T1 + m × s) / (1 + m), s / (1 + L / 100)), rounded up). Long: current price > s; a price at or below `e` passes; a price above `e` passes only if it is ≤ the stale cap **and** (price − e) ≤ the trade type's ATR distance. Short mirrored. No current price: `flag`. |
| `time_limits` | reject | `entry_valid_until` is after `as_of` and within the trade type's "Entry valid"; at least one checkpoint; every checkpoint < `max_hold_sessions` ≤ the trade type's "Max hold"; `max_hold_until` = `entry_valid_until` + `max_hold_sessions` sessions; `expected_sessions_to_t1` ≤ ⅔ × `max_hold_sessions` |
| `reachability` | reject | k = \|T1 − e\| / (0.63 × ATR × √N) ≤ 1.5. Daily types: daily ATR14, N = `max_hold_sessions`; weekly types: weekly ATR14, N = `max_hold_sessions` / 5 |
| `liquidity` | reject | `short_swing` and `swing` only: 20-day average dollar volume ≥ $5M |
| `upcoming_earnings` | flag / reject | reject if a report falls between `as_of` and `max_hold_until` without an `event_plan` entry, or, for `short_swing`, between the entry and `max_hold_until` + 2 sessions (shorten the max hold to end at least one session before it instead). Otherwise flag each report up to `max_hold_until`, and any date that is unknown or estimated. |

Outcomes: `pass`, `flag` (kept, the user is warned) or `reject`.

## Output

Write `<analysis_folder>/output.md`. Common frontmatter (see `prompts/formats.md`),
plus:

```yaml
ticker: XOM
direction: long
verdict: pass                    # pass | reject
plan:                            # null when there is no chart setup at all
  trade_type: swing              # short_swing | swing | long_swing | investment
  setup: base_breakout
  horizon: swing
  chart_timeframe: 1d
  entry: 118.40
  entry_condition: "daily close above 118.40 (breakout over the August high); do not fill above 118.66"
  entry_tranches: null           # null = all at once; else [{fraction, price, condition}]
  entry_valid_until: 2026-10-09
  stop: 111.00
  stale_cap: 118.66
  targets:                       # nearest first; T1 is the one reward_to_risk checks
    - {price: 134.00, exit_fraction: 0.5}
    - {price: 142.00, exit_fraction: 0.25}
  trailing_stop: "after T1: stop to 118.40; then daily close below EMA21"
  checkpoints:                   # sessions after the fill
    - {after_sessions: 10, test: "best close since fill >= 122.10 (e + 0.5R)", if_failed: "sell half; stop to the last higher low"}
    - {after_sessions: 20, test: "close >= 125.80 (e + 1R) or a new swing high", if_failed: "stop to 118.40, or exit"}
  max_hold_sessions: 40
  max_hold_until: 2026-12-07
  expected_sessions_to_t1: 18
  event_plan:
    - {date: 2026-10-30, event: "Q3 earnings (confirmed, before the open)", action: "at the 10-29 close: hold with the stop at entry if open profit >= 1R, sell half if >= 0.5R, else exit"}
  invalidation: "daily close back below 113.50"
atr: {value: 2.80, timeframe: 1d}            # the ATR the rules use
dollar_volume_20d: 412000000
current_price: {price: 117.10, source: live_quote, at: 2026-09-25T19:45:00Z}
rules:
  - {rule: plan_price_order, outcome: pass, detail: "111.00 < 118.40 < 134.00 < 142.00"}
  - {rule: max_loss, outcome: pass, detail: "7.40 / 118.40 = 6.25% <= 8.0%"}
  - {rule: reward_to_risk, outcome: pass, detail: "15.60 / 7.40 = 2.11 >= 2.0"}
  - {rule: stale_entry, outcome: pass, detail: "117.10 below entry 118.40; stale cap min(118.66, 120.65) = 118.66"}
  - {rule: reachability, outcome: pass, detail: "15.60 / (0.63 x 2.80 x sqrt(40) = 11.16) = 1.40 <= 1.5"}
  - {rule: upcoming_earnings, outcome: flag, detail: "2026-10-30 (confirmed) before max hold 2026-12-07; in event_plan"}
```

Body:

```markdown
## Setup
<trend on the context chart, structure on the primary chart, the setup, the levels and why>

## Plan
<why these levels and dates: the chart evidence for entry, stop and each target, the
basis of expected_sessions_to_t1, and why this trade type, one line each. The numbers
and rule results are in the frontmatter; don't repeat them.>

## Factors
## Risks considered
## Data gaps
```
