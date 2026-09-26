# 05 - Time windows and trade types

## How to use this file

- Order: (1) pick the `trade_type` with section 11; (2) read its column of the master matrix (14); (3) before publishing run the four plan checks: stop feasibility under the cap (7.2), T1 reachable inside max hold (5.3), gaps/costs/fill ceiling (7.5), earnings inside the hold (8). Clock values are canonical in `08-trade-plan-and-timeline.md` section 4; section 9 summarises them.
- Labels: [A] academic/replicated, [P] practitioner study, [C] convention, [S] speculative/contested; [A math] = arithmetic/probability under the stated assumption. "House default" = a starting value chosen for this playbook, not a published result.
- Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).
- Examples are hypothetical. Neighbours: `01-chart-reading.md` (liquidity 7.3, extension 9.2, volatility 10, regime 12, alignment 13, procedure 15), `02-indicators.md` (formulas; parameters 4), `03-chart-patterns.md` (breakouts 2.3, failed breakout 4.15), `04-strategies-and-setups.md` (setups S1-S15, matrix 5.2), `06-entries.md`, `07-exits.md`, `08-trade-plan-and-timeline.md`, `09-events-hype-and-fear.md`.

## 1. Evidence ledger: what changes with horizon

| Claim | Label | Consequence |
|---|---|---|
| 1 week-1 month: single stocks REVERSE in the cross-section (Lehmann 1990; Jegadeesh 1990); single-stock weekly returns are slightly negatively autocorrelated, indices' positively (Lo and MacKinlay 1988); strongest in illiquid names, largely eaten by costs (Avramov, Chordia and Goyal 2006), a reward for supplying liquidity (Nagel 2012) | [A] (small in liquid large caps) | short_swing: pullback entries inside uptrends; skip when the 1w or 1m return is in the top decile of the stock's own 2-year history [C house rule; the research ranks stocks against each other] |
| 3-12 months: winners keep winning (Jegadeesh and Titman 1993); own 12-month trend persists ~1 year then partly reverses (Moskowitz, Ooi and Pedersen 2012; futures/forwards) | [A] | swing, long_swing: buy RS and 6-12 month winners; no laggards "because cheap"; investment: tighter review after a double within 12 months [C] |
| Nearness to the 52-week high predicts 6-12 month returns, no later reversal (George and Hwang 2004) | [A] | new-high breakouts for swing and longer |
| Momentum crashes in volatile market rebounds after declines, driven by past losers rallying (Daniel and Moskowitz 2016) | [A] | long_swing/investment: just after a volatile market low, judge leadership on RS since the low (`02` 11) |
| 3-5 years: losers beat winners (De Bondt and Thaler 1985), largely value/size (Fama and French 1996) | [A] | investment: no new plan after a many-fold 3-5 year run with a steepening weekly slope [C, average effect applied to one stock]; prefer early stage 2 after a long base |
| Post-earnings drift ~60 sessions (Bernard and Thomas 1989), also after the announcement return (Chan, Jegadeesh and Lakonishok 1996); essentially absent in large caps since the mid-2000s (Martineau 2022) | [A], much smaller today | post-report entries for swing/long_swing, mainly small/mid caps |
| Short, intermediate and long trend signals are partly distinct: MA lengths combined beat any one (Han, Zhou and Zhu 2016); 1/3/12-month lookbacks combined worked for a century (Hurst, Ooi and Pedersen 2017; futures) | [A] | check trend on the context AND primary chart |
| Monthly close vs 10-month SMA cut index drawdowns (Faber 2007) | [P] indices; [C] one stock | investment regime filter, not an entry tool |
| MA/breakout rules worked on the Dow 1897-1986 (Brock, Lakonishok and LeBaron 1992); after data-snooping correction the best rule failed out of sample 1987-1996 (Sullivan, Timmermann and White 1999) | [A] | conventional parameters per timeframe; never optimise |
| Retail day traders overwhelmingly lose (Barber, Lee, Liu and Odean 2014; Chague, De-Losso and Giovannetti 2019) | [A] | day trading excluded (15) |

## 2. Taxonomy and data plan

### 2.1 The four trade types

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Typical hold | 3-15 sessions | 2-8 weeks (10-40 bars) | 2-6 months (9-26 weeks) | 6 months+, re-underwritten every <= 12 months |
| Primary (levels) | daily ~6 months (~126 bars) | daily ~1 year (~252) | weekly ~2 years (~104) + daily structure | weekly ~5 years (~260) |
| Context (trend) | weekly ~1 year | weekly ~2 years | weekly/monthly ~5 years | monthly ~10 years (from weeks) |
| Trigger/timing | daily | daily | daily, confirming the weekly level | weekly; daily for fine entry |
| Entry validity (`06` 9) | 5 bars | 10 bars | 4 weeks | 8 weeks |
| 20-day dollar volume < $5M (`01` 7.3) | reject | reject | flag | flag |
| Pipeline `horizon` / `chart_timeframe` | `swing` / `1d` | `swing` / `1d` | `swing` if max hold <= ~13 weeks, else `long_term` / `1w` (2.4) | `long_term` / `1w` |

short_swing floor: >= 3 sessions and no plan that needs an intraday decision; earlier exits only by stop, invalidation or target.

### 2.2 Data calls (<= 500 daily rows per GetStockPrices call)

