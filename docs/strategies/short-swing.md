# Short-term swing strategy: no-news pullback in an uptrend (2-10 trading days, daily chart)

> **Draft, for review; not used by any agent yet.** Research behind it:
> [`research.md`](research.md) §4 and §5. Open decisions: [`open-questions.md`](open-questions.md).

**Definitions** (bars dated on or before `as_of`; a daily bar counts from 16:00 New York on
its date). `C`: the `as_of` close (the signal bar). `SMAn`: simple mean of the last n daily
closes. `RSI2`: Wilder RSI with n = 2 on closes (`price_stats.rsi(bars, 2)`). `ATR`: Wilder
ATR14. `R` = entry − stop.

## 1. Purpose and edge

Buy a sharp, short, **no-news** pullback in a liquid stock that is in a long-term uptrend,
with a limit order below the signal close, and sell the bounce within days. Edge: short-term
reversal as paid liquidity provision (Jegadeesh 1990, Lehmann 1990, Nagel 2012), strongest
for moves without fundamental news (Chan 2003; Da, Liu & Schaumburg 2014), traded only in the
direction of the long-term trend (Connors-Alvarez). Why it might persist: someone has to
absorb forced and over-reacting sellers, and that service is paid. Why it might not:
it has decayed (Khandani-Lo: 0.57%/day in 1998 → 0.13% in 2007 for a simulated contrarian
book), it is thin after costs outside large caps (de Groot et al.), and the win-rate numbers
quoted for RSI(2) are the authors' own. Draws on: Connors-Alvarez RSI(2), Double 7s and
3-day pullbacks; the academic reversal and news/no-news papers.
Not used: NR7/inside-day breakouts (weak on stocks in Bulkowski's data; the classic trade is
intraday), Raschke's 80-20 and gap fades (decided in the first minutes of the session, which
the pipeline can't see).

**Why this family survives the pipeline's constraints.** The plan is computed from a final
close; the entry is a limit at a fixed price below it, so it fills only on further weakness,
whenever the order goes live. A delay of hours costs fills, not edge. The exposed part is the
**exit**: see §10 and [`open-questions.md`](open-questions.md).

## 2. Market/regime filter

New entries only when **SPY's last close > its 200-day SMA** (Connors). Nagel finds reversal
pays most in high-VIX markets, which this rule mostly excludes; a variant is an open question.

## 3. Universe/setup filter (all must hold)

