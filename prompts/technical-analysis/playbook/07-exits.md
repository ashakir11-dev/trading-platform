# 07 - Exiting a trade

## How to use this file

- Write every exit BEFORE the entry is final: section 2 = fields and pre-entry checklist; 3-4 = initial stop and its execution; 5-6 = targets and scale-out math; 7 = scale vs full exit; 8-9 = trailing and breakeven; 10 = exit cues; 11 = clocks; 12 = earnings; 13 = per-trade_type cheat sheet; 14 = grading exits.
- Every stop, target, trail, time or event exit is computed from daily/weekly OHLCV with inputs shown. No stop or target without a chart reason (role.md). Stops only move toward the trade.
- Labels: [A] academic/replicated, [P] practitioner study, [C] convention, [S] speculative/contested, [math] arithmetic identity. "House default" = a starting value chosen for this playbook, not a published result.
- Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).
- Examples are hypothetical. Neighbours: `01-chart-reading.md` (levels 6, liquidity 7.3, extension 9, regime 12), `02-indicators.md` (formulas, parameters 4), `03-chart-patterns.md` (stops 2.4, measured moves 2.5, throwbacks 2.6), `04-strategies-and-setups.md` (setups), `05-timeframes-and-trade-types.md` (stop width 7.1-7.2, reachability 5.3, graduation 13), `06-entries.md`, `08-trade-plan-and-timeline.md` (clocks 4, checkpoints 6, time limits 8, exit codes 3.1), `09-events-hype-and-fear.md` (earnings 2-4, hype 7).

## 1. Evidence ledger

| Claim | Label | Consequence |
|---|---|---|
| Driftless random walk: no stop, target, trail or scale-out changes expected profit; P(target before stop) = (e - s)/(t - s) = 1/(1 + RR). | [math] | Exits express an edge, never create one; at RR 2 a coin-flip market hits target 1/3 of the time. |
| With positive drift a stop lowers expected return; it adds a "stopping premium" only under momentum or regime switching (Kaminski and Lo 2014). | [A] | Firm stops suit trend setups; mean-reversion stops sit at true invalidation. |
| Tight stops on single US stocks tend to underperform buy-and-hold after costs; they help where serial correlation is high (Lo and Remorov 2017). | [A] | Never stop inside normal noise (3). |
| A 10% stop per stock in a monthly momentum portfolio cut the worst month from -49.79% to -11.36% (1926-2013) and more than doubled Sharpe (Han, Zhou and Zhu 2016, working paper; gaps make real fills worse). | [A] (WP) | For momentum longs the stop is part of the edge. |
| On the S&P 500, slow trend filters beat buy-and-hold on risk; popular stop rules added nothing; monthly beat frequent decisions (Clare, Seaton, Smith and Thomas 2013). | [A] | Investment exits = slow trend breaks on weekly/monthly closes. |
| Pullback mean-reversion systems did worse with percentage stops of any size tested (Connors and Alvarez 2008, own tests). | [P] | Mean reversion: time stop + structural/catastrophe stop. |
| Random entries + 3 x ATR trail + 1% risk sizing were profitable, ~38% winners (Tharp, small illustrative futures test). | [P] | Trend results come from exits and sizing: trail runners. |
| Buying all-time highs with a 10-ATR trail was profitable over 22 years, 18,000+ trades, carried by a minority of big winners (Wilcox and Crittenden 2005). | [P] | Fixed targets on trend trades cut the tail that pays for losers. |
| Investors sell winners ~1.5 times as readily as losers; winners sold beat losers kept by ~3.4% next year (Odean 1998). | [A] | Pre-commit exits; never widen a stop. |
| Take-profits cluster at round numbers, stops just beyond them (Osler 2003, FX); US stocks show order imbalances around round prices (Bhattacharya, Holden and Jacobsen 2012). | [A] | Targets just BELOW round numbers/resistance; stops a little BEYOND round numbers and obvious lows ([C] practice). |
| Volume spikes at 52-week highs (Huddart, Lang and Yetman 2009); nearness to it predicts continuation (George and Hwang 2004). | [A] | 52-week high = partial-profit spot, not a runner ceiling. |

## 2. The exit plan: write it before entry

role.md carries `stop`, `target`, `invalidation`; the rest goes one line each in `## Plan` until the `08` 12 YAML is adopted.

| Field | Content (rule: section) |
|---|---|
| `trade_type` | short_swing / swing / long_swing / investment: selects every column of 13 |
| `stop`, `stop_basis` | rule-checked stop and its arithmetic, e.g. "pivot low 47.60 (2026-09-12) - 0.5 x ATR14 1.20 = 47.00" (3); weekly types: daily-close hard stop (4.3) |
| `stop_trigger` | `close` or `intraday` (profile `level_trigger`), daily or weekly bar (4.1) |
| `catastrophe_stop` | optional resting order ~1 ATR below a close-stop (4.3) |
| `targets` | {level, fraction, basis} for T1, T2, runner; fractions sum to 1 (5, 6.5) |
| `target` (role) | = T1; `reward_to_risk` is checked on it (6.4) |
| `runner_trail`, `breakeven_rule` | method, parameters, activation (8); when the stop reaches entry (9) |
| `progress_check`, `cp2`, `max_hold` | bars, minimum progress, latest date, action at the limit (11; `08` 4, 6, 8) |
| `event_plan` | each report/event through the latest max-hold date and the action before it (12) |
| `exit_cues` | the 2-4 cues from 10 that fit THIS setup |
| `invalidation` | chart event proving the thesis wrong; may precede the stop (close back inside the base) |
| `worst_case` | gap-through-stop loss line (4.2) |