500 rows ~ 1.98 years; 20 calendar months ~ 420 rows. The hook's weekly table shows only the last 104 weeks of EACH call: stitch across calls (merge a split week) or rebuild from `raw/`. Monthly bar = first open, max high, min low, last close, summed volume. Returns, SMAs, 52-week range and ATR come from the call ending at `as_of` (`01` 14).

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Stock | 1 call, `as_of` minus ~15 months (~300 rows) | 1 call, 500 rows | 3 x ~20 months, one message | 6 x ~20 months, one message |
| SPY, sector ETF (QQQ if tech) | 1 each | 1 each | 1-3 each (weekly RS needs >= 2 years) | 3 each |
| Indicator tools | ATR, Stochastic, Bollinger (daily) | ATR, OBV, Bollinger (daily) | weekly values computed from bars | weekly/monthly computed |
| Events | next earnings (mandatory) | + last 4 report dates | last 4-8 | last 8 |
| Rough call count | ~6 | ~7 | ~12-15 | ~16-20 |

### 2.3 Warm-up and partial bars

Warm-up (else write `n/a (needs N bars, have M)`, never shorten silently): SMA200 + 20-bar slope 220 daily; 12-1 momentum 253 daily / 53 weekly; EMA(n) seed + ~2.3 x (n+1) bars, Wilder(n) seed + ~4.6 x n (`02` 1.2); 30-week SMA + 4-week slope 34 weeks; 40-week + 13-week slope 53 weeks; 10-month SMA + 3-month slope 13 months; Mansfield RS (52) 52 weeks, ~56-65 to read a slope; weekly ATR14 stable after ~45 weeks.

Partial bars: if `as_of` is not the week's last session, the latest weekly bar is IN PROGRESS: weekly-close triggers, invalidations and pivots use the last COMPLETED week; call the current one "provisional" (same for months). Pivots confirm late (hook daily pivots 5 sessions after the bar, weekly 2-3 weeks): the newest swing low may be missing from the hook's list; read `raw/` and say "unconfirmed".

### 2.4 Mapping to the pipeline's horizons and rule checks

| trade_type | `horizon` | `upcoming_earnings` window | Blind spot | Add |
|---|---|---|---|---|
| short_swing | `swing` | 45 d | none (hold ~21 calendar days) | section 8: reject if a report is inside the hold |
| swing | `swing` | 45 d | reports on days 46-56 of an 8-week hold | check to full max hold; Risks |
| long_swing <= ~3 months | `swing` | 45 d | days 46-90 | same; `chart_timeframe` expects `1d`: take final entry/stop from daily bars and set `1d`; if a level exists only weekly, set `1w` and accept the flag with the reason |
| long_swing > ~3 months | `long_term` | 30 d | 1-2 reports inside the hold | name the dates and the gap plan (8) |
| investment | `long_term` | 30 d | several reports | reports are checkpoints (9) |

## 3. Top-down analysis per trade_type

Rule [C] (Elder triple screen): higher timeframe sets direction, middle sets setup and levels, lower times the entry (screens about 5x apart). With daily bars as the floor, short_swing and swing collapse middle and lower screens into the daily chart. Detail: `01` 15.

| Step | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| 0. Regime (`01` 12) | SPY vs SMA50/200, distribution days | SPY vs rising SMA200 | SPY vs 40-week SMA | SPY monthly close vs 10-month SMA [P] |
| 1. Trend decided by | weekly: not stage 3/4; above 10-week SMA preferred | weekly stage 2 (above rising 30-week) or late-stage-1 breakout | weekly stage 2, 30-week rising >= 4 weeks; monthly not down | monthly HH/HL or completed multi-year base; above 10-month SMA |
| 2. Levels read on | daily pivots 3-4 months, gaps, EMA21/SMA20 | daily + weekly pivots 1 year, 52-week high, SMA50, prior breakouts | weekly zones 2 years, multi-year highs, 10/30/40-week SMAs | weekly/monthly zones 5-10 years, all-time high, 40-week SMA, round numbers |
| 3. Entry timed on | daily close through trigger bar/pivot | daily close through pivot or reversal at support | daily close above the weekly pivot | completed weekly close; daily only for staged/fine entry |
| 4. Stop read on | daily | daily (weekly sanity check) | weekly structure + daily hard stop | weekly/monthly structure + daily hard stop |
| 5. Target read on | daily resistance, 1-3 week measured move | daily/weekly resistance, base measured move | weekly resistance, weekly measured move | monthly/weekly resistance, multi-year measured move |

Rules: the trigger chart may only DELAY an entry the context allows, never create one against it; never take levels from a chart below the primary except the stated daily hard stop (7.2).

## 4. Noise, fractals and the horizon map

### 4.1 Signal vs noise [A math, random-walk approximation]

- Drift grows like T, noise like sqrt(T): signal-to-noise grows like sqrt(T) (weekly bar ~2.2x daily, monthly ~4.6x). Fat tails and volatility clustering make this a first approximation.
- So daily structure breaks far more often than weekly structure in the same trend; a daily lower low inside a weekly uptrend is usually noise; whipsaws per month are higher on dailies.
- Measure it: Kaufman ER(10) daily vs weekly (`02` 7.9); a trend clean only on weekly suits long_swing/investment, not short_swing [C].
- Noise floor for stops [C house default]: a stop closer than ~1 ATR of the primary chart sits inside one bar's normal range. short_swing >= 0.75 daily ATR and swing >= 1 daily ATR from entry (`07` 3.3); long_swing/investment invalidation >= 1 weekly ATR (~2.2 daily).

### 4.2 Fractal caveat

