# Swing strategy: trend-template contraction (3-12 weeks, daily chart)

> **Draft, for review; not used by any agent yet.** Research behind it:
> [`research.md`](research.md) §3 and §5. Open decisions: [`open-questions.md`](open-questions.md).

**Definitions** (bars dated on or before `as_of`; a daily bar counts from 16:00 New York on
its date). `SMAn`: simple mean of the last n daily closes. `ATR`: Wilder ATR14 on daily bars.
`52wH` / `52wL`: highest / lowest daily close of the last 252 bars; `52wHi`: highest intraday
high of the last 252 bars. `rNm`: N-month return (21 bars a month). `R` = entry − initial stop.
"Sector ETF": the SPDR sector ETF of the candidate's sector.

## 1. Purpose and edge

Buy market and sector leaders in a stage-2 uptrend at a low-risk point: either as a tight
range near the highs breaks (contraction → expansion), or as a pullback to the rising 20-day
MA resumes. Take half at 2R and trail the rest. Edges: intermediate-term momentum and
industry momentum, nearness to the 52-week high, price above rising MAs (all grade A in
[`research.md`](research.md)), plus the practitioners' consensus that entries after
contraction give small, well-defined risk (Minervini, O'Neil, Darvas, Turtle). The pattern
edge itself is only practitioner-evidenced; the filters carry most of the evidence.
Draws on: Minervini trend template + VCP, O'Neil base breakouts and 7-8% loss cap, Darvas
box, Raschke's Holy Grail (resumption trigger), Turtle ATR stops and channel exits.
Not used: post-earnings drift as a trigger (disappeared for large stocks since 2006,
Martineau 2022).

## 2. Market/regime filter

New entries only when **SPY's last close > its 50-day and its 200-day SMA** (O'Neil's "M",
at the swing horizon). The 50-day part is untested here and is the first thing to ablate in
the backtest. When off: no new entries; open trades keep their exits.

## 3. Universe/setup filter (all must hold)

| Test | Rule |
|---|---|
| History | ≥ 260 daily bars |
| Liquidity | last close ≥ $10; 20-day average dollar volume ≥ $20M |
| Trend template | close > `SMA50` > `SMA150` > `SMA200`; `SMA200` > its value 21 bars earlier; close ≥ 1.30 × `52wL`; close ≥ 0.80 × `52wH` |
| Relative strength | `r3m` − SPY `r3m` ≥ 0 and `r6m` − SPY `r6m` ≥ 0; `r3m` ≥ sector ETF `r3m` |
| Sector | sector ETF last close > its 200-day SMA |
| Volatility | 1.5% ≤ `ATR` / close ≤ 6% |

## 4. Setup (the bucket's `entry_style` picks the variant; `either` takes whichever matches)

**A. Contraction breakout (box).** Box = the last 10 bars; `BoxTop` = highest high, `BoxLow` =
lowest low. Require: depth (`BoxTop` − `BoxLow`) / `BoxTop` ≤ 10% **and** ≤ 3.5 × `ATR` / close
(tight for this stock); `BoxTop` ≥ 0.95 × `52wHi` (the box sits at the highs); last close ≤
`BoxTop` (not yet broken out); volume dry-up: mean volume of the 10 box bars ≤ mean volume of
the 50 bars before the box.

**B. Pullback resumption.** `SMA20` > `SMA50`; `SMA20` > its value 5 bars earlier; pullback
depth: highest close of the last 20 bars − last close ≥ 2 × `ATR`; the lowest low of the last
3 bars ≤ `SMA20` + 0.25 × `ATR`; last close ≥ `SMA50`.

## 5. Entry trigger and order

- **A:** buy **stop-limit**, trigger `BoxTop` × 1.001, limit trigger × 1.02.
- **B:** buy **stop-limit**, trigger = the `as_of` bar's high × 1.001, limit trigger × 1.02 (the
  entry is the resumption, not the touch of the MA).
- Valid **5 trading days**. Cancelled earlier if a daily close falls below the stop first.
- No entry if earnings fall within the next 10 trading days.

## 6. Stop

- **A:** `BoxLow` − 0.25 × `ATR`. **B:** lowest low of the last 5 bars − 0.25 × `ATR`.
- Why: beyond the structure (box or pullback low) whose break disproves the setup, with a
  small volatility buffer. **No trade** if the stop is more than 10% below the entry (O'Neil's
  7-8% cut, with room for the buffer), before the bucket's `max_loss` rule.
- Hit on a **daily close** at or below the stop; exit at the next session.

## 7. Exits

- **Target 1:** ½ of the position at entry + 2R; then move the stop to the entry (breakeven).
- **Remainder (design intent): trail.** Exit on a daily close below the lowest low of the prior
  10 bars (Turtle System 1 exit). Until the plan format has a trailing leg, the fallback is
  fixed targets per bucket: growth ½ at 2R + ½ at 4R (weighted 3.0R); speculative ⅓ each at
  2R, 3R and 5R (3.33R); core a single target at 2.5R.
