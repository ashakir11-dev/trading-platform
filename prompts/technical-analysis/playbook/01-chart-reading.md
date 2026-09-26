# 01 - Reading a chart

## How to use this file

- Read once; then run the section 15 procedure for your `trade_type` and fill the section 16 score. Sections 3-13 explain each step; section 14 reads the hook's statistics block.
- Labels: [A] academic/replicated, [P] practitioner statistical study, [C] convention, [S] speculative/contested. "House default" = a threshold chosen for this playbook, not a published result; calibrate it to the stock's own history (percentiles) when you can. No [C] or [S] item alone decides a verdict.
- Examples are hypothetical. Use only bars dated on or before `as_of`; never remembered price history.
- Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).
- Siblings: `02-indicators.md` (formulas, indicator evidence), `03-chart-patterns.md` (patterns, breakout rules), `04-strategies-and-setups.md`, `05-timeframes-and-trade-types.md` (reachability 5.3, stop feasibility 7.2), `06-entries.md`, `07-exits.md` (stops, gap risk 4), `08-trade-plan-and-timeline.md` (time to target 5, time stops 6), `09-events-hype-and-fear.md` (earnings, news, hype and fear).

## 1. What you work with

### 1.1 Data you can see

| Source | Gives | Notes |
|---|---|---|
| `GetStockPrices` + hook | returns 1w/1m/3m/6m/12m/YTD; SMA20/50/200 and % distance; 52-week (252-bar) closing and intraday range; ATR14 (Wilder); 20-bar avg dollar volume; last 6 swing highs/lows (5 bars each side); last 104 weekly bars | Stats describe THAT call's bars only. Rows in `raw/`. <= 500 rows per call. |
| `GetAverageTrueRange`, `GetBollingerBands`, `GetStochasticOscillator`, `GetOnBalanceVolume` | indicator series | Anything else: compute from bars (1.3, `02` 1.2). |
| `GetStockPrices` on SPY, QQQ, sector ETFs | benchmark bars | RS and regime; same dates as the stock. |
| `GetUpcomingInvestorEvents`, `ListFilings` (8-K 2.02) | earnings dates | Mark past reports on the chart (8.5). |
| VIX, breadth, put/call, short interest | only if the pipeline provides them | Optional; never block on them. |

No intraday bars: the finest timing unit is the daily close (hence `level_trigger: close`). The 15-min delayed quote is for the stale-entry check, not a bar.

### 1.2 History per trade_type

| trade_type | primary (levels) | context (trend) | trigger | fetch |
|---|---|---|---|---|
| short_swing | daily ~6 months | weekly ~1 year | daily | one call, ~300 days (SMA200 needs 200 bars) |
| swing | daily ~1 year | weekly ~2 years | daily | one call, 500 rows |
| long_swing | weekly ~2 years (+ daily structure) | weekly/monthly ~5 years | daily | three ~20-month calls, one message |
| investment | weekly ~5 years | monthly ~10 years | weekly; daily fine entry | six ~20-month calls, one message |

Stitch weekly tables across calls (merge a week split between calls). Monthly bar = first open, max high, min low, last close, summed volume. Weekly equivalents [C]: 10-week ~ SMA50, 30-week ~ SMA150, 40-week ~ SMA200 (not identical; say which).

### 1.3 Formulas (show inputs every time; general indicator formulas in `02` 1.2)