Pre-entry checklist (all yes, else reject or wait): (1) the stop is where the setup is wrong, not where numbers fit (3.5); (2) |e - s|/e <= `max_loss_per_trade_pct`, overshoot and worst-gap lines written (4.1-4.2); (3) T1 sits below the first graded resistance and alone passes `min_reward_to_risk` (6.4); (4) T1 reachable before its deadline, k <= ~1.5 (`05` 5.3); (5) scale-out, trail, breakeven, progress check and max-hold date written; (6) every report through the latest max-hold date has an action (12); (7) liquidity allows the exit (4.5).

## 3. The initial stop

### 3.1 Principle

The stop is where the premise is false: a breakout back in its base, a pullback below its higher low, a lower low in a trend. Structure decides WHERE; ATR decides HOW FAR BEYOND; the profile cap decides WHETHER to trade [C]. Structural stop beyond the cap: reject, or wait for an entry nearer the level. Never tighten to fit (role.md).

### 3.2 Methods (long)

| Method | Formula | Use | Label |
|---|---|---|---|
| Swing low | last confirmed pivot low below entry (hook 5-bar pivots; 2-bar pivots from raw rows for short_swing) - buffer | pullbacks, trends | [C] |
| Base / handle / flag low | low of the final contraction, handle or flag - buffer | breakouts (`03` 2.4) | [C] |
| Breakout level | pivot P - buffer; close back below P = failed | short_swing breakouts | [C] |
| Breakout-bar / gap-day low | trigger or gap bar low - buffer | short_swing momentum, post-earnings (`09` 4.3) | [C] |
| Volatility only | e - k x ATR14, k 1.5-3 | no structure within reach (blue sky) | [C]; ATR scaling [P] (Turtle 2N, LeBeau) |
| Combined (default) | min(structure - b x ATR14, e - k_min x ATR14): the FARTHER of structure-with-buffer and a minimum ATR distance | all types | [C] |
| Moving average | close below EMA21 / SMA50 / 10-week / 30-week - buffer | trail or invalidation; initial stop only if it coincides with structure | [C] |
| Elder SafeZone | prior low - c x mean downside penetration (low_{i-1} - low_i on bars where low_i < low_{i-1}, 10-20 bars), c 2-3 | noise-based alternative | [C] (Elder 2002) |
| Percentage | e x (1 - p) | never as placement: the 8% cap (like O'Neil's 7-8%) limits a chart stop, it does not place one | [S] as placement |

Why percentage stops are inferior [arithmetic]: 8% is ~8 ATR on a 1%-ATR stock (beyond any structure, losses bigger than needed) and ~1.6 ATR on a 5%-ATR stock (inside noise, hit at random). The evidence for fixed stops (Han, Zhou and Zhu at 10%) is about wide stops on portfolios, not tight percentage stops on single trades.

### 3.3 Buffers and placement

| Rule | Default | Label |
|---|---|---|
| Buffer, daily level | 0.25-0.5 x ATR14 short_swing; 0.5-1 x ATR14 swing; upper end in `intraday` mode, high ATR%, or $5-20M dollar volume | [C] house |
| Buffer, weekly level | 0.25-0.5 x weekly ATR14 (weekly bars) | [C] house |
| Minimum distance from entry | 0.75 ATR14 short_swing; 1 ATR14 swing and longer | [C] |
| Round numbers | stop on/just above a whole or half dollar goes below it (50.05 -> 49.85) | [C] (Weinstein); [A] clustering |
| Obvious lows / zones | a buffer beyond an exact prior low and beyond the FAR edge of the zone (`01` 6.2) | [C]; [A] (Osler, FX) |

### 3.4 Width and feasibility per trade_type (detail `05` 7.1-7.2)

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Typical distance | 1.5-2.5 daily ATR | 2-3.5 daily ATR | 1-2 weekly ATR | 1.5-3 weekly ATR |
| Max daily ATR% under an 8% cap | 3.2-5.3% | 2.3-4.0% | ~1.8-3.6% | ~1.2-2.4% |

Weekly columns assume weekly ATR ~ 2.2 x daily (sqrt(5) scaling, approximate [math]); use the stock's actual weekly ATR14. Feasibility [math]: ATRs needed x ATR% <= cap; 3 ATR at 3.1% = 9.3% > 8 -> reject or wait. Invalidation levels per type: section 13.

### 3.5 Rule-fitted stop tests (any true = reject the plan)

- Inside the latest consolidation, between pivots, with no level under it.
- Exactly at e x 0.92, or at a round R multiple with no structure there.
- Moved after `max_loss` or `reward_to_risk` failed.
- Less than 1 ATR from entry on swing or longer.
- A clear higher low lies between entry and stop: the setup fails earlier; use that low.

## 4. Stop execution: close vs intraday, gaps, liquidity

### 4.1 Trigger mode (profile `level_trigger`)

| | `close` (example profile) | `intraday` |
|---|---|---|
| Wording | "exit if a daily close is below 47.00" | "sell-stop at 47.00" |
| Gains / costs | ignores wicks and stop runs, verifiable on daily bars / the close can be well below the level | loss capped near the stop in orderly trade / whipsaws on spikes that recover |
| Planning | realised loss ~ (e - s) + ~0.5 x ATR14 (house [C]); if that exceeds `max_loss`, say so in Risks and lower confidence | upper end of the buffer range |
| Human action | sell near the close (quote 15-min delayed) or next open; the plan says which | resting order |

Rule checks use `stop` as written; the overshoot is a disclosure. Trails follow the same mode.

### 4.2 A stop is not a price

- A triggered stop becomes a market order and can fill far through the level in a gap; a stop-limit may not fill at all (SEC investor bulletin).
- Gap test: gap_t = open_t / close_{t-1} - 1 over 252 bars, earnings days excluded; count gaps <= -(e - s)/e and report the worst in % and ATR. >= 3 such gaps = stop inside gap noise: longer type if feasible, else reject (`05` 7.5) [C].
- `worst_case` = (e - s) + s x |worst non-earnings gap|, in % of e, beside |e - s|/e; with a report in the hold add the HEMmax line (`09` 2.3).
- Gap-prone stocks: prefer structural stops well inside the cap (e.g. <= 6% under 8%) [C].

