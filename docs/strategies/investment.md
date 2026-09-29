# Investment strategy: stage-2 leader (6+ months, weekly chart)

> **Draft, for review; not used by any agent yet.** Research behind it:
> [`research.md`](research.md) §2 and §5. Open decisions: [`open-questions.md`](open-questions.md).

**Definitions** (all from bars dated on or before `as_of`; a daily bar counts from 16:00 New
York on its date). Weekly bars are ISO weeks built from daily bars, as `price_stats.weekly`
does; only **completed** weeks count (a week counts once `as_of` is past its Friday 16:00 New
York, or a bar from a later week exists). `W10`, `W30`: simple means of the last 10 / 30 completed weekly closes. `ATR`: Wilder
ATR14 on daily bars. `52wH`: highest daily close of the last 252 bars. `R12-1`: 12-month
return excluding the last month, `(1 + r12m) / (1 + r1m) − 1` with 252 and 21 bars. `R` = entry
− initial stop. "Sector ETF": the SPDR sector ETF of the candidate's sector.

## 1. Purpose and edge

Own the strongest stocks in the strongest sectors while their long-term trend is intact, and
step aside when it breaks. Edges: trend persistence and momentum (Jegadeesh-Titman; industry
momentum, Moskowitz-Grinblatt), anchoring near the 52-week high (George-Hwang), price above a
rising long MA (Avramov et al.; the only part of Weinstein's stages with measured edge), and
a right-skewed payoff captured by trailing exits (Wilcox-Crittenden). Why it should persist:
these are under-reaction effects replicated across decades and markets, though smaller after
publication; the drawdown cut from the trend filter (Faber) is the most robust part.
Draws on: Weinstein, Faber, Antonacci (dual momentum), 12-1 momentum, George-Hwang,
Minervini's MA stacking, Wilcox-Crittenden, Clenow's index filter.

## 2. Market/regime filter

New entries only when **SPY's last close > SPY's 200-day SMA**. When off, no new entries;
open positions keep their own exits (the stock-level trend exit is the regime exit).

## 3. Universe/setup filter (all must hold)

| Test | Rule |
|---|---|
| History | ≥ 300 daily bars |
| Liquidity | last close ≥ $10; 20-day average dollar volume ≥ $20M |
| Trend | last weekly close > `W30`; `W30` > `W30` four completed weeks earlier; `W10` > `W30` |
| Near highs | last close ≥ 0.85 × `52wH` |
| Momentum, absolute and relative | `R12-1` > 0 and `R12-1` ≥ SPY's `R12-1` |
| Sector | sector ETF last close > its 200-day SMA; stock 6-month return ≥ sector ETF 6-month return |
| Volatility | `ATR` / last close ≤ 5% |

## 4. Setup (the bucket's `entry_style` picks the variant; `either` takes whichever matches)

**A. Base breakout.** Base = the last `N` completed weeks, `N` the largest value in 5..52 for
which depth = (highest weekly high − lowest weekly low) / highest weekly high ≤ 25%. Pivot `P`
= the highest weekly high in the base. Require: `N` ≥ 5; the week that made `P` is ≥ 3 weeks
before the last completed week; last weekly close in [0.92 × `P`, `P`); final contraction: the
high−low range of the last 3 completed weeks ≤ 10% of `P`; volume dry-up: mean weekly volume
of those 3 weeks < mean weekly volume of the base.

**B. Pullback to the 10-week MA.** `W10` > `W10` two completed weeks earlier; last close ≤
0.95 × `52wH` (a real pullback); last close in [`W10`, `W10` + 2 × `ATR`].

## 5. Entry trigger and order

- **A:** buy **stop-limit**, trigger `P` × 1.001, limit `P` × 1.03 (inside the pipeline's
  3% `stale_entry` drift).
- **B:** buy **limit** at `W10` + 0.25 × `ATR` (as of `as_of`; the order is not moved as `W10`
  changes).
- Valid **10 trading days**, but never across an earnings date: if earnings fall inside the
  window, the entry expires the trading day before.

## 6. Stop

- **A:** lowest low of the last 3 completed weeks (the final contraction) − 0.5 × `ATR`.
- **B:** min(`W30`, lowest low of the last 4 completed weeks) − 0.5 × `ATR`.
- Why: just beyond the structure whose failure disproves the setup, with a volatility buffer
  against noise. **No trade** if the stop is more than 15% below the entry (strategy cap),
  before the bucket's `max_loss` rule is applied.
- Hit on a **daily close** at or below the stop (`level_trigger: close`); exit at the next
  session.

## 7. Exits

- **Trailing stop**, updated each completed week: stop = max(current stop, lowest weekly low
  of the last 10 completed weeks − 0.5 × `ATR`).
- **Trend failure:** a completed weekly close below `W30` → exit at the next session.
- **Target (design intent):** no fixed target for most of the position; the edge is the right
  tail. At most one partial: ⅓ at max(`P` + base depth × `P`, entry + 3R) (A) or entry + 3R (B);
  the rest trails. The current plan format needs targets summing to 1, so this needs a format
  change (open question); until then the single target at that level is the fallback, which
  truncates the tail.
- **Time stop:** 13 weeks after the fill, a weekly close below the entry → exit.
- **Earnings:** holding through reports is accepted (a 6+ month hold spans two or more); no
  new entry across one (§5). Material news goes through the follow-up's normal re-review.

## 8. Risk and sizing

- Strategy intent: risk **0.5% of equity** per trade: shares = 0.005 × equity / R, capped at
  the bucket's `position_size_pct` of equity. Maximum 10 open positions in this strategy.
- The pipeline today sizes by notional (`position_size_pct`), not by risk: a 3% position with a
  12% stop risks 0.36% of equity, so the cap usually binds first. Fine for forward testing.
- **Fit with the buckets** (`profile.example.json`):

| Bucket limit | core | growth | speculative | Fit |
|---|---|---|---|---|
| `horizons` | swing, long_term | swing, long_term | swing only | speculative can't use this strategy |
| `max_loss_per_trade_pct` | 5 | 8 | 15 | weekly structure stops are typically 8-15%: **core (preferred `long_term`!) rejects most setups**; growth some |
| `min_reward_to_risk` | 1.5 | 2.0 | 3.0 | fine with a 3R reference target; meaningless for a trailed exit |
| `max_targets` | 1 | 2 | 3 | the ⅓-partial + trail design needs a "trail" leg, not more targets |
| `entry_style` | pullback | either | breakout | core → B, growth → A or B |

## 9. Short side

Mirrors as a stage-4 breakdown (weekly close < falling `W30`, `W10` < `W30`, within 15% of the
52-week low, `R12-1` < 0 and below SPY's, sector ETF below its 200-day; sell stop-limit under
the base low). **Recommend off** until the long side is validated: the MA and momentum effects
are stronger on the long side (Avramov et al.), losers rebound violently after market lows
(Daniel-Moskowitz), borrow availability and cost aren't in Equibles, and takeovers gap
through stops.

## 10. Failure modes / when not to take it

- V-shaped recoveries (2009, 2020): the filter re-enters late; momentum crashes hit leaders.
- Sideways markets: whipsaw around `W30`; many small losses.
- Earnings or news gaps through the stop; losses larger than R.
- Few setups: most candidates will fail the filter on any given day (a rejection, not an error).
- Don't take: a stock that already ran > 3% past `P` (stale), a base under 5 weeks, a sector
  ETF below its 200-day, or a stop that only fits the bucket by being moved.

## 11. Data needed

| Input | Available today? |
|---|---|
| Daily bars, ≥ 300 (5 years for context) | yes: `GetStockPrices` (≤ 500 rows per call; 3 calls for 5 years) |
| `ATR`, 20-day dollar volume, `52wH` and distance, 12m/1m returns | yes: `price_stats.py` |
| `R12-1` | derivable from `price_stats` returns (agent arithmetic); better as a stat |
| Weekly bars | yes, last 104 weeks in `price_stats`, **but the last row includes the incomplete current week**: needs a "completed weeks only" flag |
| `W10`, `W30` and their slopes | **new stat** (only daily SMA20/50/200 exist) |
| Base `N`, depth, `P`, pivot age, 3-week range, volume dry-up | **new stat** |
| SPY 200-day SMA, SPY `R12-1` | yes: the SPY `GetStockPrices` call the agent already makes |
| Sector ETF 200-day SMA and 6-month return | tool yes (`GetStockPrices` on the ETF); **prompt change** and a sector→ETF mapping in the brief |
| Next earnings date | yes: brief or `GetUpcomingInvestorEvents` / `ListFilings` |
| Weekly trailing stop and `W30` exit in follow-up | **new**: follow-up and the plan format know only a fixed stop |

## 12. Backtest plan

- **Hypotheses.** H1: expectancy per trade > 0 after costs, for A and B separately. H2: a
  portfolio of these trades (equal risk, ≤ 10 positions) beats SPY buy-and-hold on
  return/max-drawdown, with lower drawdown in 2008 and 2022. H3: the regime filter reduces
  drawdown more than it costs return. H4: trailing beats the fixed 3R target (tests the
  right-tail claim and the format question).
- **Metrics.** Win rate, average R, expectancy (R and %), profit share of the top 10% of
  trades, max drawdown, exposure (% of days invested), trades/year, CAGR and Sharpe vs SPY
  buy-and-hold, results per sector and per regime (SPY above/below its 200-day).
- **Sample.** Daily bars 2004-2025 (2008, 2011, 2015-16, 2018 Q4, 2020, 2022 inside), all 11
  sectors, S&P 500 + S&P 400 members **as of each date** (current constituents are survivorship
  biased; `GetIndexChanges` may allow a point-in-time list, unverified). Equibles restates
  history for splits: percent moves are fine, the $10 floor uses restated prices.
- **Costs.** 10 bp per side; entries fill at trigger + 10 bp, or not at all if the session
  opens above the limit; close-triggered exits fill at the **next open** (the pipeline's real
  latency); stop gaps fill at the open.
- **Parameters.** Fixed up front: everything above. Tuned (at most two, on 2004-2018 only):
  maximum base depth (20/25/30%) and the trailing rule (10-week low vs `W30` close only).
  Hold-out 2019-2025, run once.
- **Pipeline `/backtest`.** Agent-based and point-in-time, but honest only after the models'
  training cutoff (mid-2026), so it can't produce a performance sample for a 6+ month
  strategy. Use it for **fidelity**: on each `as_of`, does the technical agent reach the same
  setup verdict and levels as the mechanical code? Report the agreement rate and level
  differences in ATR.
- **Forward test (paper).** Entry fill rate vs the backtest, slippage vs the planned entry,
  exit latency (trigger close → exit fill, in sessions), realised R vs the backtest
  distribution, stop gaps, and agent-vs-code agreement. At a few trades a month, a performance
  verdict takes years; judge the first year on fidelity and drawdown behaviour, and trust the
  mechanical backtest for expectancy.
