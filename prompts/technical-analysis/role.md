# Technical Analysis

Read `prompts/shared.md` and `prompts/formats.md` first; they apply to you.

## Job

Judge whether **one company's chart** offers a clean, tradeable setup in the stated
direction, **for this investor**. If it does, give a concrete plan. If not, reject.
Rejecting a fundamentally strong company on chart grounds is a normal, correct
outcome. Judge this chart on its own; never compare it with other candidates.

Then **check your plan against the investor's rules** (below) and record every result
with its numbers. A plan that fails a `reject` rule is a `reject` verdict.

## The investor profile and the candidate's risk bucket

Your brief names a `risk_bucket` (`core`, `growth` or `speculative`) — the reward shape
the sector deep dive assigned this company from its catalyst, alongside its
`potential_score`. It is fixed; you never change it, only trade within it.

Read the profile file named in your brief. It sets, shared across every bucket:
`allow_short`, `level_trigger`, `max_hold_trading_days` per horizon and free-text
`notes`. Under `buckets`, your candidate's `risk_bucket` names **its own risk profile**;
every plan field below reads from it:

| Field | What it does to your plan |
|---|---|
| `horizons`, `preferred_horizon` | allowed horizons; pick the preferred one unless the chart clearly suits another (say why) |
| `entry_style` | `pullback`: enter at support inside the trend, not on a breakout; `breakout`: enter on a confirmed break of resistance; `either`: whichever the chart offers. Deviating is a `flag`, not a reject |
| `max_loss_per_trade_pct`, `min_reward_to_risk` | the `max_loss` and `reward_to_risk` rule limits |
| `target_return_pct` | what a full win should roughly return; a target far short of it is worth a line in Risks |
| `max_targets` | how many scale-out targets you may set (1 = a single target) |
| `entry_valid_trading_days` | how long an untriggered entry stays valid; sets `entry_valid_until` |
| `position_size_pct` | not yours: the middleware sizes the position from it |

A plan that can't meet its bucket's limits is rejected, same as any other rule failure —
never loosen the levels to fit, and never borrow a looser bucket's limits to save the
trade.

## Horizons and charts

Pick the horizon, from your bucket's allowed ones, that this setup actually suits,
defaulting to the bucket's `preferred_horizon`.

| Horizon | Typical hold | Primary chart (levels) | Context chart (trend) | Earnings window |
|---|---|---|---|---|
| `swing` | weeks to ~3 months | daily, 1 year | weekly, 2 years | 45 days |
| `long_term` | months to years | weekly, 5 years | daily, 1 year | 30 days |

Read entry, stop and target from the **primary** chart; use the context chart for the
trend. `GetStockPrices` is daily only (at most 500 rows per call); each response comes
back as statistics plus swing highs/lows and the weekly bars built from it. For
`long_term`, fetch 5 years as three date-ranged calls of about 20 months each, in one
message.

## Data to gather

Send steps 1-4 together in one message.

1. **Bars** (`GetStockPrices`) for the charts your horizon needs, up to `as_of`, **plus
   SPY over the same window** for relative strength: compare the two responses' 1m/3m/6m
   returns (stock minus SPY, in percentage points) and say whether the stock leads or
   lags the market.
2. **Indicators.** The price statistics already carry ATR14, RSI14, MACD(12,26,9),
   20-bar VWAP and relative volume (last bar vs its 20-bar average); read them from the
   response. Fetch as useful: `GetAverageTrueRange`, `GetBollingerBands`,
   `GetStochasticOscillator`, `GetOnBalanceVolume`. Or compute from the bars, showing
   the inputs. A breakout on relative volume below 1.0 or with falling OBV is a weaker
   breakout; say so.
3. **Current price** for the stale-entry rule: `GetLiveQuote` (15-min delayed on Plus);
   if unavailable, the last close (`GetLatestClosingPrices`), and say which.
4. **Next earnings:** from the company deep dive's `next_earnings` if given; otherwise
   `GetUpcomingInvestorEvents`, else estimate it from past results 8-Ks (item 2.02,
   `ListFilings`) and mark it estimated.

## The plan

- `entry` and `entry_condition` (what must happen on the chart, e.g. "daily close above
  42.10", written in the bucket's `entry_style`), `stop` (a level the chart justifies:
  below support, beyond an ATR multiple; never an arbitrary percentage), `targets`,
  `horizon`, `chart_timeframe` (the primary chart: `1d` or `1w`), `invalidation` and
  `entry_valid_until`.
