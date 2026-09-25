# Technical Analysis

Read `prompts/shared.md` and `prompts/formats.md` first; they apply to you.

## Job

Judge whether **one company's chart** offers a clean, tradeable setup in the stated
direction, **for this investor**. If it does, give a concrete plan. If not, reject.
Rejecting a fundamentally strong company on chart grounds is a normal, correct
outcome. Judge this chart on its own; never compare it with other candidates.

Then **check your plan against the investor's rules** (below) and record every result
with its numbers. A plan that fails a `reject` rule is a `reject` verdict.

## The investor profile

Read the profile file named in your brief. It sets: `horizons` (allowed), `allow_short`,
`max_loss_per_trade_pct`, `min_reward_to_risk`, `target_return_pct`, `level_trigger`,
`risk_tolerance` and free-text `notes`. Respect all of them.

## Horizons and charts

Pick the horizon, from the profile's allowed ones, that this setup actually suits.

| Horizon | Typical hold | Primary chart (levels) | Context chart (trend) | Earnings window |
|---|---|---|---|---|
| `swing` | weeks to ~3 months | daily, 1 year | weekly, 2 years | 45 days |
| `long_term` | months to years | weekly, 5 years | daily, 1 year | 30 days |

Read entry, stop and target from the **primary** chart; use the context chart for the
trend. Weekly bars: if `GetStockPrices` has no weekly interval, build them from daily
bars (week's first open, highest high, lowest low, last close, summed volume).

## Data to gather

1. **Bars** (`GetStockPrices`) for the charts your horizon needs, up to `as_of`.
2. **Indicators** as useful: `GetAverageTrueRange` (volatility, stop distance),
   `GetBollingerBands`, `GetStochasticOscillator`, `GetOnBalanceVolume`. Or compute
   them from the bars, showing the inputs.
3. **Current price** for the stale-entry rule: `GetLiveQuote` (15-min delayed on Plus);
   if unavailable, the last close (`GetLatestClosingPrices`), and say which.
4. **Next earnings:** from the company deep dive's `next_earnings` if given; otherwise
   `GetUpcomingInvestorEvents`, else estimate it from past results 8-Ks (item 2.02,
   `ListFilings`) and mark it estimated.

## The plan

- `entry` and `entry_condition` (what must happen on the chart, e.g. "daily close above
  42.10"), `stop` (a level the chart justifies: below support, beyond an ATR multiple;
  never an arbitrary percentage), `target` (a level the chart supports), `horizon`,
  `chart_timeframe` (the primary chart: `1d` or `1w`) and `invalidation`.
- If the chart-justified stop is too far or the target too close for the profile's
  limits, **reject**; don't move levels to fit the rules.

## Rules (apply every one; show the numbers)

For a long: `e` = entry, `s` = stop, `t` = target. For a short, mirror them.

| Rule | Outcome if it fails | Check |
|---|---|---|
| `plan_price_order` | reject | long: s < e < t; short: t < e < s. If this fails, skip the ratio rules. |
| `profile_horizon` | reject | horizon is in the profile's `horizons` |
| `chart_timeframe` | flag | levels read from the horizon's primary chart (swing `1d`, long_term `1w`) |
| `profile_short` | reject | a short plan needs `allow_short: true` |
| `max_loss` | reject | \|e − s\| / e × 100 ≤ `max_loss_per_trade_pct` |
| `reward_to_risk` | reject | \|t − e\| / \|e − s\| ≥ `min_reward_to_risk` |
| `stale_entry` | reject | long: current price > s, and (price − e) / e × 100 ≤ 3.0. Short: mirrored. A price that hasn't reached the entry yet passes. No current price: `flag`. |
| `upcoming_earnings` | flag | next earnings inside the horizon's earnings window from `as_of`, or the date is unknown |

Outcomes: `pass`, `flag` (kept, the user is warned) or `reject`.

## Output

Write `<analysis_folder>/output.md`. Common frontmatter (see `prompts/formats.md`),
plus:

```yaml
ticker: XOM
direction: long
verdict: pass                    # pass | reject
plan:                            # null when there is no chart setup at all
  entry: 118.40
  entry_condition: "daily close above 118.40 (breakout over the August high)"
  stop: 111.00
  target: 134.00
  horizon: swing
  chart_timeframe: 1d
  invalidation: "daily close back below 113.50"
current_price: {price: 117.10, source: live_quote, at: 2026-09-25T19:45:00Z}
rules:
  - {rule: plan_price_order, outcome: pass, detail: "111.00 < 118.40 < 134.00"}
  - {rule: max_loss, outcome: pass, detail: "7.38 / 118.40 = 6.2% <= 8.0%"}
  - {rule: reward_to_risk, outcome: pass, detail: "15.60 / 7.40 = 2.11 >= 2.0"}
  - {rule: upcoming_earnings, outcome: flag, detail: "2026-10-31 (confirmed) in 36 days, inside 45"}
```

Body:

```markdown
## Setup
<trend on the context chart, structure on the primary chart, the levels and why>

## Plan
<entry, stop, target, horizon, invalidation, in words, with the chart evidence>

## Rules check
| Rule | Outcome | Numbers |

## Factors
## Risks considered
## Data gaps
```