| Quantity | Formula |
|---|---|
| EMA(n) | EMA_t = EMA_{t-1} + (2/(n+1))(C_t - EMA_{t-1}), seed SMA(n); warm-up: seed + ~2.3 x (n+1) bars (`02` 1.2) |
| MA slope | (MA_t / MA_{t-k} - 1) x 100; k = 20 days (SMA50/200), 4 weeks (30-week) |
| ATR%, ATR ratio | ATR14 (Wilder, as the hook; `02` 1.2) / close x 100; ratio = ATR14 / median ATR14 of 250 days |
| Weekly ATR | same on weekly bars; cross-check ~2-2.5 x daily ATR14 (sqrt(5) = 2.24, random walk) [C] |
| Distance d | (close - MA) / ATR14 |
| CLV | ((C - L) - (H - C)) / (H - L); +1 close at high; 0 if H = L |
| RVOL | V_t / mean(V of prior 50 days, excl. t); 20 days for short_swing; weekly: / prior 10 weeks |
| Up/down volume ratio | sum V on up-close days / sum V on down-close days, 50 days |
| RS line, Mansfield RS | RS = C_stock / C_bench (aligned, rebased x100). MRS = (RS / SMA(RS, n) - 1) x 100; n = 52 weekly (Weinstein); daily n = 252 (= 52 weeks; some platforms use 200: say which) |
| Pullback depth | (swing high - pullback low) / (swing high - leg's start low); also in ATRs |
| 52-week-high ratio | close / highest close of 252 bars (hook's closing high; George and Hwang used CRSP daily prices); the intraday-high version is lower, say which |
| Gap size | (O_t - C_{t-1}) / ATR14; full gap up if L_t > H_{t-1} |
| Anchored VWAP | sum(TP x V)/sum(V) from the anchor bar, TP = (H+L+C)/3; daily approximation, treat as a zone |

## 2. Evidence ledger (chart items; indicator evidence in `02` 2)

- Best supported [A]: 3-12 month momentum, largely industry-driven (Jegadeesh and Titman 1993; Moskowitz and Grinblatt 1999; time-series momentum is shown on futures/indices, Moskowitz, Ooi and Pedersen 2012, so pair a stock's own trend with RS); nearness to the 52-week high, no long-run reversal (George and Hwang 2004); short-term 1-week/1-month reversal (Jegadeesh 1990; Lehmann 1990); 21d/200d MA distance (Avramov, Kaplanski and Subrahmanyam 2021; hook SMA20/SMA200 is a proxy); regime dependence of momentum (Cooper, Gutierrez and Hameed 2004; crashes in volatile rebounds, Daniel and Moskowitz 2016); volatility clustering (Engle 1982; Bollerslev 1986); volume informativeness (Blume, Easley and O'Hara 1994; Gervais, Kaniel and Mingelgrin 2001; Lee and Swaminathan 2000).
- Weak or dated [A limited]: MA and range-break rules worked on the DJIA 1897-1986 (Brock, Lakonishok and LeBaron 1992), not out of sample (Sullivan, Timmermann and White 1999; mixed modern record, Park and Irwin 2007). S/R predicted intraday FX trend stops (Osler 2000) and marks order-book depth on NYSE stocks (Kavajecz and Odders-White 2004). Round-number barriers: found (Donaldson and Kim 1993), disputed (Ley and Varian 1994), small order imbalances (Bhattacharya, Holden and Jacobsen 2012). Patterns: incremental information, no after-cost profit shown (Lo, Mamaysky and Wang 2000); Bulkowski [P] in-sample.
- [S]: named candles (no value on DJIA stocks, Marshall, Young and Rose 2006; one early positive sample, Caginalp and Laurent 1998); Fibonacci ratios. [C]: Dow theory, Weinstein, Wyckoff, Minervini, Elder, trendlines, trader volume rules.
- Consequence: trend/momentum, 52-week-high nearness, RS, regime and volatility carry the evidence; levels, volume and bars place entry, stop and target.

## 3. Top-down reading order

Write one line per step, in order, before looking at the trigger chart (the stock's story anchors you otherwise).

| Step | Question | Output |
|---|---|---|
| 1 Market | Regime favourable for longs? | risk_on / neutral / risk_off (12) |
| 2 Sector | Sector ETF beating SPY, in its own uptrend? | leading / neutral / lagging (11) |
| 3 Context | Stage and trend strength? | stage 1-4 (4, 5) |
| 4 Primary | Position in swing structure; which levels? | top levels with grades (6) |
| 5 Volume, bars | Demand or supply at those levels? | accumulation / distribution (7, 8) |
| 6 Extension, volatility, gaps | Stretched? Stop width? Gap-prone? | d, ATR%, gap count (9, 10, 8.5) |
| 7 RS | Leading sector and SPY? | RS state (11) |
| 8 Events | Past reactions; next report vs hold | event line (8.5) |
| 9 Trigger | Setup now, or a level to wait for? | setup (`03`, `04`, `06`) |
| 10 Alignment | Timeframes agree? | grade A-F (13) |
| 11 Score | Chart quality | grade (16) |

## 4. Trend: definition and measurement

### 4.1 Definitions

- Dow theory [C]: primary, secondary and minor trends; uptrend = higher highs and higher lows, presumed intact until a definite reversal; volume expands with the trend; related averages should confirm (SPY with QQQ; stock with its sector ETF).
- Swing uptrend: last two confirmed swing highs and lows both rising, close above the latest swing low. Mirror for downtrend; otherwise range or transition.
- MA uptrend [A effect, C settings]: close > reference MA and MA slope > 0.
- Trendline [C]: through >= 2 swing lows, validated by a 3rd touch; subjective, and its break is weaker than a structure break (4.2 rule 4).

### 4.2 Swing structure from the hook's pivots

1. Lag: a pivot needs 5 later bars, so the last 5 bars never show one. Check the last 10 rows in `raw/` and label a recent swing "unconfirmed".
2. Noise filter [C, house default]: drop a pivot whose move from the prior opposite pivot is < 1.5 x ATR14 (daily) or < 1 weekly ATR (weekly).
3. Classify with the last three highs H1..H3 and lows L1..L3 (oldest first): H3 > H2 and L3 > L2 = uptrend; both lower = downtrend; lower high + higher low = contracting range (coil, `03`); higher high + lower low = expanding range (unstable); all within ~1 ATR = flat base.
4. Break of structure: close below the latest higher low damages an uptrend; a following lower high confirms reversal [C]. Repair = new higher low + close above the last lower high.
5. Weekly pivots: compute with 2 or 3 bars each side (say which). Only 6 pivots are listed; recompute older ones from `raw/`.

### 4.3 Trend strength

| Measure | Strong | Weak | Label |
|---|---|---|---|
| SMA50 slope, 20 days | > +2% | -1% to +1% | [C] house default |
| SMA200 slope | rising >= 1 month (Minervini: 4-5) | flat/falling | [C] |
| MA stack | close > SMA20 > SMA50 > SMA200 | tangled | [C] |
| ER(20) / ADX(14) (`02`) | > 0.4 / > 25 rising | < 0.2 / < 20 | [C] |
| 6m and 12m returns | both > 0 | mixed | [A] |
| 52-week-high ratio | >= 0.90 | < 0.75 | [A] effect, [C] cut-offs |
| Pullback depth | < ~40% of the prior leg | > ~60%, or below the prior swing low | [C] house default; Fibonacci levels [S] |
| Time symmetry | pullbacks shorter (bars) than advances | as long or longer | [C] |

### 4.4 Trend by trade_type (context minimums and structure windows: section 15)

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Reference MA | EMA21/SMA20, SMA50 floor | SMA50 | 30-week SMA | 40-week SMA; 10-month SMA ([P] Faber 2007 on indices; [C] for one stock) |
| Trend break | close below last daily HL, or 2 closes below EMA21 | close below last HL and SMA50 | weekly close below 30-week, SMA turning down | monthly close below 10-month SMA, or stage 4 |

## 5. Trend phases

### 5.1 Weinstein stages (weekly, 30-week SMA) [C]

| Stage | Price vs 30-week | 30-week slope (4 weeks) | Volume | Long-only use |
|---|---|---|---|---|
| 1 Basing | around it after a decline | flat (house default abs < 1%) | drying up | watch; enter on breakout to stage 2 (investment may start late stage 1) |
| 2 Advancing | above; pullbacks hold near it | rising | up on rallies, down on pullbacks | only stage for new long_swing/investment longs; preferred for all |
| 3 Topping | whipsaws after an advance | flattening | heavy without progress | no new longs; tighten (`07`) |
| 4 Declining | below; rallies fail at it | falling | up on declines | no longs |

Flat 30-week with price within 1 weekly ATR = "stage 1 or 3": decide by the prior trend. First or second base in stage 2 beats a 3rd-4th base [C].

Minervini trend template [C], count of 8: close > SMA150 and SMA200; SMA150 > SMA200; SMA200 rising >= 1 month; SMA50 > SMA150 and SMA200; close > SMA50; close >= 30% above 52-week low (some summaries 25%); close within 25% of 52-week high; strong RS (original: proprietary IBD rating >= 70; use section 11 and say so).

### 5.2 Wyckoff phases [C]

Accumulation: A stops the decline (selling climax, automatic rally, secondary test) and sets the range; B builds cause (longest); C tests supply, often a spring; D shows strength (rallies on rising volume, higher lows on light volume, back-up after clearing resistance); E = markup (stage 2). Distribution mirrors: buying climax, automatic reaction, upthrust, sign of weakness, last point of supply, markdown.

Daily-bar rules:
- Spring: low below a well-tested range low, close back inside same or next day, CLV > 0.5 ideally. Long trigger only in stage 1/2 context; stop below the spring low (`04` S12).
- Upthrust: high above range high, close back inside with CLV < 0: warning for longs.
- Absorption: repeated resistance tests with rising lows and shrinking pullbacks = resistance weakening.

## 6. Support and resistance

### 6.1 Where levels come from

| Source | Find it | Label |
|---|---|---|
| Swing highs/lows, range edges | hook pivots, your weekly pivots; 2+ pivots within ~0.5 ATR = range edge | [C]; [A limited] |
| Role reversal | broken resistance retested as support, and vice versa | [C] |
| Gaps | gap edges (H_{t-1}, L_t); earnings gaps first | [C]/[P] |
| High-volume bars | range of an RVOL >= 2 bar (house default), esp. reversal or earnings bars | [C] |
| 52-week / all-time extremes | hook range; stitched weekly bars | [A] anchoring |
| Moving averages | SMA50/10-week, SMA200/40-week, 30-week, only if sloping and previously respected | [C] |
| Anchored VWAP | from a major pivot, breakout or earnings bar (1.3) | [C] |
| Round numbers | whole, 10s, 50s, 100s scaled to price | [S]; confluence only |
| Trendlines, Fibonacci | 4.1; 38.2/50/61.8% of a leg | [C] / [S]: confluence note only, never a standalone stop or target |

### 6.2 Zones, not lines

- Centre: the price with the most reactions (closes if they cluster tighter than wicks). Half-width (house default [C]): 0.25-0.5 x ATR14 (daily levels) or weekly ATR (weekly levels); low end for quiet stocks (ATR% < 2) and tight clusters; investment levels >= 0.5 weekly ATR. Merge overlapping zones. Which levels count per type: section 15.
- Triggers fire on a close beyond the far edge; stops sit beyond the far edge plus a buffer (`07` 3.3).

Example (hypothetical): XYZ highs 52.10, 52.45, 51.90; ATR14 1.40; half-width 0.35 x 1.40 = 0.49; zone 51.61-52.59. A breakout close must exceed 52.59.

### 6.3 Grading a level (house rubric [C])

| Criterion | Points |
|---|---|
| Pivot timeframe | weekly/monthly +2; daily +1 |
| Reactions (each followed by >= 1.5 ATR move away) | +1 each, max +3 |
| Recency | touched within 3 months +1; older than 12 months -1 (not for multi-year extremes) |
| Volume: reaction bar or gap with RVOL >= 2 | +1 |
| Proven role reversal | +1 |
| Confluence (52-week/all-time extreme, round number, rising SMA50/200 or 30-week/40-week, AVWAP) | +1 each, max +2 |
| Sharp rejection (wick >= 50% of bar, or wide-range reversal bar) | +1 |
| Broken and reclaimed more than twice | -1 |

Major >= 6, intermediate 3-5, minor <= 2. Stops and targets use major/intermediate levels only. Repeated tests [S]: resistance with rising lows beneath = weakening (bullish); support with falling highs above = weakening (bearish).

### 6.4 Using levels in a plan

1. List major/intermediate zones within 3 x the target distance.
2. Nearest major support below = stop anchor; nearest major resistance above = first target or obstacle.
3. Two or more major levels between entry and target = target the first (`07` 5).
4. Blue sky (above 52-week/all-time high): targets from measured moves or ATR projections (`03` 2.5), labelled.
5. Room: (lower edge of nearest major resistance - entry) / (entry - stop) >= `min_reward_to_risk`, else reject or wait. Never move levels to fit.
6. Reachability inside the time stop: `05` 5.3, `08` 5.

### 6.5 Breaks, false breaks and reclaims (pattern rules: `03` 2.3, 2.6, 4.15, 4.16)

| Situation | Criterion | Reading | Label |
|---|---|---|---|
| Valid break | close beyond the far edge (daily: > P + 0.1 ATR, `06` 4), CLV >= 0 (>= 0.5 strong), RVOL >= 1.4 (short_swing 1.5) | level flips role | [C] |
| Weak break | beyond the zone on RVOL < 1 or CLV < 0 | wait for a second close or a retest hold | [C] |
| Failed break (bull trap) | close back below P - 0.5 ATR (inside the zone) within 1-5 bars (`03` 2.6), worse on higher volume | exit/avoid until a new base or reclaim | [P] Bulkowski busts / [C] |
| Failed breakdown (bear trap) | close back above broken support within 1-3 bars, weekly trend up | long candidate (`03` 4.16) | [C]/[P] |
| Throwback | return to the breakout zone, holds on closes | retest entry; on average selects weaker breakouts (`03` 2.6) | [P] |
| Repeat failures | >= 2 failed closes above one level in 3 months | stronger trigger needed (`06` 3.3) | [C] |

Breakouts fail more in risk_off and choppy tape (low ER) [A for momentum state, C for breakouts]. For long_swing/investment a daily break of a weekly level is unconfirmed until the weekly close.

## 7. Volume analysis

### 7.1 Reads

| Read | Bullish | Bearish | Label |
|---|---|---|---|
| RVOL | up/breakout day >= 1.4 (short_swing 1.5) | down/breakdown day >= 1.5 | [C] thresholds |
| Up/down volume (50d) | > 1.2 | < 0.8 | [C] house default (O'Neil-style) |
| Acc/dist days, last 25 (up/down close on V > prior day and > 50d avg) | more accumulation | more distribution | [C] IBD idea; avg filter house default |
| CMF(20) (`02`) | > +0.05 rising | < -0.05 | [C] house default |
| OBV | new high with/before price | falling while price rises | [C]/[S] |
| Dry-up | pullback V < 0.7 x avg; a day < 0.5 x | pullbacks on rising V | [C] |
| Climax | selling climax after long decline (possible stage 1) | RVOL >= 2.5-3, widest range in months after a long advance, weak close | [C] Wyckoff |
| Tests of prior lows | light volume on the retest | heavy volume through the low | [C] |

### 7.2 Rules

- Breakout: prefer RVOL >= 1.4 (short_swing 1.5) and CLV >= 0 (>= 0.5 strong) [C] (O'Neil: 40-50% above average). Bulkowski [P, qualitative]: above-average breakout volume goes with larger average moves for many patterns but also more throwbacks. RVOL < 1 lowers the score and argues for a retest entry; it does not veto.
- Healthy uptrend: U/D > 1, pullbacks on falling volume [C].
- Unusually high volume mildly predicts higher next-month returns regardless of direction [A] (support, not a trigger); persistently high turnover in a long advance is a late-stage warning for long_swing/investment [A] (section 2).
- Earnings days: read with `09` 3. Index-rebalance or option-expiry spikes are not accumulation unless structure agrees [C].

### 7.3 Liquidity (hook dollar volume)

| 20-day avg dollar volume | Reading | Label |
|---|---|---|
| < $5M | illiquid: wide spreads, gaps, unreliable levels; reject short_swing/swing, flag others | [C] house default |
| $5M-$20M | tradable with care; limits, wider buffers | [C] house default |
| > $20M | normal | [C] |

Dollar volume collapsing versus its 1-year average in a falling stock = neglect; declining across a base = normal dry-up. If the human's intended order is large versus daily dollar volume, note slippage in `Risks considered`.

## 8. Bars and candles

### 8.1 Evidence

Candle names: [S]. Objective anatomy (range, CLV, gaps, volume) at a graded level in the context trend's direction: [C]. The same bar mid-range means little; never trade a bar alone.

### 8.2 Bar vocabulary

| Bar | Definition | Long-context reading | Label |
|---|---|---|---|
| Wide-range bar | range >= 1.5-2 x ATR14 | up WRB with CLV > 0.6 off support = demand; down WRB after a long advance = supply | [C] |
| NR7 | smallest range of 7 bars | compression; expansion follows, direction not predicted | [C] here; Crabel's own tests [P] were next-day breakouts in futures/indexes (`02` 7.2) |
| Inside bar | H <= prior H, L >= prior L | pause; buy-stop above its high in an uptrend | [C] |
| Outside bar | H > prior H, L < prior L | bullish if CLV > 0.5, bearish if close near low | [C]/[S] |
| Bullish reversal bar | new short-term low, CLV > 0.33, close > prior close | trigger at a graded support | [C] |
| Bearish reversal bar | new short-term high, bottom-third close below prior close | warning; exit cue (`07` 10) | [C] |
| Long lower / upper wick | wick >= 2 x body and >= 50% of range | rejection of lower / higher prices; stronger with RVOL > 1 | [S] pattern, [C] context |
| Gap up and hold | L > prior H, upper-half close, unfilled 3 days | demand; gap becomes support | [C]/[P] |

### 8.3 Gaps (full table: `03` 5)

Common (inside a range, < 0.5 ATR, low volume: usually filled, ignore); breakaway (out of a base or through a major level on high volume: lower edge becomes support, often unfilled); runaway (mid-trend strength); exhaustion (after a long extended move, huge volume, then stall: filled fast); earnings (`09` 3). Labels: [P] Bulkowski (qualitative) / [C]. A gap is classifiable only after the bar closes and in hindsight: judge by context and the next 1-3 closes.

### 8.4 Daily vs weekly

For long_swing/investment a weekly reversal or WRB outweighs any daily bar, and the weekly close is the week's key price. If `as_of` is mid-week, the last weekly bar is "in progress": its close, range and volume are not final.

### 8.5 Gap risk, events and data sanity (read before planning a stop)

A close-based stop cannot prevent a loss that opens through it: the fill is the open.

| Read | How | Use | Label |
|---|---|---|---|
| Gappiness | count open gaps abs(O_t - C_{t-1}) >= 1 ATR14 in 252 bars, split earnings / non-earnings | many non-earnings gaps = news-driven: realised loss can exceed planned; prefer shorter holds, or reject if the stop is near the cap; the separate stop-skipping gap test (>= 3 = stop in gap noise) is `07` 4.2 | [C] house default |
| Largest adverse gap | biggest down gap in % over 1-2 years | if it exceeds `max_loss_per_trade_pct`, say so in `Risks considered` (`09` 2.3) | [C] |
| Past reports | per 8-K 2.02 date: gap %, RVOL, held after 5 bars? | earnings bars become levels (6.1); reaction class `09` 3 | [C] |
| Next report | days from `as_of` vs planned max hold | inside the hold: role flags it; hold-through rules `09` 4 | [C] |
| Pre-report bars | last 3-5 bars before a report | quiet volume there is not a true dry-up; a run-up is "buy the rumor" risk (`09` 5) | [C] |
| Data sanity | one-day move near -50%/-67% with no news, or a price-scale jump | suspect an unadjusted split (`02` 1.2): use only bars after it or rescale; say so in `Data gaps` | [C] |

## 9. Extension

### 9.1 Measure

d = (close - MA) / ATR14 (daily); weekly: (close - 10-week or 30-week) / weekly ATR. Preferred: d's percentile over its last 250 days (> 90th = extended for this stock). Also count consecutive up closes and the 5-day gain in ATRs.

### 9.2 Thresholds (house defaults [C])

| trade_type | reference | normal | extended (do not chase) | climactic (tighten/exit cue) |
|---|---|---|---|---|
| short_swing | EMA21 / SMA20 | d <= 2 | d > 3 | d > 4, or 5-day gain > 4 ATR |
| swing | SMA50 | d <= 4 | d > 5 | d > 7 |
| long_swing | 10-week (weekly ATR) | d <= 2 | d > 3 | d > 4, or > 50% above 40-week |
| investment | 40-week | < 30% above | > 40% above | > 70% above with widening weekly ranges |

### 9.3 Use

- Chasing a 1-week/1-month spike risks short-term reversal and buys a wide stop [A]; being far above the long MA is not bearish for months ahead [A]. The problem is the entry, not the stock.
- Entry is allowed up to the "extended" column; between "normal" and "extended" prefer a pullback entry. Extended = "no entry here", not "reject the stock". Plan a conditional pullback entry at a graded support or the reference MA, or wait for a new base (`06`). The role's `stale_entry` rule is the operational form.

## 10. Volatility regime

### 10.1 Measures

| Measure | Contraction | Expansion | Label |
|---|---|---|---|
| ATR% | near 1-year low | near 1-year high | [A] clustering |
| ATR ratio | < 0.8 | > 1.3 | [C] house default |
| Bollinger bandwidth (20, 2) | 6-month low (squeeze) | widening after it | [C] |
| NR7/inside clusters | several in 2 weeks | first WRB after | [C] |
| Base contractions | each pullback shallower (e.g. 25%, 12%, 6%) | n/a | [C] VCP (`03` 3.14) |

### 10.2 ATR% and stop feasibility

| ATR% | Class | With max loss 8% |
|---|---|---|
| < 1.5 | low | 1.5-2.5 ATR stops are small; targets may be slow |
| 1.5-3 | normal | 2 ATR stop = 3-6% |
| 3-5 | high | 2 ATR = 6-10%: often fails `max_loss`; tight structural stop or reject |
| > 5 | very high | 1.5 ATR > 7.5%: most swing plans fail |

Max usable stop multiple = `max_loss_per_trade_pct` / ATR% [C]. If the chart-justified stop needs more ATRs, reject; never shrink a stop inside normal noise (`07` 3.5). Classes are house defaults; ATR persistence is the solid part [A].

### 10.3 Reading

- Contraction near highs after an advance, on low volume = constructive base. Expansion on down bars after an advance = distribution risk. Expansion with a climax after a long decline = possible Wyckoff phase A, not yet a buy.
- Size stops and targets with current ATR (it persists [A]); ATR ratio > 1.3 means wider valid stops and smaller size for the human.

### 10.4 By trade_type

ATR: daily for short_swing and swing, weekly (14 weeks) for long_swing and investment. Contraction that matters: NR7/inside days at a level (short_swing); squeeze or 1-3 week flag (swing); multi-week VCP in a weekly base (long_swing); multi-month base with shrinking weekly ranges (investment).

## 11. Relative strength

### 11.1 Compute

Benchmarks: SPY; the sector ETF (XLK technology, XLF financials, XLV health care, XLY consumer discretionary, XLP staples, XLC communication services, XLI industrials, XLE energy, XLB materials, XLU utilities, XLRE real estate); QQQ for growth names; a narrower industry ETF if upstream data names one. Then:
1. RS line on common dates (1.3); RS return = stock minus benchmark return over 1m/3m/6m/12m (hook lines).
2. RS new high: RS >= its 252-day (52-week) max; note whether RS led price to the high.
3. Mansfield RS > 0 and rising = outperforming; crossing 0 upward = improving [C, Weinstein].
4. RS trend: slope of a 50-day (10-week) SMA of RS.

### 11.2 Readings

| Reading | Meaning | Label |
|---|---|---|
| RS at a new 52-week high, price still below its high | leadership ahead of a breakout (underrated tell) | [C]; momentum [A] |
| Price at a new high, RS well below its high | laggard rally | [C] |
| Stock beats sector, sector beats SPY | best case | [A] industry momentum |
| Beats SPY only because the sector does | sector trade; note it | [C] |
| RS falling while price rises | distribution risk | [C] |
| RS flat or rising while SPY corrects | resilience; first candidates when the market turns | [C] |
| 12m RS strong, last month extreme | trend intact, reversal risk; prefer a pullback | [A] |

Momentum works over 3-12 months [A]; do not over-read 1-week RS. After a deep, volatile market decline, judge leadership by RS gained since the market low (`02` 11) [A].

### 11.3 By trade_type

Deciding lookback: 1-3 months (short_swing, sector ETF first), 3-6 months (swing), 6-12 months (long_swing), 12 months and multi-year (investment, SPY first). Minimums: section 15.

## 12. Market regime filter

### 12.1 Inputs (SPY, QQQ, 11 sector ETFs, unless regime is given upstream)

| Input | Risk-on | Neutral | Risk-off | Label |
|---|---|---|---|---|
| SPY vs SMA200 | above, rising | above and flat, or just below a rising one | below, falling | [A] old index evidence (BLL 1992) / [C] |
| SPY monthly close vs 10-month SMA (long_swing, investment) | above | within 2% | below | [P] Faber 2007 (mainly smaller drawdowns) |
| SPY vs SMA50 | above | crossing | below | [C] |
| SPY below its 52-week high | < 5-8% | 8-15% | > 15-20% | [A] Li and Yu (2012) nearness effect; cut-offs [C] |
| Sector ETFs above SMA200 | >= 8 of 11 | 5-7 | <= 4 | [C] house default breadth proxy |
| SPY/QQQ distribution days (down >= 0.2% on higher volume, 25 sessions) | <= 3 | 4-5 | >= 6 | [C] IBD; ETF volume is a proxy |
| VIX / % of members above SMA200 (if available) | < 20 / > 60% | 20-30 / 40-60% | > 30 or +50% in a month / < 40% | [C]; panic states hurt momentum [A] |

Regime = majority of available inputs; SPY vs SMA200 breaks ties. Record each input.

### 12.2 Rules

- risk_on: normal standards. neutral: grade A or B only, prefer RS leaders, favour first targets. risk_off: long_swing/investment only stage 1-to-2 transitions with RS at new highs; short_swing/swing only grade A with shorter holds; say regime lowers confidence. One strong chart never overrides regime (momentum's regime dependence is [A]).
- Read regime on the trade's timeframe: short_swing on SPY daily (SMA50, distribution days); investment on SPY monthly (10-month SMA).
- If the regime drops a class before the human acts, the plan must be re-checked (`06` 9).

## 13. Multi-timeframe alignment

Principle [C] (Elder triple screen): trade with the higher timeframe; time entries on the lower.

### 13.1 Matrix (long-only)

| Context | Primary | Grade | Allowed |
|---|---|---|---|
| stage 2 / uptrend | uptrend | A | breakouts, pullbacks |
| stage 2 / uptrend | pullback or range inside it | A | pullback to support with a reversal trigger |
| stage 2 / uptrend | downtrend (broke last HL) | C | wait for repair (new HL + close above last LH) |
| stage 1 | breakout from base | B | early stage 2; smaller first tranche (`06` 10) |
| stage 1 | range | C | watch (investment may scale in at base support, structural stop) |
| stage 3 | any | D | no new longs |
| stage 4 / downtrend | any bounce | F | no longs |

### 13.2 Rules

1. Context decides direction, primary decides levels, trigger decides timing. No levels from the trigger chart when the primary is weekly (except the daily "hard" level of `05` 7.2, stated).
2. A primary signal against the context trend needs structure repair plus RS improvement and is capped at grade C.
3. Conflicting reads on one timeframe (price up, OBV diverging) lower confidence one notch; they never flip direction.
4. For investment, a weekly signal outranks all daily signals.

## 14. Reading the hook's statistics block

| Line | Extract | Checks |
|---|---|---|
| Title, bar count, dates | coverage | Last bar = last trading day <= `as_of`, else stale. < 252 bars: short "52-week" range, no 12m return; < 200: no SMA200. |
| Last close (high, low) | CLV, range vs ATR | WRB, NR, reversal bar? |
| Returns | momentum profile | 6m, 12m > 0 = trend [A]; extreme 1w/1m = reversal risk [A]; compare with SPY/sector lines. |
| SMA20/50/200, % distance | stack, extension | Convert to ATRs; compute slopes from `raw/`. |
| 52-week closing and intraday range | 52-week-high ratio; blue sky vs overhead supply | Intraday high > ~1 ATR above the closing high (house default) = failed probe: wick resistance zone between them. |
| ATR14, % of close | volatility class, stop feasibility | 10.2 |
| Dollar volume (20 bars) | liquidity | 7.3; share-volume averages and RVOL from `raw/` |
| Swing highs/lows (last 6) | structure, levels | 4.2 lag and noise filter |
| Weekly bars (last 104, ISO weeks) | context trend, weekly pivots and ATR, 10-week/30-week/40-week | first week may be partial, last may be in progress (8.4); holiday weeks have 4 days |

Multi-call fetches: take returns, SMAs, 52-week range and ATR from the call ending at `as_of`; older calls give history and levels only. Cite the raw file behind every derived number (`prompts/shared.md`).

## 15. Procedure per trade_type

Common steps: (1) fetch in one message: stock bars (1.2), SPY, sector ETF, QQQ if relevant, the 11 sector ETFs unless regime is given upstream, indicators, current price, next earnings; (2) section 3 in order, one line per step; (3) knockouts (16.1): any one = reject and stop; (4) score (16.2-16.3); (5) setup and plan via `03`, `04`, `06`, `07`, `08`, events via `09`. Exit, invalidation and time stop are fixed before any entry is proposed; a plan without a time stop is incomplete (`08` 6).

| Step | short_swing (3-15 days) | swing (2-8 weeks) | long_swing (2-6 months) | investment (6 months+) |
|---|---|---|---|---|
| Regime input | SPY daily vs SMA50/200, distribution days | SPY vs rising SMA200 | SPY vs 40-week | SPY vs 10-month SMA |
| Context needed | weekly not stage 3/4; close > SMA50 preferred | weekly stage 2 or late stage 1 breakout; SMA200 and 30-week rising | weekly stage 2, 30-week rising >= 4 weeks, or stage 1 breakout; monthly not down | monthly HH+HL or completed multi-year base; monthly close > 10-month SMA; prefer first stage 2 after a long base |
| Structure | daily 3-4 months; active swing (pullback, breakout, 1-3 week flag) | daily HH+HL 3-6 months; base or pullback | weekly pivots 2 years; daily for entry/stop only | weekly stages 5 years; monthly pivots |
| Levels | daily zones within ~3 ATR, recent gaps, SMA20/EMA21 | daily/weekly pivots 1 year, 52-week high, SMA50, prior breakouts | weekly zones, multi-year highs, 30-week/40-week | monthly/weekly zones, all-time high, 40-week, big round numbers |
| Volume | breakout RVOL >= 1.5 or dry-up (20-day) | 50-day U/D, acc/dist days, dry-up | weekly breakout V vs 10-week avg; weekly U/D in base | multi-year volume trend; weekly climaxes |
| Max extension at entry (not "extended", 9.2) | d vs EMA21 <= 3 | d vs SMA50 <= 5 | weekly d vs 10-week <= 3 | <= 40% above 40-week, else staged entry (`06` 10) |
| RS needed | not falling 1 month vs sector | 3m and 6m > 0 vs SPY and sector | 6m and 12m > 0; Mansfield > 0 rising | 12m > 0; multi-year RS uptrend |
| Typical structural stop (`05` 7.1) | 1.5-2.5 daily ATR from entry; buffer 0.25-0.5 ATR beyond the level; >= 0.75 ATR from entry | 2-3.5 daily ATR; buffer 0.5-1 ATR; >= 1 ATR from entry | 1-2 weekly ATR; buffer 0.25-0.5 weekly ATR; daily hard stop; if > 8%, reject rather than tighten | 1.5-3 weekly ATR; buffer 0.5 weekly ATR; daily hard stop; 8% cap often binds |
| Events (8.5) | report inside the hold: avoid unless the plan is built around it | decide hold-through by `09` 4.2 | expect 1-2 reports: compare the largest past reaction gap with the stop (`09` 2.3, 4.2) | several reports; judge each reaction at checkpoints (`09` 3) |
| Room and time (k <= 1.5, `05` 5.3) | >= 2R; T1 within ~3.7 daily ATR (k over 15 bars) | >= 2R to next major resistance or measured move; T1 within ~6 daily ATR (40 bars) | >= 2R to weekly resistance; T1 within ~4.8 weekly ATR (26 weeks) | chart times entry and sets thesis invalidation; fundamentals upstream |
| Horizon, `chart_timeframe` | `swing`, `1d` | `swing`, `1d` | `swing` if max hold <= ~3 months else `long_term`; `1w` | `long_term`, `1w` |

The `## Setup` body condenses the section 3 lines: regime, sector, stage, structure, top 3 levels with grades, volume, extension, ATR% and gap count, RS, next event, alignment, score.

## 16. Chart quality score

House rubric [C]: criteria follow section 2; weights and cut-offs are not backtested. Report each line with its number and raw file.

### 16.1 Knockouts (any one = reject for longs)

| Knockout | Test |
|---|---|
| Stage 4 / downtrend on context | 5.1; grade F |
| Stage 3 on context | grade D |
| No feasible stop | chart stop > `max_loss_per_trade_pct` (10.2) |
| No room | nearest major resistance < `min_reward_to_risk` x risk above entry, no clean break setup (6.4) |
| Illiquid | 20-day dollar volume < $5M for short_swing/swing (house default) |
| Unusable data | too few bars for the type and cannot fetch more, or unresolved split/bad rows (8.5) |

### 16.2 Scored criteria (0/1/2; max 24; evidence per section 2)

| # | Criterion | 2 | 1 | 0 |
|---|---|---|---|---|
| 1 | Regime | risk_on | neutral | risk_off |
| 2 | Sector vs SPY | RS rising, ETF above SMA200 | flat | lagging, below SMA200 |
| 3 | Context stage | stage 2, MA rising | early stage 2 / late stage 1 breakout | stage 1 range |
| 4 | Primary structure | clean HH+HL, shallow pullbacks | one ambiguity | range/transition |
| 5 | Momentum | 6m, 12m > 0 and 52-week-high ratio >= 0.90 | mixed, ratio 0.75-0.90 | 6m < 0 or ratio < 0.75 |
| 6 | RS | new RS high, or vs SPY and sector both rising | one positive | both negative |
| 7 | Level clarity | entry and stop at major levels | intermediate | minor/undefined |
| 8 | Room | >= 3R, or blue sky with a measured move | 2R-3R | < 2R |
| 9 | Volume | U/D > 1.2 and breakout RVOL >= 1.4 (short_swing 1.5) or dry-up | neutral | U/D < 0.8, heavy down days |
| 10 | Extension | normal (9.2) | between normal and extended, or extended with the entry planned at a pullback | climactic at entry |
| 11 | Volatility and gaps | stop <= 0.6 x max loss, ATR ratio 0.8-1.3, few non-earnings gaps | stop fits; ATR ratio outside band or gappy | stop barely fits with ATR expanding on down bars, or largest adverse gap > max loss |
| 12 | Alignment | A | B | C |

Earnings inside the hold is not scored: it is the `upcoming_earnings` flag and `09`.

### 16.3 Interpretation

| Total | Grade | Meaning |
|---|---|---|
| 19-24 | A | clean; normal confidence; full plan |
| 14-18 | B | tradeable; list weak criteria as `away` factors; staged entry or first target |
| 9-13 | C | marginal; only a strong setup outside risk_off; usually wait |
| 0-8 | D | reject on chart grounds |

A 0 on #1, #3, #5 or #6 caps the grade at C. Report total, grade and every 0 in factors. Never round up to reach a pass; a clean reject is a correct outcome.

## 17. Common reading errors

- A level as one price; an in-progress weekly bar treated as closed; missing a swing because pivots lag 5 bars; stats from an older call used as current.
- Any high-volume day called accumulation (needs an up close, CLV > 0.5; earnings days go to `09`); candle names or Fibonacci ratios read as signals; one-week RS over-read.
- Buying because a stock is far below its high (nearness to the high is the [A] positive); ignoring regime.
- A first close above a level treated as confirmed with no failure plan (6.5); assuming a stop fills at its price in a gappy stock (8.5); tightening a stop to pass the 8% rule instead of rejecting; an entry without exit, invalidation and time stop.

Shorts (only if `allow_short: true`) mirror all of this: stage 4, LH+LL, RS new lows, breakdowns on volume, rallies on dry volume; squeeze and gap risk are larger.

## Sources

Academic
- Avramov, Kaplanski, Subrahmanyam (2021), Review of Financial Economics 39(2).
- Bhattacharya, Holden, Jacobsen (2012), Management Science 58(2) (not re-checked online).
- Blume, Easley, O'Hara (1994), Journal of Finance 49(1).
- Bollerslev (1986), Journal of Econometrics 31; Engle (1982), Econometrica 50(4) (not re-checked online).
- Brock, Lakonishok, LeBaron (1992), Journal of Finance 47.
- Caginalp, Laurent (1998), Applied Mathematical Finance 5.
- Cooper, Gutierrez, Hameed (2004), Journal of Finance 59(3).
- Daniel, Moskowitz (2016), Journal of Financial Economics.
- Donaldson, Kim (1993), JFQA 28(3).
- George, Hwang (2004), Journal of Finance 59.
- Gervais, Kaniel, Mingelgrin (2001), Journal of Finance 56(3).
- Jegadeesh (1990), Journal of Finance 45(3).
- Jegadeesh, Titman (1993), Journal of Finance 48(1) (not re-checked online).
- Kavajecz, Odders-White (2004), Review of Financial Studies 17(4).
- Lee, Swaminathan (2000), Journal of Finance 55.
- Lehmann (1990), QJE 105(1).
- Ley, Varian (1994), Applied Financial Economics 4(3) (not re-checked online).
- Li, Yu (2012), JFE 104(2).
- Lo, Mamaysky, Wang (2000), Journal of Finance 55.
- Marshall, Young, Rose (2006), Journal of Banking and Finance 30.
- Moskowitz, Grinblatt (1999), Journal of Finance 54(4).
- Moskowitz, Ooi, Pedersen (2012), JFE.
- Osler (2000), FRBNY Economic Policy Review 6(2).
- Park, Irwin (2007), Journal of Economic Surveys 21(4).
- Sullivan, Timmermann, White (1999), Journal of Finance 54(5).

Practitioner
- Faber (2007), A Quantitative Approach to Tactical Asset Allocation, SSRN 962461. https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf
- Bulkowski, Encyclopedia of Chart Patterns; https://thepatternsite.com/volbkout.html, https://thepatternsite.com/gaps.html (described qualitatively; figures not verified directly).
- O'Neil, How to Make Money in Stocks (breakout volume, distribution days). https://finance.yahoo.com/news/watch-distribution-days-spot-peaks-220700524.html
- Weinstein, Secrets for Profiting in Bull and Bear Markets. https://www.stageanalysis.net/blog/4266/how-to-create-the-mansfield-relative-performance-indicator
- Minervini, Trade Like a Stock Market Wizard (trend template, VCP).
- StockCharts ChartSchool (Wyckoff tutorial; Chaikin Money Flow/CLV); Kaufman efficiency ratio: https://help.tc2000.com/m/69404/l/749623-kaufman-efficiency-ratio
- Select Sector SPDR tickers, https://www.sectorspdrs.com/ (not re-checked online; site unreachable from this environment)
- Definitions only: Wilder (ATR, ADX); Elder (triple screen); Edwards and Magee, Murphy (Dow theory, S/R, trendlines, gaps, volume); Bollinger (bandwidth, squeeze); Granville (OBV); Crabel (NR4/NR7; futures, intraday).