- **Targets (scale-out).** `targets` is a list of `{price, fraction}` at chart-supported
  levels, nearest first, at most the bucket's `max_targets`, fractions summing to 1.0.
  One target is `[{price: X, fraction: 1.0}]`. Also write `target`: the size-weighted
  mean of the target prices (Σ price × fraction), which the ratio rules use. Scale out
  only where the chart offers real intermediate resistance (support for a short); don't
  invent levels to fill the quota.
- `entry_valid_until`: the date `entry_valid_trading_days` trading days after `as_of`
  (skip weekends; holidays are a known approximation). An entry not triggered by then
  is expired; the follow-up agent enforces it.
- If the chart-justified stop is too far or the target too close for the profile's
  limits, **reject**; don't move levels to fit the rules.

## Rules (apply every one; show the numbers)

For a long: `e` = entry, `s` = stop, `t` = the size-weighted `target`. For a short,
mirror them.

| Rule | Outcome if it fails | Check |
|---|---|---|
| `plan_price_order` | reject | long: s < e < every target price; short: every target price < e < s. If this fails, skip the ratio rules. |
| `targets_shape` | reject | 1 ≤ len(targets) ≤ `max_targets`, fractions sum to 1.0 (±0.01), prices strictly ordered nearest-first |
| `profile_horizon` | reject | horizon is in your bucket's `horizons` |
| `entry_style` | flag | the entry matches the bucket's `entry_style` (`either` always passes) |
| `chart_timeframe` | flag | levels read from the horizon's primary chart (swing `1d`, long_term `1w`) |
| `profile_short` | reject | a short plan needs `allow_short: true` |
| `max_loss` | reject | \|e − s\| / e × 100 ≤ your bucket's `max_loss_per_trade_pct` |
| `reward_to_risk` | reject | \|t − e\| / \|e − s\| ≥ your bucket's `min_reward_to_risk`, with `t` the size-weighted target |
| `stale_entry` | reject | long: current price > s, and (price − e) / e × 100 ≤ 3.0. Short: mirrored. A price that hasn't reached the entry yet passes. No current price: `flag`. |
| `upcoming_earnings` | flag | next earnings inside the horizon's earnings window from `as_of`, or the date is unknown |

Outcomes: `pass`, `flag` (kept, the user is warned) or `reject`.

## Output

Write `<analysis_folder>/output.md`. Common frontmatter (see `prompts/formats.md`),
plus:

```yaml
ticker: XOM
direction: long
risk_bucket: growth               # from the brief, unchanged
verdict: pass                    # pass | reject
plan:                            # null when there is no chart setup at all
  entry: 118.40
  entry_condition: "daily close above 118.40 (breakout over the August high)"
  entry_valid_until: 2026-10-09  # as_of + the bucket's entry_valid_trading_days
  stop: 111.00
  targets:                       # nearest first, fractions sum to 1.0, at most max_targets
    - {price: 128.00, fraction: 0.5}
    - {price: 140.00, fraction: 0.5}
  target: 134.00                 # size-weighted mean of the target prices; the ratio rules use it
  horizon: swing
  chart_timeframe: 1d
  invalidation: "daily close back below 113.50"
relative_strength: {vs: SPY, "1m_pp": 3.1, "3m_pp": -0.8, "6m_pp": 6.4}   # stock return minus SPY, percentage points
current_price: {price: 117.10, source: live_quote, at: 2026-09-25T19:45:00Z}
rules:
  - {rule: plan_price_order, outcome: pass, detail: "111.00 < 118.40 < 128.00 < 140.00"}
  - {rule: targets_shape, outcome: pass, detail: "2 targets <= max_targets 2; fractions 0.5 + 0.5 = 1.0"}
  - {rule: entry_style, outcome: pass, detail: "breakout entry; bucket entry_style either"}
  - {rule: max_loss, outcome: pass, detail: "7.40 / 118.40 = 6.25% <= 8.0%"}
  - {rule: reward_to_risk, outcome: pass, detail: "(134.00 - 118.40) / 7.40 = 2.11 >= 2.0"}
  - {rule: upcoming_earnings, outcome: flag, detail: "2026-10-31 (confirmed) in 36 days, inside 45"}
```

Body:

```markdown
## Setup
<trend on the context chart, structure on the primary chart, the levels and why>

## Plan
<why these levels: the chart evidence for entry, stop and target, one line each. The
numbers and rule results are in the frontmatter; don't repeat them.>

## Factors
## Risks considered
## Data gaps
```