- **Time stop:** 15 trading days after the fill, if target 1 hasn't been hit and the close is
  below entry + 0.5R, exit. **Max hold:** 63 trading days (the profile's `swing` value).
- **Earnings:** if a report falls inside the hold, exit at the last close before it unless
  target 1 has been hit (then hold the rest with the stop at breakeven).

## 8. Risk and sizing

- Strategy intent: risk **0.5% of equity** per trade (shares = 0.005 × equity / R), capped at the
  bucket's `position_size_pct`. At most 6 open positions in this strategy, at most 2 per sector.
- **Fit with the buckets:**

| Bucket limit | core | growth | speculative | Fit |
|---|---|---|---|---|
| `max_loss_per_trade_pct` | 5 | 8 | 15 | stops of 4-10%: core takes the tightest, growth most, speculative all |
| `min_reward_to_risk` | 1.5 | 2.0 | 3.0 | fallback targets give 2.5 / 3.0 / 3.33R: passes, but only because the targets are set to pass; the real payoff is the trail |
| `max_targets` | 1 | 2 | 3 | fits the fallback |
| `entry_style` | pullback | either | breakout | core → B, speculative → A, growth → either |
| `entry_valid_trading_days` | 10 | 10 | 5 | strategy wants 5; the box goes stale after that |

## 9. Short side

Mirrors (close < `SMA50` < `SMA150` < `SMA200`, falling `SMA200`, `r3m`/`r6m` below SPY and the
sector ETF, sector ETF below its 200-day; sell stop-limit under a tight box at the lows).
**Recommend off** at first: the underlying effects are weaker on the short side, squeezes
and takeover gaps hit the stop, and borrow isn't in Equibles.

## 10. Failure modes / when not to take it

- False breakouts: throwbacks and failures are normal (Bulkowski: 47% of recent cups dropped
  substantially within two months of breakout). The 2R partial and breakeven stop limit the
  damage; the win rate may be under 50%.
- Choppy or correcting markets (regime filter); sector rotations out of the leader group.
- Breakout volume can't be checked before a resting stop-limit fills; a low-volume breakout is
  a known weaker case.
- Gaps through the stop on news. Don't take: a box already broken by > 2%, a pullback that
  closed below `SMA50`, or anything with earnings inside the next 10 trading days.

## 11. Data needed

| Input | Available today? |
|---|---|
| Daily bars (1 year + 2-year context) | yes: `GetStockPrices` |
| `SMA20/50/200`, `52wH`, `52wL`, `52wHi`, `r3m`, `r6m`, `ATR`, dollar volume | yes: `price_stats.py` |
| `SMA150`; `SMA200` and `SMA20` slopes | **new stat** |
| Box (10-bar high/low, depth), 20-bar highest close, 3- and 5-bar lows | **new stat** (derivable from raw bars, but error-prone for an agent) |
| Volume means (10 bars, prior 50 bars) | **new stat** (only last-bar relative volume exists) |
| SPY `SMA50`/`SMA200`, `r3m`, `r6m` | yes: the agent's SPY call |
| Sector ETF `r3m` and 200-day SMA | tool yes; **prompt change** + sector→ETF mapping |
| Earnings date | yes |
| Breakeven move after target 1, 10-day-low trail | **new** in follow-up (fixed stop only today) |

## 12. Backtest plan

- **Hypotheses.** H1: expectancy > 0 after costs for A and for B. H2: the portfolio (≤ 6
  positions, 0.5% risk each) beats SPY buy-and-hold on return/max-drawdown. H3: the trail
  beats the fixed fallback targets. H4: each filter (regime, sector, RS, volume dry-up) earns
  its place: drop one at a time on the in-sample period only.
- **Metrics.** Win rate, average R, expectancy, max drawdown, exposure, trades/year, average
  hold, share of stops gapped, CAGR and Sharpe vs SPY buy-and-hold, per sector and per regime.
- **Sample.** 2004-2025, S&P 500 + S&P 400 point-in-time members, all sectors (including 2008,
  2020, 2022). Survivorship and split caveats as in [`investment.md`](investment.md) §12.
- **Costs.** 10 bp per side plus slippage: stop-limit entries fill at trigger + 10 bp, or not at
  all when the open gaps above the limit; close-triggered exits fill at the next open.
- **Parameters.** Fixed up front: everything above. Tuned (at most two, 2004-2018): box depth
  cap (8/10/12%) and the trail (10-day low vs close below `SMA20`). Hold-out 2019-2025, once.
- **Pipeline `/backtest`.** Honest only for post-cutoff dates; use it to measure the agent's
  fidelity to these rules (same verdict and levels as the code) and the rejection rate.
- **Forward test (paper).** Entry fill rate, slippage, exit latency, realised R vs backtest,
  agent-vs-code agreement. Expect a handful of trades a month: 30 closed trades is the first
  checkpoint, and even then only a gross divergence from the backtest is informative.