### 4.3 Weekly invalidation with a daily hard stop

A week can fall further than the cap before it closes. long_swing and investment plans carry `invalidation` = weekly close below W (weekly structure - buffer) AND rule-checked `stop` = hard stop H on a daily close, H >= e x (1 - max_loss/100). If W < H the structure and the cap disagree: trade only if H is itself a daily structural level; else reject or wait (`05` 7.2). Optional `catastrophe_stop` in `close` mode: resting order ~1 ATR below the close-stop [C]; it does not cover overnight gaps.

### 4.4 Gaps on the exit side [C house rules]

| At the open | Plan instruction to the human |
|---|---|
| Below the stop / hard stop | `intraday`: the stop fills at market; accept it. `close`: exit at that close if still below (`09` 4.3 D1). Never wait for "a bounce back to the stop"; never lower the stop. |
| Below the trail, above the initial stop | same, for the trailed portion |
| Above T1 | the resting sell-limit fills at the better open; runner stop to gap-day low - 0.25 ATR if the day closes in its upper half on RVOL >= 1.5; a close in the lower half back below T1 = reversal cue: short_swing/swing sell the runner too |
| Up, target not reached | no action at the open; after 2 closes holding the gap, trail to the gap-day low (`09` 4.3) |
| Up after a long run, then fading | exhaustion-gap cue (10) |

### 4.5 Liquidity and dividends

- $5-20M dollar volume (`01` 7.3): exit with limits, wider buffers, scale out one level earlier; < $5M is not traded as short_swing/swing. Position large versus daily dollar volume: exit over several sessions, selling into up days [C].
- Ex-dividend in the hold with dividend >= 0.1 x ATR14: a close-stop within one dividend of the ex-date close can trip on the payout alone; follow `08` 7.3.

## 5. Targets

### 5.1 Sources (long)

| Source | Compute | Label | Use |
|---|---|---|---|
| Resistance / supply zone | lower edge of the next zone: swing highs, base tops, heavy-volume reversal bars, unfilled gap-down windows (`01` 6) | [C] | first choice: zone edge - 0.25 x ATR14 |
| 52-week / all-time high | hook's 52-week intraday high | [A] | partial just below; a close above = continuation cue |
| Measured move | pattern height or pole from the breakout (`03` 2.5) | [P] full height reached only about half the time for several patterns (Bulkowski) | base case 0.5-0.75 x height; full height = T2 |
| Prior leg (AB = CD) | prior impulse added to the pullback low | [C] | swing T2 |
| ATR projection | e + m x ATR14 (daily or weekly) | [C] | blue sky only; check k |
| R multiple | e + n x (e - s) | [C] | runner checkpoint only; never the rule-checked `target` (passes R:R by construction) |
| Mean | SMA5 / SMA10 / SMA20 | [P] (Connors-Alvarez: close above SMA5) | mean-reversion target |
| Band / range edge | Bollinger upper (SMA20 + 2 x population SD of 20 closes), channel line, range top | [C] | range trades: edge - buffer |
| Anchored VWAP overhead | AVWAP from a prior major high or gap-down day (`02` 7.10) | [C] | modifier: holders reach breakeven there |
| Round number | whole/half/10 above | [A] clustering | modifier: target just below |
| Fibonacci extension 1.272/1.618 | prior leg x ratio from the pullback low | [S] (tests find no reliable edge for the ratios alone) | only where it coincides with a level |

### 5.2 Placement rules

1. Sell before the crowd: target = level - 0.25 x ATR14, and below any round number inside that buffer [C; A clustering].
2. Two or more graded levels between entry and a candidate: T1 = the first (`01` 6.4).
3. The rule-checked target is the base case, never the stretch.
4. Reachability k = (t - e)/(0.63 x ATR14 x sqrt(max-hold bars)) <= 1.5 (`05` 5.3; weekly: weekly ATR14 and weeks) [C, random-walk scaling]; T1 deadline = min(max hold, 2 x expected bars to T1) (`08` 6.1).

### 5.3 Picking T1, T2, runner

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| T1 (= `target`) | nearest daily resistance / prior swing high, >= 2R | next daily/weekly resistance or 52-week high | next weekly resistance or 0.5-0.75 x weekly measured move | first major weekly/monthly resistance or prior all-time high |
| T2 | full measured move / prior leg; often none | full measured move or prior leg | full weekly measured move | multi-year measured move (review point) |
| Runner | none or small; out by max hold | trailed to max hold | weekly trail | position rides a weekly trail |
| Blue sky (no supply in 2 years) | 0.5-0.75 x measured move or 2-3 ATR projection, k <= 1.5 | same; 2-3R only as a checkpoint | measured move; trail beyond | no fixed target; trail and review |

"2-3R" objectives anywhere in the playbook are runner checkpoints; the rule-checked `target` is always a chart level (resistance, measured move or ATR projection).

## 6. Single vs multiple targets, and scale-out math

### 6.1 Formulas [math]

R = e - s; fractions f_i (sum 1) exited at x_i.
- Result (R) = sum f_i x (x_i - e)/R. Planned blended R:R = sum f_i x (T_i - e)/R, the runner at its last FIXED target or at breakeven (say which). Floor after T1 = f_1 x (T1 - e)/R.
- Expectancy = win% x avg win(R) - loss% x avg loss(R); with scale-outs, sum over paths of P(path) x result.
- Break-even win rate = 1/(1 + RR); with round-trip cost c in R: (1 + c)/(1 + RR) (`05` 7.5).

### 6.2 Hold-or-sell rule (every scale-out and trail decision)