| Test | Rule |
|---|---|
| History | ≥ 220 daily bars |
| Liquidity | `C` ≥ $10; 20-day average dollar volume ≥ **$50M** (costs decide this strategy; de Groot et al.) |
| Trend | `C` > `SMA200`; `SMA50` > `SMA200` |
| Volatility | 1% ≤ `ATR` / `C` ≤ 3.3% (keeps the 3×ATR stop ≤ 10%) |
| No news behind the drop | no earnings report in the last 5 trading days; no material 8-K (the follow-up agent's item list) filed in the last 5 trading days; no bar in the last 3 with \|close-to-close change\| > 3 × `ATR` |
| No news ahead | no earnings report in the next 10 trading days (whole entry window + hold) |

## 4. Setup

`RSI2` ≤ 10 and `C` < `SMA5`. (One oversold measure, the most-tested one; the Double 7s and
3-lower-lows variants describe the same condition.)

## 5. Entry trigger and order

- Buy **limit** at `C` − 0.5 × `ATR` (buy only further weakness; the price is fixed at `as_of`,
  so it doesn't matter when the order goes live).
- Valid **2 trading days** (the sessions after `as_of`). Unfilled → expired, no trade.
- **No trade** if the target (§7) is less than max(0.75 × `ATR`, 1% of `C`) above the entry:
  the expected gain must be many times the round-trip cost.

## 6. Stop

- Entry − **3 × `ATR`**, on a daily **close** at or below it; exit at the next session.
- Why so wide: this is a catastrophe stop, not a thesis stop. Tight stops cut mean-reversion
  trades on the noise they are buying (Connors reports stops "hurt" on stocks); the pipeline
  still requires a stop, and the time stop does most of the risk control. **No trade** if the
  stop is more than 10% below the entry.

## 7. Exits (first one wins)

1. **Target:** a close ≥ `SMA5` as of `as_of` (the plan's static target price) → exit next
   session. Single target, fraction 1.0.
2. **Bounce:** a close above the *current* `SMA5` (Connors' exit; the target moves with it) →
   exit next session.
3. **Time stop:** at the close of the 5th session after the fill → exit next session. The
   profile's max hold for this horizon would be 10 trading days as a backstop.
4. **Stop** (§6).
- No position is held into an earnings report (§3 already excludes it).

## 8. Risk and sizing

- Strategy intent: risk **0.25% of equity** per trade at the 3×ATR stop (shares = 0.0025 ×
  equity / R), capped at the bucket's `position_size_pct`. At most 5 open positions, at most 2
  per sector: signals cluster in market-wide selloffs, so positions are correlated.
- Expected shape (to be confirmed by the backtest, not assumed): win rate well above 50%,
  average win around 1 `ATR`, average loss larger, reward:risk per trade ≈ **0.3-0.7**.
- **Fit with the buckets:**

| Bucket limit | core | growth | speculative | Fit |
|---|---|---|---|---|
| `horizons` | swing, long_term | swing, long_term | swing | **no `short_swing` horizon exists** |
| `max_loss_per_trade_pct` | 5 | 8 | 15 | 3×ATR stops are 3-10%: core rejects most |
| `min_reward_to_risk` | 1.5 | 2.0 | 3.0 | **every bucket rejects every trade** (R:R ≈ 0.3-0.7) |
| `entry_style` | pullback | either | breakout | a pullback: speculative would flag it |
| `entry_valid_trading_days` | 10 | 10 | 5 | strategy wants 2 |
| `target_return_pct` | 8 | 15 | 30 | a 1-4% bounce is far short of every bucket's target |

The strategy can only run with its own limits: an **expectancy rule** (backtested win rate ×
average win − loss rate × average loss > costs) in place of a minimum reward:risk. Proposed as
an open question, not decided.

## 9. Short side

The Connors mirror (below `SMA200`, `RSI2` ≥ 90, sell limit at `C` + 0.5 × `ATR`) exists but is
**not recommended**: stocks drift up, squeezes and takeover gaps are the left tail of a short,
and borrow availability and cost aren't in Equibles. Keep it off unless a backtest shows it
separately.

## 10. Failure modes / when not to take it

- **Exit latency.** The edge is concentrated in the first few sessions and averages ~1 `ATR`;
  close-based triggers already delay each exit to the next session, and today every exit is
  also a user `/trade` command. A further day of delay can erase the average trade.
- **Cadence.** The 12-hour alert cooldown can hold a target or stop alert raised soon after a
  fill alert; the 14-day full re-review is longer than the whole trade.
- **Falling knives:** news the filter missed (8-K item coverage is partial, press releases
  aren't in the filter), sector-wide shocks, market crashes (2008, March 2020) where the
  200-day filters switch off late.
- **Costs and decay:** at a ~1-2% average gain, 10 bp per side is a large share; the reversal
  effect has shrunk since publication.
- Don't take: a drop on earnings or an 8-K, a stock under its 200-day, a gap-down shock bar,
  or a trade whose target is within cost range of the entry.

## 11. Data needed

| Input | Available today? |
|---|---|
| Daily bars (1 year) | yes: `GetStockPrices` |
| `SMA50/200`, `ATR`, dollar volume | yes: `price_stats.py` |
| `RSI2`, `SMA5`, 3-bar max \|change\| in ATR | **new stat** (`rsi()` takes `n`; only RSI14 is reported) |
| SPY 200-day SMA | yes: the SPY call |
| Earnings in the last 5 / next 10 trading days | yes: `GetUpcomingInvestorEvents`, `ListFilings` (item 2.02) |
| Material 8-Ks in the last 5 trading days | yes: `ListFilings` is in the technical agent's tools; the filter is new prompt logic |
| Exit on a close above the current `SMA5`; 5-session time stop | **new** in follow-up |
| Intraday data | not needed, not available |

## 12. Backtest plan

- **Hypotheses.** H1: expectancy > 0 after 10 bp per side, and still > 0 at 20 bp. H2: the
  limit entry below `C` beats buying at `C` (fewer, better trades). H3: the no-news filter
  improves expectancy (compare with and without it). H4: exiting at the next open instead of
  the trigger close costs less than the edge (measures the pipeline's latency cost). H5:
  results have not decayed to zero in 2019-2025 (report 2004-2012, 2013-2018, 2019-2025
  separately).
- **Metrics.** Win rate, average win/loss in R and %, expectancy, max drawdown, exposure,
  trades/year, average hold, worst trade, performance vs SPY buy-and-hold, per regime (VIX
  above/below 20, SPY above/below its 200-day).
- **Sample.** 2004-2025, S&P 500 point-in-time members only (liquidity), all sectors; 2008,
  2020 and 2022 inside. Survivorship and split caveats as in [`investment.md`](investment.md) §12.
- **Costs.** 10 bp per side base case, 5 and 20 bp sensitivities; a limit fills only if the
  low trades **below** the limit (touching is not a fill); exits at the next open; stops gapped
  at the open fill at the open.
- **Parameters.** Fixed up front: everything above. Tuned (at most two, 2004-2018): the `RSI2`
  threshold (5/10) and the limit offset (0 / 0.5 × `ATR`). Hold-out 2019-2025, once.
- **Pipeline `/backtest`.** The one strategy with enough trades for post-cutoff agent
  backtests (mid-2026 on) to say something about performance as well as fidelity; still a
  small sample. Measure agent-vs-code agreement on every `as_of`.
- **Forward test (paper).** Limit fill rate vs the backtest, **exit latency in sessions**
  (trigger close → exit fill), realised R vs the backtest, cost per round trip. With several
  trades a week, 50 closed trades is a realistic first checkpoint; stop early if exit latency
  alone exceeds the backtested average gain.