The same shapes appear on every timeframe [C], but a 2-week daily flag is dominated by noise and reversal effects while a 6-month weekly base can reflect accumulation [C, O'Neil/Weinstein]. Bulkowski's statistics come mostly from daily charts: do not transfer them to weekly patterns as proven [P scope note]. A weekly flag is a daily base: name the pattern on the chosen type's primary chart.

## 5. Parameter scaling

### 5.1 Equivalents (5 sessions/week, ~21/month) [C]

| Daily | Weekly | Monthly | Use |
|---|---|---|---|
| EMA10 / EMA21 | 2-week / ~4-week | - | short_swing pullback lines |
| SMA50 | 10-week | ~2.5-month | O'Neil 10-week line; swing trend |
| SMA150 | 30-week | ~7-month | Weinstein stage line |
| SMA200 | 40-week | ~9-10-month | long-term trend |
| SMA210 | ~43-week | 10-month | Faber rule [P] |
| 252-day high | 52-week high | 12-month high | 52-week-high effect [A] |
| 12-1 momentum close[t-21]/close[t-252] - 1 | close[w-4]/close[w-52] - 1 | close[m-1]/close[m-12] - 1 | [A] |

Equivalents are close, not identical (weekly SMAs use week-end closes): say which. Oscillator lengths are NOT rescaled: weekly RSI14 spans 70 sessions and differs from daily RSI70; keep standard lengths per timeframe (`02` 4). Weekly Bollinger (20, 2) spans 100 sessions; weekly squeezes are rarer and longer.

### 5.2 Volatility scaling

- Weekly ATR14 ~ sqrt(5) = 2.24x daily under a random walk; in practice ~2-2.5x (single-stock negative weekly autocorrelation lowers it; trends and gaps raise it). COMPUTE from weekly bars; the ratio is a cross-check [A math; C range]. Monthly ~ sqrt(21) = 4.6x daily.
- Daily sigma ~ ATR14 / 1.6 (random-walk high-low range ~1.6 sigma, Parkinson 1980; true range adds gaps) [A math, approx]. Sigma over n sessions: sigma_n ~ 0.63 x ATR14 x sqrt(n).
- sigma_n in daily ATRs: n = 5: 1.4; 10: 2.0; 15: 2.4; 20: 2.8; 40: 4.0; 60: 4.9; 126: 7.1; 252: 10.0. Weekly: 0.63 x weekly ATR14 x sqrt(weeks): 13: 2.3; 26: 3.2; 52: 4.5 weekly ATRs.

### 5.3 Reachability check (every target)

Driftless random walk: P(touch a level k x sigma_n away within n sessions) = 2 x (1 - Phi(k)) (reflection principle) [A math].

| k = (T1 - e) / sigma_n(max hold) | 0.5 | 1.0 | 1.5 | 2.0 | 2.5 |
|---|---|---|---|---|---|
| P(touch), no drift, no stop | 62% | 32% | 13% | 4.6% | 1.2% |

- Assumes continuous monitoring; a close-confirmed level is reached less often: an upper bound. n = the type's max hold (15, 40 sessions; 26, 52 weeks with weekly sigma).
- With a stop 1R below and target R x risk above, a driftless walk hits the target first with probability 1 / (1 + R) (gambler's ruin) [A math]: 33% at R = 2, exactly break-even. Edge comes from drift (trend, momentum, PEAD) or a better entry, never from the ratio.
- House rules [C]: k <= 1.0 plausible; 1.0-1.5 needs a named tailwind (aligned context and primary trend, RS > 0, drift in a small/mid cap); k > 1.5: move to a longer type if its structure supports it (11), else reject. Never lengthen the time stop to make the math pass.

Example (hypothetical): XYZ 50.00, ATR14 1.25, target 56.00. short_swing: sigma_15 = 0.63 x 1.25 x 3.87 = 3.05, k = 1.97: unrealistic. swing: sigma_40 = 4.98, k = 1.2: only with a named tailwind.

## 6. Patterns, breakouts and false breakouts by timeframe

| Structure duration (on the chart where it formed) | Fits | Notes |
|---|---|---|
| 3-10 daily bars (flag, pennant, NR7/inside-bar coil, 2-5 day pullback) | short_swing | small measured moves; a throwback can eat the whole move |
| 2-8 weeks of daily bars (tight flag/VCP, flat base, pullback to SMA50) | swing (short_swing if tight and at the pivot) | O'Neil flat base >= ~5 weeks, <= ~15% deep [C] |
| 7 weeks-15 months (cup with handle, double bottom, weekly flat base) | swing to long_swing | O'Neil: valid cups ~7-65 weeks, most 3-6 months [C] |
| 1-5+ years (stage 1 base, multi-year range, weekly inverse H&S) | long_swing to investment | Weinstein investor buy near a flattening/rising 30-week SMA [C] |

- Bulkowski: tall patterns outperform short ones in most types [P, in-sample]; height grows roughly with sqrt(duration) [A math approx.], so short daily patterns give small measured moves: check 5.3 first.
- Throwbacks to the breakout price (Bulkowski: within 30 calendar days) are common after upward breakouts, and breakouts without one did better on average [P, as summarised; no figures quoted]. For short_swing and swing, stop below the pattern's support zone, not just under the pivot, or buy the retest (S2).
- "Longer patterns are more reliable" is [C]; no rigorous cross-timeframe test exists.

Breakout confirmation and failure per type (pivot P; `03` 2.3, 4.15; `06` 12):

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Valid breakout | daily close > P + 0.1 ATR, RVOL >= 1.5 | same, RVOL >= 1.4 | completed weekly close > P + 0.1 weekly ATR, week RVOL >= 1.2 (daily close for timing if the week has not closed back below P) | weekly close > P + 0.1 weekly ATR, or the first pullback that holds |
| Failed (close back below P - 0.5 ATR within 1-5 bars) | exit at that close | exit at that close | daily failure = warning; weekly close back in the base = invalidation; hard stop still live | weekly close back in the base = exit or reduce |
| Re-entry (once per setup, `06` 3.3) | fresh T9 reclaim or a new setup | reclaim of P after a new daily higher low | weekly reclaim | new base |
| Confirmation cost | little lag, most false signals [C] | one bar | weekly lag: a close > 3% above the planned entry hits `stale_entry`; plan a throwback entry | same; stage in |

Low breakout volume is a warning, not a veto [C/P]. In neutral/risk-off regimes (`01` 12) expect more failures: favour pullback entries (S1, S2) [C].

## 7. Stops, targets, R:R, win rates and costs

### 7.1 Stop placement and width (house defaults [C]; method `07` 3)

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Invalidation level | trigger-bar, pullback or flag low | base/handle low, last daily higher low, SMA50 zone | last weekly higher low, weekly base low, 10-week SMA zone | weekly/monthly base low, 30/40-week SMA zone, last monthly higher low |
| Buffer | 0.25-0.5 daily ATR | 0.5-1 daily ATR | 0.25-0.5 weekly ATR | 0.5 weekly ATR |
| Total distance | 1.5-2.5 daily ATR | 2-3.5 daily ATR | 1-2 weekly ATR (~2.2-4.5 daily) | 1.5-3 weekly ATR or the structural level |
| % for a 2.5% ATR stock | ~4-6% | ~5-9% | ~5.5-11% | ~8-17% |
| Trigger (`level_trigger: close`) | daily close | daily close | weekly close (invalidation) + daily-close hard stop at the cap | same |

### 7.2 Feasibility under the max loss (arithmetic)

Max ATR% for a stop of m ATRs under an 8% cap: ATR% <= 8 / m.

| | short_swing (m 1.5-2.5 D) | swing (m 2-3.5 D) | long_swing (m 1-2 W) | investment (m 1.5-3 W) |
|---|---|---|---|---|
| Max daily ATR% | 5.3-3.2% | 4.0-2.3% | ~3.6-1.8% (weekly 8-4%) | ~2.4-1.2% (weekly 5.3-2.7%) |

- Longer types fit only calmer stocks or entries close to the structural level. A volatile stock with a clean weekly setup usually FAILS `max_loss` as long_swing/investment: reject; never tighten to a daily level to pass (role.md).
- Weekly invalidation can be breached intraweek by more than the cap: always state a daily-close hard stop H >= e x (1 - max_loss/100) (`07` 4.3). If the weekly structure lies below H, take the trade only if H is itself a daily structural level; else reject or wait for an entry nearer the level.

### 7.3 Targets and realistic R:R

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Target source | nearest daily resistance, prior swing high, 1-3 week measured move | next major daily/weekly resistance, 52-week high, base measured move | weekly resistance, multi-year high, weekly measured move | multi-year measured move, prior all-time high, monthly resistance |
| Typical distance [C], capped by k <= 1.5 (5.3) | 3-3.7 daily ATR (cap 3.7 over 15 bars) | 4-6 daily ATR (cap 6.0 over 40 bars) | 2-4.8 weekly ATR (cap 4.8 over 26 weeks) | 3-6.8 weekly ATR (cap 6.8 over 52 weeks) |
| Realistic R:R (check 5.3) | 2-2.5 | 2-3 | 2-4 | 2-4 (T1 is a checkpoint) |
| Blue sky | measured move, k <= 1.5 | measured move; 2-3R only as checkpoint | measured move; trail beyond | measured move as first checkpoint |

`min_reward_to_risk` must pass on T1, the plan's `target` (`07` 6.4). A graded resistance (`01` 6.3) inside 2R is T1: do not jump it. If only a target with k > 1.5 reaches 2.0, reject or change type. Arithmetic [math]: 2R inside the k cap needs a stop <= cap / 2, i.e. <= ~1.8 daily ATR (short_swing), <= ~3.0 daily ATR (swing), <= ~2.4 weekly ATR (long_swing), <= ~3.4 weekly ATR (investment); a wider stop in the 7.1 range fails unless a longer type fits.

### 7.4 Win rate vs payoff (attributed numbers only)

- Break-even win rate = 1 / (1 + R): 33% at R = 2, 25% at 3 [arithmetic].
- Long-hold trend following (buy all-time highs, 10-ATR trail): profitable over 22 years and 18,000+ trades, carried by a minority of large winners (Wilcox and Crittenden 2005) [P]; the 1950-2024 update reports a ~44% win rate with fewer than 7% of trades producing essentially all profit (Zarattini, Pagani and Wilcox 2025) [P, as summarised in `04`].
- Very short mean reversion (RSI(2), Connors and Alvarez 2008; practitioner replications, mostly on index ETFs): win rates well above 50%, small average gains [P; figures not re-verified, none quoted].
- Pattern [C]: shorter holds trade payoff for win rate, longer holds the reverse. No attributed win rates exist for these trade types as such: never quote any. Consequence: trend-type plans keep a runner on a trail; mean-reversion short_swing plans exit in full at the target.

### 7.5 Gaps, slippage, costs and the fill ceiling

| Check [A math unless labelled] | Rule | Bites hardest |
|---|---|---|
| Fill ceiling | e_max = (T1 + R_min x s) / (1 + R_min); above it `reward_to_risk` fails. Write "void if filled above e_max" when e_max < e x 1.03 | thin-R:R plans; weekly-close entries |
| Cost in R | cost_R = round-trip spread+slippage % / stop %; break-even win rate becomes (1 + cost_R) / (1 + R). Half the stop = double the cost in R | short_swing, thin names |
| Close-trigger overshoot | realised loss ~ |e - s| + ~0.5 ATR14 (`07` 4.1, [C]): a third more than planned on a 1.5-ATR stop | short_swing |
| Overnight gap test | count non-earnings gaps in 252 bars that alone skip the stop, plus the worst (`07` 4.2); >= 3 means the stop sits in gap noise: longer type if feasible, else reject [C house default] | short_swing, swing |
| Worst-case line | (e - s) + s x worst gap, in % of e, beside the planned loss; add the largest earnings reaction if a report is in the hold | all |
| Weekend gap | buying after the weekly close (Friday close or Monday open) carries it; check the stale cap on the actual fill | long_swing, investment |

## 8. Earnings and events per type

Volatility is elevated around announcements (Beaver 1968) [A]; the reaction is often the quarter's largest move (check the stock's own history). A small average announcement-month premium exists (Frazzini and Lamont 2007; Barber, De George, Lehavy and Trueman 2013) [A]: an average, not a reason to hold a specific report. `09` owns event reading and the per-type rules (`09` 4.1-4.3; HEM/HEMmax `09` 2.2); `CONVENTIONS.md` lists the defaults. Time-window consequences:

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Report between entry and latest max hold + 2 sessions | not allowed: shorten max hold to end >= 1 session before it (only if T1 stays reachable, 5.3), else reject | cushion rule at the last close before (`09` 4.2); no new entry in the last 10 sessions | expected (1-2): name each with its action; pilot <= 1/3 before | expected: each report is a checkpoint; tranche around it |
| Post-report setups (S13) | days 1-10 | post-earnings base or drift, weeks 1-8 [A, weak in large caps] | weekly base, entry 2-6 weeks after | new stage 2 after a report-driven breakout |
| Gap vs stop | n/a | HEM > stop distance: cushion rule strictly | HEMmax > stop: realised loss can exceed `max_loss`; lower confidence | same; thesis review after each report |
| Role window vs hold (2.4) | 45 d covers the hold | 45 d; check to max hold | 45 or 30 d; check to max hold | 30 d |

Release after the close on T -> act at T's close; before the open -> at T-1's close (`07` 12).

## 9. Review cadence, checkpoints, time stops, maximum hold

No trade is open-ended. Before entry the plan states invalidation, stop (plus hard stop for weekly types), T1, fill ceiling (7.5), checkpoint dates, max-hold date and the action at each report. Clocks are canonical in `08` 4 (checkpoint criteria `08` 6.2, checkpoint actions `08` 6.3, time limits `08` 8; summary `CONVENTIONS.md`): CP1 bar 5 / bar 10 / week 6 / week 13; CP2 bar 10 / bar 20 / week 13 / week 26; max hold 15 bars / 40 bars / 26 weeks / 52 weeks per plan; renewals 1 / 1 / 1 / unlimited (each a full re-underwrite). A plan's checkpoints are the earlier of `08` 6.1's formula and these. Stops are checked on every daily close (weekly types: daily-close hard stop plus weekly-close invalidation); full review every 2-3 sessions / weekly / weekly with a deep review every 4 weeks / monthly and after each report. Scale-out after T1: `07` 6.5.

Structure beats progress: a structural failure exits regardless of open profit (`08` 6.3). T1 deadline = min(max hold, 2 x expected bars to T1) (`08` 6.1). O'Neil [C]: take most profits at 20-25%, but hold a stock up 20% within 3 weeks of a breakout for at least 8 weeks; cut losses at 7-8%. For a swing that 8-week hold is a graduation (13), not an extension.

## 10. Setups that suit each type

Codes and fit per `04` 5.2. S8 (MA crossovers) is a filter for every type, never a setup.

| trade_type | Primary fit | With care | Not used |
|---|---|---|---|
| short_swing | S1 pullback to rising EMA10/21; S2 retest; S9 squeeze / NR7 coil; S10 RSI(2) above rising SMA200 [P]; S11 range; S13 post-report gap (after it); S14 gap fill; S15 capitulation (high risk) | S3 (first days), S5, S12 | S4, S6, S7; any report inside the hold |
| swing | S1 (EMA21/SMA50); S2; S3 flat base/VCP/cup; S5; S7 20/55-day Donchian; S9; S12; S13 PEAD | S4 as filter, S6, S10, S11 | S14, S15; patterns with k > 1.5 |
| long_swing | S3 weekly base; S4 RS leader; S5 new 52-week high [A]; S6 30-week stage 2; S7 weekly; S12 | S1 (10-week), S2 weekly, S9 weekly, S13 to next report | S10, S11, S14, S15; after a 3-5 year run |
| investment | S4; S5; S6 Weinstein investor buy | S1 (40-week, staged), S2, S3 weekly, S7 filter, S12 staged start | S9-S11, S13-S15; late stage 2 far above the 40-week; stage 3/4 |

## 11. Choosing the trade_type

Run in order; stop at the first rejection that applies to every remaining type.

1. **Allowed.** Profile `horizons` (2.1): `swing` only -> short_swing, swing, long_swing <= ~3 months; `long_term` only -> long_swing > 3 months or investment.
2. **Where the setup lives.** The duration of the structure defining entry and stop nominates the type (6). Never stretch a 2-week daily flag into an investment, or shrink a 1-year weekly base into a short_swing without its own daily structure.
3. **Context and regime.** The type's context chart must pass `01` 13 (grade C+, A/B preferred); if it fails but a shorter type's passes (weekly only stage 1), consider the shorter type. Regime (`01` 12.2): risk_off allows long_swing/investment only for stage 1->2 transitions with RS at new highs, short_swing/swing only at grade A with shorter holds.
4. **Stop feasibility.** Structural stop (7.1) passes `max_loss` (7.2) and the noise floor (4.1). If not, the only legitimate move is to a SHORTER type with its own structure nearer the entry; else reject.
5. **Room.** T1 >= `min_reward_to_risk` x risk AND k <= 1.5 over the max hold (5.3). If k > 1.5, try a LONGER type whose structure supports the same invalidation (re-apply its buffer, re-check `max_loss`, R:R); else reject.
6. **Events** (8): a report inside 15 sessions removes short_swing; a report 2-3 weeks out usually means wait and re-run after it.
7. **Volatility, gaps, liquidity.** Daily ATR% > ~4%: usually only short_swing (or swing with a ~2-ATR stop) fits the cap; > ~5.3% even short_swing needs < 1.5 ATR, near the noise floor: usually reject. Dollar volume < $5M rejects short_swing/swing; gap count >= 3 (7.5) argues against short_swing.
8. **Tie-break** [C]: the cleaner structure on its primary chart; if equal, the longer type (better signal-to-noise, momentum zone, fewer decisions), within `target_return_pct` and `horizons`.

One sentence in `## Setup`: "trade_type swing: 6-week daily flat base in a weekly stage 2; stop 3.1 ATR (7.4%) fits; T1 k = 1.1 over 40 sessions; next report after max hold."

## 12. Timeframe conflicts

Direction always comes from the chosen type's context chart. A conflict never flips direction: it lowers the grade, shortens the type, or means wait. Rules [C], long-only:

| Conflict | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Weekly up, daily down (pullback) | classic buy: wait for a daily reversal (higher low + close above prior high, or back above EMA10/21) | buy at support on a daily trigger; stop below the pullback low | noise unless it breaks the last weekly higher low; may stage in | noise; staged buys |
| Weekly down, daily up (bounce) | only if weekly is not stage 4 and room to weekly resistance >= 2R; grade C | reject | reject | reject |
| Weekly range (stage 1), daily breakout | allowed; target inside the range top | allowed, range top = T1; grade B | needs a weekly CLOSE above the range | wait for weekly breakout and first pullback |
| Monthly down, weekly up | n/a | note in Risks | grade C max; weekly base must be complete | reject until monthly close > 10-month SMA and repaired structure |
| Up but extended (`01` 9.2) | wait for pullback or 3-10 day flag | wait for base or pullback to EMA21/SMA50 | wait for pullback toward 10-week SMA | staged entry (`06` 10) |
| Oscillators disagree across timeframes | ignore weekly oscillators | confidence -1 notch | confidence -1; tighter time stop | stage-3 warning; review |
| Market regime down, stock up (`01` 12.2) | grade A only, shorter hold | grade A only; prefer to wait | stage 1->2 with RS at new highs only | same; stage slowly, no full size |
| Volatility expansion (ATR ratio > 1.3, `01` 10.1) | re-run 7.2; often fails | re-run 7.2; prefer pullback entries | weekly ATR lags: floor it at current daily ATR x ~2.2 | wait for contraction or stage in |

## 13. Graduation and degradation

Changing type mid-trade is a new, dated plan with every rule re-checked (record format `08` 9).

### 13.1 Graduation (shorter -> longer): winners only

All required [C]: (1) open profit >= 1R or original T1 reached; (2) the longer type's context and primary charts qualify NOW (e.g. swing -> long_swing: completed weekly close at a new 52-week high or above weekly resistance, 10-week SMA rising, weekly higher lows); (3) a structural stop for the longer type exists at or ABOVE the original entry, so the position cannot become a loss; (4) no report within ~2 weeks, or the cushion rule (8) passes.

Actions: take the planned partial at the original T1 (1/3-1/2); stop on the rest = higher of (current trail, new structural stop); new target on the new primary chart with k re-checked (5.3); restart checkpoints and max hold from the graduation date; update `horizon` if the mapping changes (swing -> `long_term` when the new max hold exceeds ~3 months) and its earnings window. Ladders: short_swing -> swing (flag becomes a daily trend); swing -> long_swing (daily base breakout becomes a weekly stage-2 breakout); long_swing -> investment only with the upstream fundamental thesis intact.

### 13.2 Degradation (longer -> shorter): allowed, tightens risk

Trigger: the longer type's structure weakens while the shorter type's holds (e.g. long_swing: weekly close below the 10-week SMA, RS rolling over, daily higher lows intact). Action: re-plan on the shorter primary chart: stop UP to daily structure, max hold cut to the shorter type's remaining window, target to the nearest daily resistance, trail switched to the shorter method.

### 13.3 Forbidden conversions [C]

- Never turn a losing short_swing or swing into a longer type to avoid the stop; the original stop stands.
- Never widen a stop when changing type.
- Never add to a loser to "improve the average" (O'Neil, Minervini: add only to winners).
- Never trail a weekly-type position with a daily method without a written degradation (`07` 8.2).

## 14. Master matrix

| Topic | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Hold / max hold | 3-15 sessions / 15 bars | 2-8 weeks / 40 bars | 2-6 months / 26 weeks | 6 months+ / re-plan at 52 weeks |
| Horizon / earnings window | `swing` / 45 d | `swing` / 45 d | `swing` (<= 3 mo) or `long_term` / 45 or 30 d | `long_term` / 30 d |
| Trend tool (context) | weekly stage, 10-week SMA; daily SMA50 | weekly 30-week slope; daily SMA200 slope | weekly 30/40-week SMA; monthly structure | 10-month SMA, monthly HH/HL |
| Level chart | daily 6 months | daily 1 year (+ weekly) | weekly 2 years (+ daily) | weekly 5 years (+ monthly) |
| Entry trigger | daily close through trigger bar / flag high; reversal bar at EMA10/21 | daily close through pivot; reversal at SMA50 / throwback | daily close above weekly pivot; completed weekly close above base | completed weekly close above level; staged daily buys |
| Breakout volume / entry validity | RVOL >= 1.5 / 5 bars | >= 1.4 / 10 bars | week >= 1.2 / 4 weeks | week >= 1.2 or OBV 26-week high / 8 weeks |
| Stop method | trigger/pullback low - 0.25-0.5 ATR | base/handle/higher low - 0.5-1 ATR | weekly higher low/base - 0.25-0.5 weekly ATR + daily hard stop | weekly/monthly structure - 0.5 weekly ATR + daily hard stop |
| Stop width / max daily ATR% at 8% | 1.5-2.5 daily ATR / 3.2-5.3% | 2-3.5 daily ATR / 2.3-4.0% | 1-2 weekly ATR / 1.8-3.6% | 1.5-3 weekly ATR / 1.2-2.4% |
| Targets / realistic R:R | nearest daily resistance, 3-3.7 daily ATR / 2-2.5 | major resistance or measured move, 4-6 daily ATR / 2-3 | weekly resistance or measured move, 2-4.8 weekly ATR / 2-4 | multi-year measured move, 3-6.8 weekly ATR / 2-4 |
| Scaling in | single entry | single, or 2/3 + 1/3 on follow-through / retest hold (above entry only) | 2-3 tranches: breakout, first 10-week pullback | 2-4 tranches at defined levels |
| Scaling out (`07` 6.5) | all at T1, or 1/2 + tight trail | 1/2 at T1, trail rest (100% for mean reversion/range) | thirds: T1, T2, trail | 1/4-1/3 at T1, rest on the weekly trail; trims on climax/extension/stage-3 signs |
| Trail | 2-bar low or EMA10 close | EMA21/SMA50 close, 5-bar pivot, or chandelier 22 / 3 ATR | 10-week SMA weekly close, weekly higher lows, chandelier 10W / 2.5-3 weekly ATR | 30/40-week SMA weekly close, weekly higher lows |
| Time stop | CP1 bar 5, CP2 bar 10 | CP1 bar 10, CP2 bar 20 | CP1 week 6, CP2 week 13 | CP1 week 13, CP2 week 26 |
| Earnings rule | none inside hold + 2 sessions | cushion rule or exit/halve; no entry in last 10 sessions | named reports with actions; pilot before, add after | reports = checkpoints; tranche around them |
| Review cadence | every close; review each 2-3 sessions | every close; weekly review | weekly; deep every 4 weeks | monthly + after each report |
| Indicator params (`02` 4) | EMA10/21, SMA50; ATR14 D; RSI(2) or Stoch(14,3,3); RVOL vs 20 d | SMA50/200, EMA21; ATR14 D; RSI14/MACD D; Donchian 20/55; RVOL vs 50 d | 10/30/40-week SMA; ATR14 W; RSI14/MACD W; Donchian 20/52 W; Mansfield RS | 40-week and 10-month SMA; ATR14 W; weekly RSI(14) context only |
| Documented edge | short-term reversal inside a trend [A] | momentum, 52-week high, PEAD [A] | momentum, 52-week high [A] | 12-month trend [A]; beware 3-5 year reversal [A] |
| Typical failure | noise stop-outs, throwbacks, cost per R | false breakouts, earnings gaps | weekly stop too wide for the cap; weekly-close lag | buying late stage 2 / stage 3 |

## 15. Why day trading is excluded

- No intraday bars, 15-minute delayed quotes, a human executing: an intraday plan cannot be read, triggered or audited, and `as_of` counts a daily bar only from 16:00 New York time.
- Fewer than 1% of Taiwanese day traders could predictably earn positive abnormal returns net of fees (Barber, Lee, Liu and Odean 2014); 97% of Brazilian futures day traders who persisted over 300 days lost money (Chague, De-Losso and Giovannetti 2019) [A].
- At horizons of days, costs and bid-ask bounce are a large share of the expected move, and the documented shortest-horizon effect is reversal that pays liquidity provision, not direction (Lehmann 1990; Jegadeesh 1990; Nagel 2012) [A].
- So the shortest type is short_swing (>= 3 sessions); every trigger is a daily close or a next-session order the human places.

## 16. Worked example (hypothetical)

XYZ, `as_of` 2026-09-25 (a Friday; numbers invented). Profile: swing and long_term, max loss 8%, min R:R 2.0. Dollar volume $60M; regime risk_on.

- Context: weekly above a rising 30-week SMA for 20 weeks; 12-1 momentum +34%; stage 2; monthly above the 10-month SMA.
- Primary: 7-week daily flat base 44.20-48.00 (7.9% deep); close 47.60; daily ATR14 1.10 (2.3%); weekly ATR14 2.60 (ratio 2.36).
- Step 2 nominates swing. Entry: daily close above 48.00 + 0.1 ATR -> 48.11. Stop under the base: 44.20 - 0.5 ATR = 43.65 -> risk 9.3%: FAILS the cap.
- Step 4, shorter type: last 8 bars form a 46.60-48.00 handle. short_swing stop 46.60 - 0.3 ATR = 46.27 (3.8%) fits; T1 = resistance 52.40 (R:R 2.33), but sigma_15 = 0.63 x 1.10 x 3.87 = 2.68, k = 4.29 / 2.68 = 1.60 > 1.5: unrealistic.
- Step 5, swing with the handle as invalidation (legitimate only because the handle low is the latest daily higher low inside the base; say so): stop 46.60 - 0.55 = 46.05 (4.3%, 1.9 ATR > noise floor); R:R 4.29 / 2.06 = 2.08; sigma_40 = 4.38, k = 0.98: plausible.
- Fill ceiling: e_max = (52.40 + 2 x 46.05) / 3 = 48.166 -> 48.16, well below the role's 3% line (49.55), so the stale cap (`06` 8.3) is 48.16: "void if filled above 48.16".
- Events: report 2026-11-12, 48 calendar days out: outside the 45-day rule window, inside the hold. Pre-report rule: cushion test at the 2026-11-11 close (`09` 4.2); Risks.
- Plan: swing, `1d`, entry 48.11 on a daily close above 48.11, valid 10 bars, stop 46.05, T1 52.40, CP1 bar 10, CP2 bar 20, max hold 40 bars from the fill (2026-11-20 if filled next session).

## Sources

- Avramov, Chordia, Goyal (2006), Liquidity and autocorrelations in individual stock returns, Journal of Finance 61(5).
- Barber, De George, Lehavy, Trueman (2013), The earnings announcement premium around the globe, JFE 108(1). https://webuser.bus.umich.edu/rlehavy/BDLT.pdf
- Barber, Lee, Liu, Odean (2014), The cross-section of speculator skill: evidence from day trading, Journal of Financial Markets 18. https://ideas.repec.org/a/eee/finmar/v18y2014icp1-24.html
- Beaver (1968), The information content of annual earnings announcements, Journal of Accounting Research 6 (Suppl.).
- Bernard, Thomas (1989), Post-earnings-announcement drift, Journal of Accounting Research 27. https://ideas.repec.org/a/bla/joares/v27y1989ip1-36.html
- Brock, Lakonishok, LeBaron (1992), Simple technical trading rules..., Journal of Finance 47. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1992.tb04681.x
- Bulkowski, Encyclopedia of Chart Patterns (2nd ed., 2005); https://thepatternsite.com/heightwidth.html, https://thepatternsite.com/throwbacks.html
- Chague, De-Losso, Giovannetti (2019), Day trading for a living? https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101
- Chan, Jegadeesh, Lakonishok (1996), Momentum strategies, Journal of Finance 51(5).
- Connors, Alvarez (2008), Short Term Trading Strategies That Work; replication https://www.quantifiedstrategies.com/rsi-2-strategy/
- Daniel, Moskowitz (2016), Momentum crashes, JFE 122(2). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2371227
- De Bondt, Thaler (1985), Does the stock market overreact? Journal of Finance 40.
- Elder (1993; 2014), Trading for a Living / The New Trading for a Living (Triple Screen).
- Faber (2007), A quantitative approach to tactical asset allocation. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461
- Fama, French (1996), Multifactor explanations of asset pricing anomalies, Journal of Finance 51(1).
- Frazzini, Lamont (2007), The earnings announcement premium and trading volume, NBER w13090. https://www.nber.org/system/files/working_papers/w13090/w13090.pdf
- George, Hwang (2004), The 52-week high and momentum investing, Journal of Finance 59. https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf
- Han, Zhou, Zhu (2016), A trend factor, JFE 122. https://ideas.repec.org/a/eee/jfinec/v122y2016i2p352-375.html
- Hurst, Ooi, Pedersen (2017), A century of evidence on trend-following investing, JPM 44. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2993026
- Jegadeesh (1990), Journal of Finance 45; Lehmann (1990), QJE 105. Summary: https://alphaarchitect.com/quantitative-momentum-research-short-term-return-reversal/
- Jegadeesh, Titman (1993), Returns to buying winners and selling losers, Journal of Finance 48. https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf
- Kaufman, Trading Systems and Methods (efficiency ratio).
- Lo, MacKinlay (1988), Stock market prices do not follow random walks, RFS 1. https://finance.martinsewell.com/stylized-facts/dependence/LoMacKinlay1988.pdf
- Martineau (2022), Rest in peace post-earnings announcement drift, Critical Finance Review 11. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607
- Minervini (2013), Trade Like a Stock Market Wizard.
- Moskowitz, Ooi, Pedersen (2012), Time series momentum, JFE 104. https://www.sciencedirect.com/science/article/pii/S0304405X11002613
- Nagel (2012), Evaporating liquidity, RFS 25(7).
- O'Neil, How to Make Money in Stocks (base durations, 7-8% loss, 20-25% profit, 8-week hold). https://finance.yahoo.com/news/using-20-sell-rule-help-200500142.html, https://traderlion.com/trading-strategies/the-8-week-hold-rule/
- Parkinson (1980), The extreme value method for estimating the variance of the rate of return, Journal of Business 53.
- Sullivan, Timmermann, White (1999), Data-snooping, technical trading rule performance, and the bootstrap, Journal of Finance 54. https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00163
- Weinstein (1988), Secrets for Profiting in Bull and Bear Markets.
- Wilcox, Crittenden (2005), Does trend following work on stocks? https://www.cis.upenn.edu/~mkearns/finread/trend.pdf
- Zarattini, Pagani, Wilcox (2025), Does trend-following still work on stocks? https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5084316
- Note: the Bulkowski, Wilcox-Crittenden and QuantifiedStrategies pages could not be opened in review; figures from them are qualitative here; Zarattini-Pagani-Wilcox figures as summarised in `04-strategies-and-setups.md`.