At price P with stop S' and next target T2, holding beats selling iff q > (P - S')/(T2 - S'), q = P(T2 before S'). Under a driftless random walk q equals the ratio [math]. So: hold a runner only where the setup shows CONTINUATION at this horizon (trend, momentum, 52-week-high breakouts, post-earnings drift [A]); exit fully where it is MEAN-REVERTING or RANGE-BOUND (short-term reversal [A], range tops, the mean). Raising S' lowers the hurdle and q together; breakeven never adds expectancy by itself.

### 6.3 Worked arithmetic (hypothetical probabilities)

XYZ: e 50.00, s 47.00 (R 3.00), T1 56.00 (+2R), T2 62.00 (+4R). Assume P(T1 first) = 0.45; from T1, P(T2 before 47.00) = 0.55 and P(T2 before 50.00) = 0.40.

| Plan | Paths (probability: result) | E |
|---|---|---|
| A: all at T2, stop fixed | 0.2475: +4R; 0.7525: -1R | +0.24R |
| B: 1/2 T1, 1/2 T2, stop fixed | 0.55: -1R; 0.2475: +3R; 0.2025: +0.5R | +0.29R |
| C: 1/2 T1, stop to breakeven, 1/2 T2 | 0.55: -1R; 0.18: +3R; 0.27: +1R | +0.26R |
| D: all at T1 | 0.45: +2R; 0.55: -1R | +0.35R |

Here the runner does not pay (0.55 < hurdle 9/15 = 0.60; 0.40 < 6/12 = 0.50); with q = 0.70, A and B beat D. Continuation odds are a property of the setup family, not of comfort. Scaling out cuts variance and give-back and changes expectancy only through q; C vs B is the small price of a no-loss runner.

### 6.4 How `reward_to_risk` is checked when scaling out

- role.md checks one `target`: `target` = T1, and T1 alone must pass `min_reward_to_risk` (`05` 7.3; `08` 10).
- Blended R:R and the floor after T1 are information in `## Plan`; they cannot rescue a T1 below the minimum (all files agree: `04` 1.4, `08` 10).
- Never state a blend with a T2 that is not a chart level or fails k <= 1.5.

### 6.5 Scale-out templates ([C] house fractions; aligned with `08` 10)

| Setup family | Template | Why |
|---|---|---|
| Breakout / trend, swing | 1/2 at T1; 1/2 at T2 or on the trail | continuation plausible (momentum [A]); few large winners pay [P] |
| Breakout / trend, long_swing | 1/3 T1, 1/3 T2, 1/3 weekly trail | 3-12 month momentum [A] |
| Pullback in uptrend (short_swing, swing) | 1/2 at T1 (prior high), 1/2 on EMA10/EMA21 or 2-bar pivots | prior high is supply |
| short_swing momentum | all at T1, or 1/2 + tight trail | too short for a runner to pay much |
| Mean reversion (RSI(2), oversold bounce) | 100% at the mean (SMA5/10/20) or time stop | reversal lasts ~1 week-1 month [A] (Jegadeesh 1990; Lehmann 1990) |
| Range trade | 100% below the range top; a breakout is a new plan | defined supply |
| Post-earnings gap / drift | 1/2 at T1; runner trailed; out >= 5 sessions before the next report | drift ~60 trading days [A] (Bernard and Thomas 1989), much weaker in large caps (Martineau 2022) [A] |
| Investment (stage 2 from a long base) | trim 1/4-1/3 at T1; later trims only on climax, extension or size limit; rest on weekly trail | long trends, 52-week-high effect [A] |
| Climax / parabolic (any) | sell 1/2 to all into strength | 10 |

Never add and scale out at the same level (`04` 1.6); after adds one stop covers the position and total open risk stays <= initial risk (`06` 10.3).

## 7. Scale out vs full exit

### 7.1 Decision rules (judged at the close; first matching row decides; [C] house order)

| # | Condition | Action |
|---|---|---|
| 1 | Stop, hard stop, trail or invalidation triggered | full exit of that portion, no discretion |
| 2 | Max hold or T1 deadline reached | `08` 8: exit, or re-underwrite as a NEW plan; never a silent extension |
| 3 | Report/event before the next session | execute the event plan (12) |
| 4 | Mean-reversion or range trade at target | full exit |
| 5 | Climax, exhaustion gap, or hype score >= 4 (`09` 7.2) | sell 1/2 to all into strength; tight trail on the rest |
| 6 | Trend/breakout trade at T1 | planned fraction; stop per 9; rest on the trail |
| 7 | Progress check failed (11) | the type's fail action (`08` 4): short_swing exit; swing, long_swing halve, stop to last higher low; investment reduce |
| 8 | Two or more cues (10) within 3 bars | exit (short_swing, swing); halve and tighten (long_swing, investment) |
| 9 | One cue | tighten one notch (EMA21 -> EMA10; chandelier 3 -> 2 ATR); no sale |
| 10 | None | hold; ratchet the trail; log stop value and date |

By type: short_swing single exit at T1 or 1/2 + tight trail, all out by bar 15; swing scales on trend/breakout, single exit on pullback-into-resistance and mean reversion; long_swing always scales; investment exits on weekly trend breaks, trims at T1, climax or size.

### 7.2 Regime adjustments (`01` 12) [C house defaults]

| Regime (re-read at each review) | Adjustment |
|---|---|
| risk_on | plan as written |
| neutral | T1 fraction one step larger (long_swing 1/3 -> 1/2; investment 1/4 -> 1/3); no blue-sky stretch targets |
| risk_off after entry | all trails one notch tighter; no adds; short_swing/swing exit at CP1 unless +0.5R and take T1 in full; weekly types halve on a weekly close below the 10-week SMA |
| market-wide news gap (`09` 10) | judge the stock's excess move, not the raw gap |

Momentum's regime dependence is [A]; these adjustments are [C].

### 7.3 After an exit: re-entry [C]

A stop-out ends the plan (exit code `08` 3.1). Re-entry is a NEW plan with its own trigger, stop and rule checks: a reclaim within 1-3 bars with a stop under the new low (`06` 3.1 T9), or a new base/pullback; once per setup (`06` 3.3). Never re-buy on the exit bar, to "win back" a loss, or after a lower low in a weekly downtrend. After a target exit, a new setup is judged like any entry, `stale_entry` included.

## 8. Trailing stops

### 8.1 Methods (long; ratchet up only)

| Method | Formula (show inputs) | Character | Label |
|---|---|---|---|
| Swing-low | last confirmed pivot low - buffer (5-bar hook pivots; 2-bar from rows) | structural; lags by confirmation bars | [C] |
| EMA | close below EMA(n); EMA_t = a x close_t + (1 - a) x EMA_{t-1}, a = 2/(n+1), seed SMA(n) | EMA10 tight, EMA21 standard | [C] |
| SMA50 | close below SMA50 on RVOL (V / 50-day avg) >= 1.5, or two closes below | swing, long_swing leaders | [C] (O'Neil; 1.5 house) |
| 10-week / 30-40-week SMA | weekly close below; Weinstein: below the lower of the 30-week SMA and the last minor low, under round numbers | long_swing / investment | [C] |
| Chandelier | highest high(n) - m x ATR(n) (Wilder); LeBeau n 22, m 3; highest high SINCE ENTRY until n bars have passed | volatility-scaled; loose in parabolic moves | [C] (untested, `02` 5.9) |
| ATR from close | close - m x ATR14, ratcheted | Tharp's test used 3 ATR | [P] (illustrative) |
| Donchian low | close (Turtles: a trade) below the lowest low of the last N bars, excluding today | Turtle 10-day / 20-day exits | [P] |
| Prior-bar low | close below the prior bar's low | tight mode, climax runs | [C] |
| Parabolic SAR (Wilder 1978) | SAR_{t+1} = SAR_t + AF x (EP - SAR_t); EP = highest high of the move; AF 0.02, +0.02 per new EP, max 0.20; SAR_{t+1} <= lows of bars t, t-1 | whipsaws in ranges | [S] for stocks; parabolic phases only |

### 8.2 Parameters and rules ([C], consistent with `02` 4 and `08` 10)

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Default trail | 2-bar pivot low - 0.25 ATR, or close below EMA10 | close below EMA21, or 5-bar pivot low - 0.5 ATR | weekly close below 10-week SMA, or weekly higher low - 0.25 weekly ATR | weekly close below 30/40-week SMA, or weekly higher low |
| Chandelier alt. | HH10 - 2 x ATR14 | HH22 - 3 x ATR22 | HH10W - 2.5-3 x weekly ATR14 | HH26W - 3 x weekly ATR14 |
| Donchian alt. | 5-bar low | 10- or 20-bar low | 10-week low | 20-week low |
| Tight mode (after a cue) | prior-bar low | EMA10 or 2-bar pivot | EMA21 daily or 5-week low | 10-week SMA |
| Activation | after T1 or +1.5R | after T1 or first higher low above entry | after first weekly higher low above entry | same |

1. Effective stop = max(initial stop, trail). 2. Recompute every bar (week), never lower; log value and date. 3. Trail on the invalidation's timeframe; a daily trail on a weekly-type position is a degradation needing a new plan (`05` 13). 4. One trail per position; switch only tighter, on a written cue. 5. Structure over indicator: when a pivot low and an MA disagree, use the one THIS trend has respected (count bounces). 6. Judge trails by give-back and capture over many trades (14).

## 9. Moving the stop to breakeven

| Aspect | Effect | Label |
|---|---|---|
| Win rate | rises: entry-level stops become scratches | [math] |
| Average winner | falls: normal retests eject trades; throwbacks to the breakout level are common in Bulkowski's tables, varying by pattern (`03` 2.6) | [math]; [P] |
| Expectancy | unchanged under a random walk (6.2); nearer stops give up part of a continuation edge; no rigorous test found | [math]; [S] |
| Risk budget | removes open risk | [C] |

Rules [C house]: before T1, never at a fixed +1R by reflex; move only to structure (a NEW higher low above entry, stop = that low - buffer). Breakouts: stop stays below the breakout zone until price has held above it. After the T1 partial: stop = max(entry, last higher low - buffer) for short_swing, swing, long_swing (`08` 10); investment uses the last weekly higher low only. CP2 failed: stop to breakeven or exit (`08` 6.3). Holding through a report under the cushion rule: stop >= entry (12).

## 10. Discretionary exit signals (cheat sheet)

Judged at the close. One cue = tighten; two = sell (7.1). Price/volume outrank oscillators.

| Signal | Exact criteria (long) | Strength | Action | Label |
|---|---|---|---|---|
| Climax run | after months of advance: 25-50%+ in 1-3 weeks, or 7 of 8 / 8 of 10 bars up, with the move's largest daily gain and highest volume; `01` 9.2 "climactic" | high | sell 1/2 to all into strength (limit on an up day) | [C] (O'Neil, Minervini); criteria untested (`03` 4.12) |
| Extension | beyond `01` 9.2 climactic; investment 70-100% above the 40-week/200-day SMA | high near climax | trim; tight mode | [C] (O'Neil) |
| Exhaustion gap | after an extended run, gap up (low > prior high) on RVOL >= 2 that closes in the lower half or fills within ~5 bars | high when filled | sell on the fill | [P] qualitative (Bulkowski); [C] thresholds; known only in hindsight |
| Largest down day | biggest one-day drop since the move began, above-average volume, after a climax | high | sell the rest or prior-bar-low trail | [C] |
| Breakaway gap down | gap through the trail, SMA50 or a support zone on RVOL >= 2, close near the low | high | exit at the close (4.4) | [C] |
| Failed follow-through | breakout closes below P - 0.5 ATR within 5 bars, or below the handle/final-contraction low; close below P on RVOL above the breakout day's | high | exit or halve (invalidation) | [C] windows; [P] Bulkowski busts (`03` 2.6, 4.15) |
| Lower high, then lower low | primary chart pivot high below the prior, then a close below the last pivot low | high | exit | [C] |
| Reversal bar / stall at target | new high into the target zone closing in its bottom third below the prior close; or 3+ bars within 0.5 ATR of the zone with no close above | medium | take the target now | [C] |
| Key/outside reversal week | weekly higher high and lower low, close in bottom third, at resistance | medium (weekly types); weak alone (`03` 4.11) | partial; tighten | [C] |
| MA break on volume | close below EMA21/SMA50 or weekly below the 10-week SMA, RVOL >= 1.5 | medium-high | exit if it is the trail; else tighten | [C] |
| News/earnings fade | U3 or U4 reaction (`09` 3.1) | high | `09` 4.3, 7.2 | [C] |
| RS breakdown | RS line (stock/SPY closes) at a 50-day (swing) or 26-week (weekly types) low while price is not; or 12-1 momentum below SPY's | medium | tighten; no adds | [C]; momentum [A] |
| Distribution cluster | 3+ down closes on RVOL > 1.3 within 10 bars, lower-third closes | medium | tighten | [C] (`08` 6.2) |
| Stage 3 | 30-week SMA flattens, price whipsaws across it on heavy volume | medium (weekly) | reduce 1/3-1/2; exit on stage 4 | [C] (Weinstein) |
| Regime turns risk_off | `01` 12 | medium | 7.2 | [C]; [A]/[P] background (Clare et al. 2013; Faber 2007) |
| Bearish divergence alone | price higher high, RSI/MACD lower high | low | note only (`02` 9) | [S] |

## 11. Time stops and maximum hold

No trade is open-ended. Clocks are canonical in `08` 4 (setup-specific earlier clocks `08` 4.1; checkpoint criteria and actions `08` 6.2-6.3; summary `CONVENTIONS.md`) [C]: CP1 (MFE >= +0.5R) bar 5 / bar 10 / week 6 / week 13, fail action exit / halve, stop to last higher low / halve, tighten / reduce; CP2 (close >= +1R or new swing high, else stop to breakeven or exit) bar 10 / bar 20 / week 13 / week 26; max hold 15 bars / 40 bars / 26 weeks / 52 weeks per plan (short_swing / swing / long_swing / investment). A plan's checkpoints are the earlier of these and `08` 6.1's formula.

Why [A background]: short-term reversal works over 1 week-1 month (Jegadeesh 1990; Lehmann 1990); momentum 3-12 months, partly reversing later (Jegadeesh and Titman 1993, 2001); drift about 60 trading days (Bernard and Thomas 1989; weak in large caps now, Martineau 2022). A time stop must not outlast the effect the setup relies on; no progress by the check says q is low (6.2). At any limit "nothing" is not an option (`08` 8: exit, renew or graduate, `05` 13). If T1 needs longer than max hold, change type or reject.

## 12. Event exits (earnings and scheduled events)

`09` 2-4 own the measurements (HEM, HEMmax, WL%) and reaction classes.

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Report between entry and latest max hold + 2 sessions | not allowed: max hold ends >= 1 session before, or reject | cushion rule (`09` 4.2): open >= 1R AND stop raisable to >= entry AND HEM < stop distance -> hold with raised stop; partial -> halve; fail -> exit at the last close before | name each report; cushion rule; fail -> halve, WL% in Risks; RU20 >= 3 ATR run-up -> trim 1/4-1/3 before | hold; if HEMmax > stop distance, say loss can exceed `max_loss`; review after |
| Timing | - | release after the close on T -> act at T's close; before the open -> T-1's close | same | same |
| After the report (`09` 4.3) | - | U1: trail to gap-day low; U3/U4: sell 1/2, exit on a close below the gap-day low; D1: exit at the close | U1: stop below the gap window; U3/U4: trim 1/3; D1: exit or reduce | thesis review; exit on weekly structure break |
| Other dated events | as earnings | cushion rule | Risks + action | Risks |

Rationale [A]: volatility is elevated at announcements (Beaver 1968); the sign is not predictable from the chart and no stop controls the jump (4.2). Drift is a reason to hold AFTER a strong reaction, not THROUGH an unknown one.

## 13. Master exit table per trade_type (cheat sheet)

| Item | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Stop basis | trigger-bar / pullback / flag low or breakout level - 0.25-0.5 ATR | base/handle low, last daily higher low or SMA50 zone - 0.5-1 ATR | weekly higher low / base low / 10-week zone - 0.25-0.5 weekly ATR | weekly base low / 30-40-week zone / monthly higher low - 0.5 weekly ATR |
| Stop trigger | daily close | daily close | weekly close + daily-close hard stop <= cap | same |
| T1 = `target` (>= 2R alone) | nearest resistance | next resistance / 52-week high | next weekly resistance / 0.5-0.75 weekly MM | first major weekly/monthly resistance |
| Scale-out | all at T1, or 1/2 + tight trail | 1/2 T1, rest T2/trail (trend); 100% at target (mean reversion, range) | 1/3 T1, 1/3 T2, 1/3 trail | 1/4-1/3 at T1; climax/size trims |
| Trail | 2-bar pivot / EMA10 | EMA21 / 5-bar pivot; chandelier 22/3 | 10-week SMA / weekly higher low | 30/40-week SMA / weekly higher low |
| Breakeven | after T1 | after T1 or structural higher low; CP2 fail | after T1 or first weekly higher low | structure only |
| CP1 / CP2 / max hold | bar 5 / 10 / 15 | bar 10 / 20 / 40 | week 6 / 13 / 26 | week 13 / 26 / 52 |
| Earnings | none inside hold | cushion rule or exit/halve before | named; cushion or halve | hold; review after |
| Priority cues | reversal bar/stall at target, failed follow-through | failed breakout, EMA21/SMA50 break on volume, climax | weekly reversal, 10-week break on volume, RS breakdown | stage 3/4, 40-week break, 70%+ extension |
| Pipeline horizon | `swing` | `swing` | `swing` if max hold <= ~13 weeks, else `long_term` | `long_term` |

## 14. Evaluating exits afterwards

The plan must record entry, initial stop, every exit (price, date, fraction, exit code `08` 3.1) and max hold so the evaluator can grade it.

### 14.1 Measures [math unless labelled]

| Measure | Formula (long) | Reads |
|---|---|---|
| R multiple | sum f_i (x_i - e)/(e - s_initial) | always vs the INITIAL stop |
| MAE / MFE | (e - lowest)/R, (highest - e)/R, entry to exit; closes in `close` mode, highs/lows in `intraday` (`08` 6.1) | pain / opportunity |
| Give-back | (peak - avg exit)/(peak - e), size-weighted | high = trail loose or late |
| Capture | (avg exit - e)/(peak - e), winners; TradeStation "exit efficiency" is the range-based variant [C] | share of MFE kept |
| Post-exit move | best/worst price in the k bars after exit (k = the type's CP1 length), in R | big gains after target/time exits = premature |
| Edge ratio | mean(MFE/ATR)/mean(MAE/ATR) over N bars after entry | entry quality; > 1 favourable (Faith 2007) [P] |
| Expectancy; T1 hit rate | win% x avg win - loss% x avg loss; share reaching T1 | hit rate should beat 1/(1 + RR) |
| Exit-reason mix | shares of stop, trail, target_final, time_*, event_exit, invalidation | many time_* = timing/selection problem |
| SQN (Tharp) | sqrt(N) x mean(R)/stdev(R), N capped at 100 | t-statistic of mean R; bands [C]; N >= ~30 |

Daily-bar ambiguity: if one bar touches both stop and target in `intraday` mode, assume the stop filled first; in `close` mode the close decides. Judge decisions only on bars up to that date; later bars judge outcomes.

### 14.2 Diagnosis (>= ~20 comparable trades per setup; thresholds [C])

MAE method (Sweeney 1997) [P]: in a trader's own records eventual winners rarely go far against the entry, so the MAE distribution of winners shows where noise ends and where the stop belongs.

| Pattern | Diagnosis | Fix |
|---|---|---|
| Losers stopped, then reached target within max hold; winners' MAE clusters near the stop | stop inside noise | wider buffer or next structure; smaller size, never a higher cap |
| Stop-outs at round numbers/obvious lows, then trend resumed | stops where orders cluster | buffer beyond them (3.3) |
| Realised losses far beyond the stop | gap risk under-weighted | stricter gap test and event rules (4.2, 12) |
| Winners' MAE < 0.5R, losers straight to the stop | stop wider than needed | nearer structure |
| Median MFE < T1 distance; T1 hit rate below 1/(1 + RR) | targets too far | first resistance as T1; enforce k |
| Many trades ran > 2R past T1 | trend exits too early | keep a runner (6.5) |
| Give-back > 50% of MFE | trail loose or late | tighter trail after T1; honour climax cues |
| Many losers had MFE >= 1R first | open profit unprotected | T1 partial at first resistance; structural breakeven |
| Many time stops, small losses | early entries or weak setup | better triggers (`06`), or accept the cost |
| High win rate, negative expectancy | rare large losses | catastrophe stop, event exits |

## 15. Common exit errors

Widening or removing a stop, or holding a gap-through loss "until it comes back" (disposition effect [A]); stops at round numbers or exact lows; targets at or above resistance or a round number; counting a trailed runner at an imagined price; full size through a report with the stop inside the usual earnings move; a daily trail on a weekly trade without re-planning; selling a whole trend position at T1 by habit, or holding a mean-reversion trade past its mean; breakeven at +1R on breakouts that normally throw back; exiting on a divergence alone; no max-hold date, a silent extension, or an instant re-entry after a stop-out.

## 16. Worked example (hypothetical)

XYZ, swing; profile max loss 8%, min R:R 2.0, `close`. 7-week flat base: pivot 80.00, handle low 76.10, base low 72.00; ATR14 1.60 (2.0%). Resistance zone 88.00-88.60 (prior swing high; 52-week high 88.60); nothing higher on 2 years. Next report in 52 trading days.

1. Entry: close above 80.16 (80.00 + 0.1 ATR). Stop 76.10 - 0.8 = 75.30; R 4.86 = 6.1% (pass); overshoot line 7.1%.
2. T1 = 88.00 - 0.40 = 87.60 = +1.53R; the measured move (88.00) lands in the same zone. Above 88.60 only an R objective exists (3R = 94.74, k = 14.58/(0.63 x 1.60 x sqrt(40)) = 2.29 > 1.5), not a chart level and not even reachable.
3. T1 < 2.0R: fail. A blend (1/2 at T1, 1/2 at 3R = 2.27R) cannot rescue it (6.4); raising the stop would be rule-fitting (3.5). Verdict: reject.
4. A different setup that passes: anticipatory entry in the handle (`06` 3.1 T7) on a reversal close near 78.50: stop 75.30, R 3.20 (4.1%), T1 87.60 = 2.84R. The pivot 80.00 is supply inside the trade: add "close above 80.00 within 10 bars, else exit"; the breakout's failed-follow-through cue does not apply below 80.00.
5. Its exit plan: 1/2 at 87.60, then stop to max(78.50, last higher low - 0.8), rest on an EMA21 close; CP1 bar 10 (MFE >= 80.10), CP2 bar 20 (close >= 81.70 or new swing high); max hold 40 bars, before the report (bar 52): no event action. Cues: reversal bar or stall in 87-89, close below EMA21 on RVOL >= 1.5, close below 76.10.

## 17. Shorts (mirror notes, only if `allow_short: true`)

Mirror every price rule. Use short_swing/swing clocks only, reject any report inside the hold, trail tighter (declines are fast and squeezes sharp; asymmetric volatility [A]), and list borrow cost as a data gap (`08` 16).

## Sources

- Beaver, W. (1968), Journal of Accounting Research 6 (Supplement): earnings announcement volatility.
- Bernard, V., Thomas, J. (1989), Journal of Accounting Research 27: post-earnings drift. https://ideas.repec.org/a/bla/joares/v27y1989ip1-36.html
- Bhattacharya, U., Holden, C., Jacobsen, S. (2012), Management Science 58(2): round-number imbalances. https://pubsonline.informs.org/doi/10.1287/mnsc.1110.1364
- Bulkowski, T., Encyclopedia of Chart Patterns (2nd ed., 2005); https://thepatternsite.com/measure.html ; https://thepatternsite.com/gaps.html ; https://thepatternsite.com/throwbacks.html ; https://thepatternsite.com/WeinsteinStops.html (via search summaries).
- Clare, A., Seaton, J., Smith, P., Thomas, S. (2013), Journal of Asset Management 14(3): trend following, stop losses and trading frequency on the S&P 500. https://openaccess.city.ac.uk/17842/
- Connors, L., Alvarez, C. (2008), Short Term Trading Strategies That Work ("Stops hurt"). https://tradingmarkets.com/trading-tip/stops-hurt-1597528
- Elder, A. (2002), Come Into My Trading Room (SafeZone). https://www.luxalgo.com/library/concept/elder-safezone-stop/
- Faber, M. (2007), Journal of Wealth Management 9(4): 10-month SMA timing.
- Faith, C. (2007), Way of the Turtle (edge ratio, Turtle exits). https://www.buildalpha.com/eratio/ ; https://www.theturtletrader.com/turtle-trading-rules/
- George, T., Hwang, C.-Y. (2004), Journal of Finance 59: 52-week high and momentum. https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf
- Han, Y., Zhou, G., Zhu, Y. (2016), Taming momentum crashes: a simple stop-loss strategy, SSRN WP. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2407199
- Huddart, S., Lang, M., Yetman, M. (2009), Management Science 55(1): volume at 52-week highs/lows. https://pubsonline.informs.org/doi/10.1287/mnsc.1080.0920
- Jegadeesh, N. (1990), Journal of Finance 45(3): short-term reversal. Jegadeesh, N., Titman, S. (1993), Journal of Finance 48(1); (2001), Journal of Finance 56(2): momentum and later reversal.
- Kaminski, K., Lo, A. (2014), When do stop-loss rules stop losses? Journal of Financial Markets 18. https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf
- LeBeau, C., Lucas, D., Computer Analysis of the Futures Market (chandelier). https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit
- Lehmann, B. (1990), Quarterly Journal of Economics 105(1): weekly reversal.
- Lo, A., Remorov, A. (2017), Journal of Financial Markets 34: stop-loss with serial correlation and costs. https://alo.mit.edu/research-page/stop-loss-strategies-with-serial-correlation-regime-switching-and-transaction-costs/
- Martineau, C. (2022), Rest in peace post-earnings announcement drift, Critical Finance Review 11(3-4).
- Minervini, M. (2013, 2016), Trade Like a Stock Market Wizard; Think and Trade Like a Champion. https://www.chartmill.com/documentation/stock-screener/fundamental-analysis-investing-strategies/465-Mark-Minervini-Strategy-Think-and-Trade-Like-a-Champion-Trading-Strategy
- Odean, T. (1998), Journal of Finance 53: disposition effect (3.4% as reported in secondary summaries). https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00072
- O'Neil, W., How to Make Money in Stocks (sell rules). https://finance.yahoo.com/news/vertical-logic-learning-read-sell-215900159.html
- Osler, C. (2003), Journal of Finance 58: currency order clustering. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf
- SEC Investor Bulletin: Stop, stop-limit, and trailing stop orders. https://www.sec.gov/oiea/investor-alerts-bulletins/ib_stoporders.html
- StockCharts ChartSchool, Parabolic SAR. https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/parabolic-sar
- Sweeney, J. (1997), Maximum Adverse Excursion, Wiley.
- Tharp, V., Trade Your Way to Financial Freedom (random-entry test). https://www.tradingblox.com/tbforum/viewtopic.php?t=3637
- TradeStation, Entry/Exit Efficiency report field. https://help.tradestation.com/10_00/eng/tradestationhelp/subsystems/spr_topics/report/entry_efficiency_exit_efficiency__strategy_performance_report_.htm
- Weinstein, S. (1988), Secrets for Profiting in Bull and Bear Markets.
- Wilcox, C., Crittenden, E. (2005), Does trend following work on stocks? https://www.cis.upenn.edu/~mkearns/finread/trend.pdf
- Wilder, J. W. (1978), New Concepts in Technical Trading Systems (ATR, Parabolic SAR).
- Fibonacci tests: Expert Systems with Applications (2021) https://www.sciencedirect.com/science/article/abs/pii/S0957417421012495 ; (2006) http://aeconf.com/articles/may2006/aef070109.pdf
- Note: Han-Zhou-Zhu, Odean, Clare et al., Connors-Alvarez, Tharp and Wilcox-Crittenden figures are as stated in abstracts or secondary summaries; none is a rule input. Every table threshold is [math] or a labelled house default.
