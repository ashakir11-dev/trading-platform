# 02 - Indicators

## How to use this file

- Follow **section 13** (data gate -> regime -> trend block -> volatility -> volume -> timing -> plan fields). Pick the stack in **section 10**, then look up each indicator in the **master table** (3) and its card (5-7).
- Count **one vote per redundancy group** (8): three oscillators agreeing is one vote; trend, 12-1 momentum and RS form one "trend block".
- Indicators confirm or time what price structure shows; they never set a stop or target alone (levels `01`, `03`; exits `07`; clocks `08`; earnings `09`).
- Labels: [A] academic/replicated, [P] practitioner study, [C] convention/house default, [S] speculative/contested. Examples are hypothetical.
- Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).

## 1. Ground rules

### 1.1 Where each number comes from

| Source | Gives | Notes |
|---|---|---|
| Price hook (`GetStockPrices`) | returns 1w-12m/YTD (5/21/63/126/252 bars); SMA20/50/200 + % distance; closing/intraday high-low of the last <= 252 fetched bars; ATR14 (Wilder); 20-day dollar volume; last 6 5-bar pivots; <= 104 weekly bars | "52-week" range = bars fetched only. Newest listed pivot is >= 5 bars old: find later swings in raw rows. No EMA, no share-volume average. |
| `GetAverageTrueRange`, `GetBollingerBands`, `GetStochasticOscillator`, `GetOnBalanceVolume` | named indicators | Record stated parameters; if absent or wrong, compute. Backtests: only if every row is <= `as_of`. |
| Raw bars (`raw/NNN-GetStockPrices.json`) | everything else | Show inputs (dates, window). |
| SPY/QQQ, sector ETF via `GetStockPrices` | regime, RS | Same dates and `as_of`. |
| Not this agent's tools | VIX, put/call, short interest, breadth | Only from an upstream `raw/` (11.4). |

### 1.2 Computation conventions (state them when used)

| Item | Definition |
|---|---|
| True range | TR = max(H - L, abs(H - C_prev), abs(L - C_prev)) |
| SMA / EMA | SMA(n) = mean of last n closes. EMA: alpha = 2/(n+1); EMA_t = alpha*C_t + (1-alpha)*EMA_{t-1}; seed = SMA of first n |
| Wilder(n) | S_t = (S_{t-1}*(n-1) + x_t)/n, seed = mean of first n; = EMA of span 2n-1 (ATR, RSI, ADX) |
| Warm-up | Seed weight < 1% after a further ~2.3*(n+1) bars (EMA) or ~4.6*n (Wilder): EMA26 ~86 total, RSI14/ATR14 ~78, MACD signal ~90-100, ADX14 100+. Fetch >= 250 bars (weekly: same count in weeks). |
| Weekly/monthly bar | first open, max high, min low, last close, summed volume. A partial period (mid-week `as_of`, or a daily bar before 16:00 New York) is not a completed bar: signals use completed bars only. |
| Typical price | TP = (H + L + C)/3 |
| Slope over k | (X_t/X_{t-k} - 1)*100 or (X_t - X_{t-k})/ATR14; state which |
| Depth | <= 500 rows per call; SMA200 needs 200+ bars, so fetch ~1 year even for short_swing |
| Adjustment | Hook returns are price-only (studies use total returns). A one-day ~-50%/-67% move on a volume jump with no news = suspect an unadjusted split: compute after it. |

### 1.3 Parameter discipline

Use section 4's defaults; never tune to the chart: the best of ~7,800 rules on the Dow survived data-snooping correction in 1897-1986 but not in 1987-1996 (Sullivan, Timmermann & White 1999) [A]; with false-discovery control and costs, winners did not persist (Bajgrowicz & Scaillet 2012) [A]; anomalies shrink ~26% out of sample and ~58% post-publication (McLean & Pontiff 2016) [A]. Faber (2007) picked the 10-month SMA unoptimised and reports nearby lengths behave similarly [P].

## 2. What the evidence says

| Finding | Label | Consequence |
|---|---|---|
| 3-12 month winners keep outperforming (Jegadeesh & Titman 1993); own 12m return predicts the next 1-12m (Moskowitz, Ooi & Pedersen 2012; Hurst et al. 2017, futures; stocks noisier, Lim, Wang & Yao 2018) | [A] | 12-1 and 3-12m RS are the best chart inputs for swing+; weight market/sector trend too. |
| Nearness to the 52-week high explains much of momentum, no long-run reversal (George & Hwang 2004) | [A] | Near-high is strength, not "overbought". |
| MA and range-break rules worked on the Dow 1897-1986 (Brock, Lakonishok & LeBaron 1992), not after (Sullivan et al. 1999; Bajgrowicz & Scaillet 2012) | [A] | Trend filters, not standalone edges. |
| MA timing pays more on high-volatility portfolios (Han, Yang & Zhou 2013); MA rules are weighted sums of past price changes (Zakamulin 2017; Marshall et al. 2017) | [A] | Filters matter most for volatile names; price-vs-MA and momentum are one block. |
| SMA21/SMA200 distance adds beyond momentum (Avramov, Kaplanski & Subrahmanyam 2021, one study); smooth momentum persists, jumpy does not (Da, Gurun & Warachka 2014) | [A] | Underrated quality gauges (7.6, 7.7). |
| 1-week/1-month losers beat winners next period (Jegadeesh 1990; Lehmann 1990), mostly in illiquid stocks and eaten by costs (Avramov, Chordia & Goyal 2006) | [A] | Buy short dips in uptrends; don't chase spikes. A tilt only. |
| Top-decile volume days/weeks precede higher next-month returns (Gervais, Kaniel & Mingelgrin 2001); months-long high-turnover winners reverse sooner (Lee & Swaminathan 2000) | [A] | RVOL matters over ~1 month; heavy-turnover leaders are late-stage. |
| Momentum crashes in high-volatility rebounds, driven by losers (Daniel & Moskowitz 2016); vol-scaling nearly doubled its Sharpe (Barroso & Santa-Clara 2015) | [A] | Long-only: winners lag; size down in high volatility (`08`). |
| 95 TA studies: 56 positive, 20 negative, 19 mixed, most with snooping/cost issues (Park & Irwin 2007); RSI/MACD rule tests mixed by market | [A] | Oscillators time entries; they are not reasons to trade. |
| Pattern detection shifts return distributions (Lo, Mamaysky & Wang 2000), not shown profitable after costs | [A] | Structure first. |

## 3. Master table

Groups: **T** trend, **Ts** trend strength, **M** oscillator/timing, **Ml** intermediate momentum, **V** volatility, **Vol** volume flow, **RS** relative strength, **X** trail, **L** level tool (no vote). Tier 1 best, 2 most common, 3 underrated. Get: H hook, Tool named tool, C compute. swing+ = swing, long_swing, investment. Parameters: section 4.

| Indicator | Tier | Family (group) | Best trade_types | Get | Evidence |
|---|---|---|---|---|---|
| Price vs SMA50/200, 10/30/40-week, 10-month | 1 | trend (T) | all | H/C | [A] index; [C] stock thresholds |
| MA slope | 1 | trend (T) | all | C | [A] identity |
| 12-1 momentum, ROC 3m/6m | 1 | momentum (Ml) | swing+ | H | [A] |
| 52-week-high proximity | 1 | trend (T) | swing+ | H | [A] |
| RS line, Mansfield RS | 1 | rel. strength (RS) | all | C | [A] concept, [C] form |
| ATR14, ATR% | 1 | volatility (V) | all | H/Tool | [C]; clustering [A] |
| Donchian / N-bar breakout | 1 | trend (T) | short_swing, swing | C | [A] historic; [S] stand-alone |
| Relative volume (RVOL) | 1 | volume (Vol) | all | C | [A] effect, [C] threshold |
| Chandelier exit | 1 | trail (X) | swing, long_swing | C | [C] |
| EMA 10/21, crossovers, ribbons | 2 | trend (T) | short_swing, swing | C | [C] |
| MACD / PPO (12,26,9) | 2 | momentum (M (zero line T)) | swing, long_swing | C | [C]; tests [S] |
| RSI(14) | 2 | momentum (M) | swing | C | [C]; 70/30 [S] |
| Short ROC (10-21) | 2 | momentum (M) | short_swing | C | [C] |
| Stochastic (14,3,3), Williams %R | 2 | momentum (M) | short_swing | Tool/C | [C]/[S] |
| CCI(20) | 2 | momentum (M) | short_swing | C | [C]/[S] |
| Bollinger Bands (20,2) | 2 | volatility (V) | short_swing, swing | Tool | [C] |
| ADX/DMI(14) | 2 | trend strength (Ts) | swing, long_swing | C | [C] |
| OBV | 2 | volume (Vol) | swing, long_swing | Tool | [C]/[S] |
| Parabolic SAR | 2 | trail (X) | rarely | C | [S] |
| Supertrend (10,3) | 2 | trail (X) | short_swing, swing | C | [C] |
| Ichimoku (9,26,52) | 2 | trend (T) | long_swing | C | [C]/[S] |
| RSI(2) pullback | 3 | reversal timing (M) | short_swing | C | [P] no-stop tests; reversal [A] |
| NR4/NR7/inside day | 3 | volatility (V) | short_swing, swing | C | [P] intraday; [C] multi-day |
| BandWidth squeeze, %B | 3 | volatility (V) | short_swing, swing | Tool/C | [C] |
| Keltner (20,2,ATR10) | 3 | volatility (V) | short_swing, swing | C | [C] |
| HV ratio | 3 | volatility (V) | all but investment | C | [A] clustering, [C] use |
| MA distance SMA21/SMA200 | 3 | trend (T) | swing+ | C (H proxy) | [A] one study |
| Frog-in-the-pan ID | 3 | momentum quality (Ml) | long_swing, investment | C | [A] |
| Regression slope x R^2 (90) | 3 | trend quality (T) | swing, long_swing | C | [P] ranking |
| Kaufman ER (10/20) | 3 | trend strength (Ts) | all | C | [C] |
| Aroon(25) | 3 | trend age (Ts) | swing | C | [C] |
| TSI (25,13) | 3 | momentum (M) | swing | C | [C] |
| Anchored VWAP (daily TP) | 3 | volume-price (L) | all | C | [C] |
| Volume-by-price (daily approx.) | 3 | volume-price (L) | swing, long_swing | C | [C] |
| Up/down volume ratio (50) | 3 | volume (Vol) | swing, long_swing | C | [C] |
| Pocket pivot (10) | 3 | volume trigger (Vol) | short_swing, swing | C | [C] |
| A/D line, CMF(20) | 3 | volume (Vol) | swing | C | [C]/[S] |
| MFI(14) | 3 | volume-momentum (M) | short_swing | C | [C]/[S] |
| Force index (2,13) | 3 | volume-momentum (Vol) | short_swing, swing | C | [C] |
| IBD-style RS score / percentile | 3 | rel. strength (RS) | swing, long_swing | C | [A] concept, [C] weights |
| Breadth/sentiment | context | regime | all | upstream | [C]/[S] |

## 4. Parameters per trade_type

[C] unless labelled; not optimised. D daily, W weekly, Mo monthly. Oscillator lengths are not rescaled across timeframes (weekly RSI14 is not daily RSI70; `05` 5.1).

| Indicator | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Trend MAs | EMA10, EMA21 (D); SMA50 context | SMA50, SMA200; EMA21 for pullbacks | 10-week, 30-week; 40-week context | 40-week; 10-month [P] |
| MA slope window | EMA21 (or SMA20) over 5 bars | SMA50 over 20; SMA200 over 20 | 30-week over 4 W | 40-week over 8-13 W |
| Momentum | 1m ROC | 3m, 6m; 12-1 filter | 6m, 12-1 | 12-1 |
| RS window | 21-63 bars vs sector ETF | 63-126 bars; Mansfield D 252 | Mansfield W 52 | Mansfield W 52 |
| ATR | ATR14 D | ATR14 D (ATR22 chandelier) | ATR14 W (+ D for buffers) | ATR14 W |
| Donchian | 10, 20 | 20, 55 | 20-week, 52-week | 52-week |
| Chandelier (`07` 8.1) | HH10 - 2 x ATR14 | HH22 - 3 x ATR22 (LeBeau) | HH10W - 2.5-3 x weekly ATR14 | HH26W - 3 x weekly ATR14 |
| RVOL | V / avg20 | V / avg50 | W vol / 10-week avg | W vol / 10-week avg |
| Oscillator (one) | RSI(2) or Stoch(14,3,3) | RSI(14) or MACD | MACD W or RSI(14) W | RSI(14) W, context |
| Bands | BB(20,2), squeeze lookback 125; Keltner(20,1.5-2) | BB(20,2) D | BB(20,2) W | not used |
| Trend strength (one) | ER(10) D | ADX14 or ER(20) D | ADX14 W or ER(10) W | ER(10) W |
| HV ratio | HV10/HV100 | HV20/HV100 | HV10/HV52 W | not used |
| Volume flow (one) | CMF(20) or pocket pivot | OBV or U/D (50) | OBV W | OBV W |

## 5. Tier 1: best

Each card: measures and formula | read | lies when | evidence, group.

### 5.1 Price vs moving average
- Trend position: (C/SMA_n - 1)*100; weekly SMAs from the hook's weekly closes. Weinstein [C]: stage 2 = above a rising 30-week SMA, stage 4 = below a falling one.
- Read: longs need price above a rising SMA200 (swing), 30/40-week (long_swing, investment) or SMA50/EMA21 (short_swing). Minervini trend template [C]: `01` 5.1. Extension d = (C - MA)/ATR14 per `01` 9.2 (swing: extended if d > 5 vs SMA50) = wait for a pullback, not a short.
- Lies: ranges, V-shaped reversals, gaps. [A] index/portfolio, weak after 1986; [P] Faber; stock thresholds [C]. T.

### 5.2 Moving-average slope
- (SMA_t/SMA_{t-k} - 1)*100 or per ATR. Identity: SMA_n(t) - SMA_n(t-1) = (C_t - C_{t-n})/n, so SMA direction = sign of n-bar momentum (exact), and tomorrow's tick is known: up if tomorrow's close > the close dropping out.
- Read: rising = trend; flat (< ~0.5 ATR over the window) = range tactics; falling = no swing+ longs without a completed base (`03`).
- Lies: after sharp reversals (lag (n-1)/2 bars). Identity exact, momentum [A], thresholds [C]. T.

### 5.3 12-1 momentum and ROC
- ROC_n = (C_t/C_{t-n} - 1)*100. 12-1 = (1 + R12)/(1 + R1) - 1 from the hook (exact: 252/21-bar offsets). The sign is the time-series read; vs SPY/sector is the cross-sectional read.
- Read: positive and above SPY and sector = leader; negative = no swing+ long without a confirmed base. short_swing: 1m ROC for strength; a big 1w spike = don't chase (reversal [A]).
- Lies: sharp post-bear rebounds; trends built by one gap [A]. [A]. Ml.

### 5.4 52-week-high proximity
- C / highest close of last 252 bars (George & Hwang used the highest daily CRSP price, i.e. a close; the intraday-high version differs: state which).
- Read: >= ~0.90 in a rising trend = leadership [C threshold]; new closing high from a sound base = breakout candidate (`03`, `04` S5).
- Lies: one-day spike highs; takeover re-ratings; thin names; < 252 bars fetched. [A] cross-sectional. T.

### 5.5 RS line and Mansfield RS
- RS_t = C_stock/C_bench on common dates; Mansfield = (RS_t/SMA(RS, n) - 1)*100, n = 52 weekly (Weinstein) or 252 daily (some platforms use 200; state which).
- Read: RS new high with or before price = best breakout confirmation [C, O'Neil]; Mansfield > 0 and rising = outperforming [C, Weinstein]; price up with RS falling = laggard, downgrade or reject. Minimums per trade_type: `01` 11.3.
- Lies: falling benchmark (check absolute trend); ETF dominated by the stock (use SPY). [A] concept, [C] form. RS.

### 5.6 ATR14 and ATR%
- Wilder ATR; ATR% = ATR/C*100 (hook gives both).
- Read: ruler for buffers, extension, size. Max stop multiple = `max_loss_per_trade_pct` / ATR% (`01` 10.2); structural stop fails `max_loss` -> reject, never tighten. Stops inside ~1 ATR are noise-prone for swing [C]. Falling ATR in a base = constructive.
- Lies: inflated after an earnings gap (decay 13/14 per bar: ~35% of the excess left after 14 bars, ~11% after 30); understates the coming earnings move (`09`); not directional. Definition [C]; clustering [A] (Engle 1982; Bollerslev 1986). V.

### 5.7 Donchian channel / N-bar breakout
- Upper = highest high of the prior n bars (exclude today); lower = lowest low; mid = average.
- Read: close above the prior n-bar high = continuation trigger (Turtles, a futures system: 20-day entry/10-day exit, 55/20; Faith 2007) [C]; shorter-window low = trail; 52-week breakout with volume and RS = investment-grade signal (52-week-high effect [A]).
- Lies: ranges, low-volume breaks, breaks into earnings, channel set by one spike bar. [A] historic (BLL), [S] stand-alone today. T.

### 5.8 Relative volume (RVOL)
- RVOL = V_t / mean(V of prior 50 bars) (20 for short_swing, as `01` 1.3); weekly vs prior 10 weeks.
- Read: breakout RVOL >= 1.4 (short_swing 1.5) [C house default; O'Neil asks 40-50%+ above average]; pullback dry-up < 0.7-1.0 = healthy; down close on RVOL > ~1.5 near highs = distribution warning [C] (IBD's distribution day is an index rule: down >= 0.2% on volume above the prior day's). Top-decile volume precedes higher next-month returns [A].
- Lies: earnings, rebalances, option expiry, half-days, partial bars. Vol.

### 5.9 Chandelier exit
- Long stop = highest high(n) - m x ATR(n); LeBeau 22, 3; ratchet only. Values in section 4; activation and rules in `07` 8.
- Lies: parabolic moves (too loose), gap-downs. Pair with a close rule in `close` mode. [C] (no published test found). X.

## 6. Tier 2: most common, and how they are misused

### 6.1 EMA10/EMA21, crossovers, ribbons
- Golden cross = SMA50 above SMA200; ribbon = EMAs 10..60 (fanned = trend, braided = range). EMA10/21 = pullback zones in strong short_swing/swing trends [C].
- Misuse: counting price>MA, cross and ribbon as three votes (all T; crossovers are momentum rules, Zakamulin 2017 [A]); EMA as a hard level; buying a golden cross after a large run. [C].

### 6.2 MACD and PPO
- MACD = EMA12 - EMA26; signal = EMA9(MACD); histogram = MACD - signal; PPO = MACD/EMA26*100 (prefer: comparable across prices).
- Read: MACD > 0 is trend information (T). Histogram turning up below zero in an uptrend pullback = momentum resuming [C]; weekly zero-line cross = slow long_swing marker.
- Misuse: signal-line crosses alone; divergences as reversal calls (9). Lies in ranges and after gaps. [C]; tests mixed [S]. M.

### 6.3 RSI(14)
- Gain = max(C - C_prev, 0), loss = max(C_prev - C, 0); Wilder-smooth each; RSI = 100 - 100/(1 + avgGain/avgLoss).
- Read: 70/30 are convention. Regime ranges [C] (Cardwell; Brown 1999): uptrends hold ~40-80, pullbacks bottom near 40-50; downtrends ~20-60, rallies stall near 50-60 (do not buy that bounce). > 70 early in an uptrend = strength.
- Misuse: selling 70/buying 30 against the trend; "oversold" in stage 4. [C]; 70/30 rule [S]. M.

### 6.4 Short ROC, stochastic, Williams %R, CCI
- ROC(10-21) around zero is a noisy oscillator [C] (long ROC is 5.3).
- Stochastic: fast %K = (C - LL14)/(HH14 - LL14)*100; slow %K = SMA3(fast); %D = SMA3(slow). %R = (HH14 - C)/(HH14 - LL14) x -100 = fast %K - 100 (same information). Get `GetStochasticOscillator` (record fast/slow). Uptrend: slow %K < 20 crossing up through %D at support = short_swing timing; > 80 in uptrends is normal.
- CCI(20) = (TP - SMA20(TP)) / (0.015 x mean absolute deviation of TP); +/-100 used like stochastic; adds nothing beside RSI.
- Misuse: using more than one; trading every cross; fading pinned readings in trends. [C]/[S]. All M.

### 6.5 Bollinger Bands (20,2)
- Mid = SMA20 +/- 2 x population SD of 20 closes (sample SD is ~2.6% wider, sqrt(20/19)); %B = (C - lower)/(upper - lower); BandWidth = (upper - lower)/mid x 100. Check the tool's period, multiplier and SD type.
- Read: walking the upper band = strength [C]; mid-band pullbacks = routine entries; a close outside is not a sell. Squeeze: 7.3. Misuse: fading every upper-band touch. Lies after gaps. [C]. V.

### 6.6 ADX/DMI(14)
- +DM = H - H_prev if > (L_prev - L) and > 0, else 0; -DM = L_prev - L if > (H - H_prev) and > 0, else 0; Wilder-smooth TR, +DM, -DM; +DI = 100 x sm(+DM)/sm(TR), -DI likewise; DX = 100 x abs(+DI - -DI)/(+DI + -DI); ADX = Wilder(DX, 14).
- Read [C] (as `01` 4.3): > 25 trending, < 20 weak. Rising from < 20 with +DI > -DI = new trend; > 40 turning down = maturing, not reversal. Its job: choose tactics (> 25 breakouts and MA pullbacks; < 20 buy support only, nearer targets).
- Lies: lags (100+ bar warm-up); high ADX in a crash = downtrend. [C]. Ts.

### 6.7 OBV
- OBV_t = OBV_{t-1} + V if C > C_prev, - V if lower, else unchanged; read slope and relative highs (`GetOnBalanceVolume`).
- Read: new high with or before price = accumulation; falling in a flat base = distribution [C]. Lies: one event day dominates; a 0.01 up-close counts the whole day. [C]/[S]. Vol.

### 6.8 Parabolic SAR, Supertrend, Ichimoku
- SAR: SAR_{t+1} = SAR_t + AF x (EP - SAR_t); AF 0.02 step 0.02 max 0.20; in uptrends <= prior two lows. Always-in, whipsaws in stocks [S]; prefer the chandelier. X.
- Supertrend (10,3): bands (H+L)/2 +/- 3 x ATR10; final lower = max(basic lower, prior final lower) while prior close >= prior final lower, else basic lower (upper mirrored); flips on a close through the active band. An ATR trail [C]. X.
- Ichimoku: Tenkan = (HH9+LL9)/2; Kijun = (HH26+LL26)/2; Senkou A = (Tenkan+Kijun)/2, Senkou B = (HH52+LL52)/2, both shifted 26 forward; Chikou = close shifted 26 back. Above a rising cloud = uptrend; Kijun = pullback level. Adds little beyond MAs + Donchian mid [C]/[S]. T.

## 7. Tier 3: underrated

### 7.1 RSI(2) pullback (Connors)
- RSI with n = 2 (~10+ bars warm-up). Connors' rules [P]: close > SMA200; buy when RSI(2) closes < 5 (< 10 looser); exit on a close above SMA5; lower readings did better in his tests. Fits short-term reversal [A].
- Caveats: his tests (Connors & Alvarez 2008) had no stop and a quick exit, pre-publication; with a structural stop and 2R target his statistics do not transfer (1.3). Use only as a short_swing trigger; if 2R is not structurally available, reject. `08` clocks apply.
- Lies: stage 3/4; news-driven drops (`09`); SPY below SMA200. M.

### 7.2 NR4 / NR7 / inside day
- Range = H - L; NR7 = smallest of the last 7 bars, NR4 of 4; inside day = H < H_prev and L > L_prev; NR7 + inside = double compression.
- Read: contraction tends to precede expansion (Crabel 1990) [P for next-day intraday breakouts in futures/indexes; this multi-day use is C]. Trigger above the NR bar high (buy-stop, or close in `close` mode), only in a base or uptrend pullback; direction from structure [S otherwise]. Cancel if not triggered within ~3-5 bars [C house default]. Weekly NR bars time long_swing entries.
- Lies: pre-earnings compression; illiquid names. V.

### 7.3 BandWidth squeeze and %B
- Squeeze = BandWidth at its lowest of 125 bars (Bollinger/StockCharts) [C]. TTM variant (Carter) [C]: BB(20,2) inside Keltner(20,1.5); state mid-line and ATR period.
- Read: a bigger move is likely, not direction or timing (volatility persists, then mean-reverts [A]; squeezes can last weeks). Direction = trend + first close outside the band on RVOL > 1 with BandWidth expanding. Head fakes (Bollinger) [C]: cancel if price closes back inside the range within ~3 bars [C]. Directional edge [C]/[S]. V (not with NR7).

### 7.4 Keltner channels
- EMA20 +/- 2 x ATR10 (StockCharts default; Keltner's 1960 original used a 10-day SMA of TP +/- 10-day average range; state which).
- Read: ATR envelope, steadier than Bollinger. Close above the upper band early in an uptrend = thrust; EMA20 pullbacks = entries; repeated upper-band closes late in a move = climactic (`01` 9.2) [C]. V.

### 7.5 Historical volatility ratio
- r = ln(C_t/C_{t-1}); HV_n = sample SD(r, n) x sqrt(252) x 100 (weekly sqrt(52)). Ratio HV10/HV100 or HV20/HV100; Connors & Raschke (1995) used HV6/HV100 < 0.5 with NR4/inside day [C].
- Read: < ~0.5 quiet (base contraction); > 1.5 stressed (size down, `08`) [C thresholds; clustering A]. V.

### 7.6 Moving-average distance (MAD)
- SMA21/SMA200 (Avramov et al. 2021); hook proxy SMA20/SMA200 (say so).
- Read: > 1 and rising = strength; high-MAD stocks outperformed after controlling for momentum and 52-week proximity [A, one study]. For one stock a gauge, not a forecast; far above SMA200 is not bearish on multi-month horizons, it only worsens entry and stop distance. Lies in crash rebounds. T.

### 7.7 Frog-in-the-pan ID
- Over the 12-1 window: ID = sign(R_{12-1}) x (% down days - % up days); more negative = smoother.
- Read: at similar momentum, smooth trends persisted, jumpy ones did not [A] (Da et al. 2014). Prefer low ID for long_swing/investment. A quality modifier inside Ml, not a vote.

### 7.8 Regression slope x R^2 (Clenow)
- Regress ln(C) on t over 90 bars; annualised = (exp(252 x b) - 1) x 100; score = annualised x R^2. R^2 < ~0.5 = noisy [C, unattributed].
- Clenow ranks with stock > SMA100, index > SMA200 and no recent gap > 15% (book backtest) [P]. Use to separate orderly from erratic trends. T.

### 7.9 Kaufman efficiency ratio
- ER_n = abs(C_t - C_{t-n}) / sum abs(C_i - C_{i-1}) over n (10 Kaufman, or 20). 0 chop, 1 straight line.
- Read: ER(20) > 0.4 trend tactics, < 0.2 range tactics (house default as `01` 4.3) [C]. Daily vs weekly ER(10): a trend clean only on weekly suits long_swing/investment, not short_swing (`05` 4.1). Cheap ADX substitute. Ts.

### 7.10 Anchored VWAP from daily bars
- AVWAP_t = sum(TP_i x V_i)/sum(V_i) from anchor a to t ("approximated from daily typical price"). Anchor chosen for a stated reason before looking: short_swing pivot low, gap or breakout day; swing last earnings day or pivot low; long_swing base low; investment cycle low or 52-week high.
- Read (Shannon) [C]: above AVWAP from a key low = buyers since then in profit (support); AVWAP from a high = trapped buyers' cost (resistance); reclaiming the earnings-gap AVWAP = gap buyers back in control (`09`).
- Error is largest on wide-range and anchor days: a zone +/- 0.25-0.5 ATR [C, unattributed]. L; no test found.

### 7.11 Up/down volume ratio
- Volume on up closes / volume on down closes, last 50 bars (IBD) [C]. > 1 accumulation, > ~1.5 strong, < 1 distribution (`01` scores > 1.2 / < 0.8). Steadier than OBV. Vol.

### 7.12 A/D line and Chaikin money flow
- CLV = ((C - L) - (H - C))/(H - L) (0 if H = L); MFV = CLV x V; A/D = cumulative MFV; CMF(20) = sum MFV/sum V (Chaikin used 21). CLV alone = breakout-bar close location (`06` 5.1).
- Read: CMF persistently > +0.1 buying, < -0.1 selling [C]. Lies on gaps (a gap-up closing at its low reads as distribution). [C]/[S]. Vol: OBV or A/D/CMF, not both.

### 7.13 MFI, force index, TSI, Aroon
- MFI(14): MF = TP x V, positive if TP > TP_prev; MFI = 100 - 100/(1 + sum pos/sum neg); 80/20 [C]. Volume-weighted RSI: M, redundant.
- Force index (Elder): FI = (C - C_prev) x V; FI(2) = EMA2, FI(13) = EMA13. Uptrend: FI(2) < 0 = pullback buy zone; FI(13) > 0 = bulls in control [C]. Vol.
- TSI = 100 x EMA13(EMA25(m))/EMA13(EMA25(abs m)), m = C - C_prev; zero line = bias [C]. Instead of MACD, not with it. M.
- Aroon(25): Up = 100 x (25 - bars since 25-bar high)/25, Down likewise. Up > 70 and Down < 30 = fresh trend; both low = base [C]. Ts.

### 7.14 IBD-style RS score and percentile
- Community replication (IBD double-weights the latest quarter) [C]: 0.4 x ROC63 + 0.2 x (ROC126 + ROC189 + ROC252). Compare with SPY's and the sector ETF's score. A 1-99 percentile needs universe data: write `NOT CHECKED: percentile RS rank (no universe data)` unless upstream provides it. RS (not a second vote).

### 7.15 Pocket pivot (Morales & Kacher 2010)
- Up close whose volume exceeds the largest down-day volume of the prior 10 sessions, inside a base or at/just above a rising 10-day or 50-day MA, not extended [C].
- Read: early accumulation cue; can replace breakout RVOL as the short_swing/swing entry's volume condition. Void if extended or below a falling SMA50. No test found. Vol (one vote with RVOL).

### 7.16 Volume-by-price (daily approximation)
- Over the primary window (e.g. 1 year daily), 10-20 equal price bins [C house choice]; add each day's volume to its close's bin. Label "approximated from daily bars".
- Read [C]: heavy bins = support below / supply above; a thin zone above the pivot = room to run (`05` 5.3). Feeds level grading (`01` 6.3). L. Lies: window choice.

## 8. Redundancy and collinearity

| Group | Members | Default pick |
|---|---|---|
| T | price vs SMA, slope, crossovers, ribbons, MACD zero line, Ichimoku, Donchian mid, 52-week proximity, MAD, regression slope | price vs rising SMA50/200 or 30/40-week + 52-week proximity |
| Ts | ADX, ER, Aroon, R^2 | ER or ADX |
| M | RSI, RSI(2), stochastic, %R, CCI, MFI, TSI, short ROC, MACD histogram | RSI(14) swing; RSI(2) or stochastic short_swing |
| Ml | 12-1, 3m/6m ROC, ID | 12-1 |
| V | ATR, Bollinger, BandWidth, Keltner, HV, NR4/NR7 | ATR + one contraction measure |
| Vol | RVOL, pocket pivot, OBV, A/D, CMF, U/D, force index | RVOL at trigger + one flow measure |
| RS | RS line, Mansfield, IBD score | RS line vs SPY and sector ETF |
| X | chandelier, Supertrend, SAR, Donchian low | one trail per `07` 8.1 |
| L | AVWAP, volume-by-price | levels only |

Rules:
1. Votes = distinct agreeing groups, max one per group. M is timing; X and L are not votes.
2. T, Ml and RS are collinear: one **trend block**, rated strong / transitional / against. Independent evidence comes from volume and price structure. So at most ~4 independent votes exist (trend block, volume, contraction, structure); "10 of 12 indicators bullish" is a misuse.
3. T and Ml disagree (above SMA200, 12-1 negative) = transitional: short_swing tactics or reject.
4. Choose the stack before reading values; report every member, including dissenters. Never add indicators until one agrees.

## 9. Divergences

| Type | Definition (same pivot bars) | Reliability | Use |
|---|---|---|---|
| Regular bearish | price higher high, oscillator lower high | [S]: frequent in healthy trends, repeats | tighten trail (`07`), skip adds; never an exit alone |
| Regular bullish | price lower low, oscillator higher low | [S] | only after price confirms (higher low, level reclaim) |
| Hidden bullish | price higher low, oscillator lower low | [C]/[S] | supports an uptrend pullback entry |
| Hidden bearish | price lower high, oscillator higher high | [C]/[S] | downtrend: don't buy the bounce |
| Volume | price new high, OBV/A-D/U-D not confirming | [C]/[S] | downgrade breakout |
| RS | price new high, RS line not | [C] | prefer to reject breakout setups |

Calling one: use swing pivots 5-60 bars apart on the traded chart (weekly for long_swing/investment; weekly outranks daily); the first pivot's reading should be extreme (e.g. RSI > 70 or < 30) [C]; act only after price confirms. No rigorous evidence for divergence as a standalone signal: [S], low weight.

## 10. Minimal stacks

### 10.1 Per trade_type

| trade_type | Trend | Momentum/timing | Volatility | Volume | RS | Regime |
|---|---|---|---|---|---|---|
| short_swing | EMA21/SMA50 + SMA50 slope (D) | 1m ROC; RSI(2) or stochastic | ATR14, NR7/inside | RVOL(20) or pocket pivot | vs sector ETF, 21-63 bars | SPY vs SMA50/200 |
| swing | SMA50/200 + slopes; 52-week proximity | 12-1, 3m; RSI(14) | ATR14, squeeze | RVOL(50) + U/D or OBV | vs SPY and ETF, 63-126 bars | SPY vs rising SMA200 |
| long_swing | 10-week/30-week + slope; 52-week proximity | 12-1 (+ ID) | ATR14 W, HV ratio | weekly RVOL, OBV W | Mansfield W 52 | SPY vs 40-week |
| investment | 40-week and 10-month + slope | 12-1, 6m | ATR14 W (stop feasibility) | weekly breakout volume, OBV W | Mansfield W 52 | SPY vs 10-month |

### 10.2 Per setup (`03`, `04`)

| Setup | Go (all) | No-go |
|---|---|---|
| Breakout from base | contraction (BandWidth/NR) before; close above pivot/Donchian high + buffer; RVOL >= 1.4 (short_swing 1.5); CLV >= 0; RS at/near new high | RS lagging; RVOL < 1 with CLV < 0; earnings in the hold (`09`); > 3% past entry (stale_entry) or extended (`01` 9.2) |
| Pullback in uptrend | rising SMA50/EMA21; RSI(14) 40-50 or RSI(2) < 5-10; dip on RVOL < 1; reversal close above prior bar high | last swing low broken; news or high-volume dip; close > 1 ATR below the MA on RVOL > 1.2 |
| Volatility contraction | HV ratio/BandWidth low, shrinking pullbacks, U/D > 1; break of NR/squeeze high with RVOL | below a falling SMA200; contraction into earnings |
| Trend continuation (long_swing/investment) | rising 30/40-week, 12-1 > SPY's, Mansfield > 0; weekly close above prior weekly pivot or 10-week reclaim | flattening 40-week with Mansfield < 0 |
| Mean-reversion dip (short_swing) | rising SMA200; RSI(2) < 5 | stage 4; news drop; SPY below SMA200 |
| Bottom attempt | higher low + SMA50 (10-week) reclaim + rising RS; AVWAP from the high as first resistance | oscillator-only evidence; confidence stays low [S] |

### 10.3 Indicators in the plan fields ([C] house defaults; canonical values in `CONVENTIONS.md`)

| Field | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| `entry_condition` (structure + one volume cue, `level_trigger` mode; `06` 4-5) | close > P + 0.1 ATR, RVOL(20) >= 1.5 | close > P + 0.1 ATR, RVOL >= 1.4 | weekly close > P + 0.1 weekly ATR, week RVOL >= 1.2 | weekly close > P + 0.1 weekly ATR, or 10-week reclaim |
| `stop` (structure; ATR sizes only the buffer, `07` 3.3) | level - 0.25-0.5 ATR, >= 0.75 ATR from e | level - 0.5-1 ATR, >= 1 ATR from e | weekly level - 0.25-0.5 weekly ATR; daily-close hard stop within the cap | weekly level - 0.5 weekly ATR; daily-close hard stop within the cap |
| Trail after activation (`07` 8.2) | 2-bar pivot - 0.25 ATR or EMA10 close | EMA21 close or 5-bar pivot - 0.5 ATR | weekly close < 10-week | weekly close < 30/40-week |
| `invalidation` (indicator backstop; the setup's structural line comes first, `03` 2.6) | close < EMA21 | close < SMA50 | weekly close < 10-week | weekly close < rising 30-week |
| Clocks CP1 / CP2 / max hold (`08` 4) | bar 5 / 10 / 15 | bar 10 / 20 / 40 | week 6 / 13 / 26 | week 13 / 26 / 52 (re-underwrite) |

Every plan states stop, target, trail and clocks before entry. No indicator reading extends the max hold; a winner at max hold is re-underwritten (`08`).

## 11. Regime, events and liquidity

- **Regime** (`01` 12): SPY (QQQ for growth) above a rising SMA200 / 10-month SMA = risk-on (BLL 1992 [A], Faber 2007 [P]; "rising" [C]); below a falling one = no new swing+ longs unless RS is exceptional. Sector ETF above rising SMA50/200 for breakouts [C]. After deep, volatile declines prior winners lag (Daniel & Moskowitz 2016) [A]: judge leadership on RS since the low until SPY regains a rising SMA200.
- **Earnings in the hold** (`09`): pre-earnings squeezes/NR7 are event compression, not setups; ATR understates the move. No new short_swing entry across earnings; others per `09` and the `upcoming_earnings` flag.
- **0-10 bars after an earnings gap**: ATR/BandWidth/HV inflated, RSI/stochastic pinned, OBV/A-D jump, Donchian and pivots reset. Anchor AVWAP at the gap day, use gap-day high/low as levels, and name the distorted indicators.
- **Gaps and slippage**: a buy-stop fills above the trigger in a gap; if the open is beyond the stale cap, cancel (`06` 7-8); a close-mode trigger can close past `stale_entry`. Stops fill below the stop on gap-downs: note it for high-ATR% names (`07` 4).
- **Liquidity**: hook 20-day dollar volume < $5M = reject short_swing/swing, flag others (`01` 7.3) [C]; in thin names pivots, RVOL, NR bars and AVWAP are unreliable.
- **False breakouts** cluster in low-volume breaks, risk-off tapes and intraday pokes: in `close` mode require the close; in `intraday` mode add only after RVOL/CLV confirm (`06`).
- **Breadth/sentiment** (only from upstream `raw/`): VIX stress = size down (`01` 12.1) [C; momentum suffers in high-volatility states A]; put/call extremes = index-level contrarian colour [S]; short interest/days to cover = crowding or squeeze fuel, raises gap risk [C]/[S]; % above SMA200 = breadth [C]. Never time a single stock with them.

## 12. Misuse checklist (fix or reject the read)

- "Overbought" used against a stock at a 52-week high in a rising trend; same-group indicators (or trend + 12-1 + RS) counted as separate votes; divergence alone drives the verdict.
- Value before warm-up or on a partial bar; tool value without parameters, or with rows after `as_of` in a backtest; parameters changed from section 4 without reason.
- Stop/target on an indicator line without structure; stop tightened to fit `max_loss`; entry without its exit and clocks; an indicator used to extend a time stop.
- Earnings-gap distortion or event-day volume not flagged; a practitioner statistic (Connors, Crabel, Turtles) quoted for different rules; a cross-sectional effect presented as a forecast for this stock.

## 13. Read procedure and reporting

1. **Data gate**: enough bars for warm-up; last bar complete; split check; liquidity; earnings date known. Fail -> fetch more or list it in `## Data gaps`.
2. **Regime**: risk_off -> only what `01` 12.2 allows, lower confidence.
3. **Trend block** (T + Ml + RS, context chart): strong -> trend setups; transitional -> short_swing or reject; against (below falling SMA200/30-week, 12-1 < 0, RS falling) -> reject longs except a confirmed bottom attempt.
4. **Trend strength** (Ts): high -> breakout/MA-pullback tactics; low -> buy support with nearer targets, or wait.
5. **Volatility**: ATR% -> max stop multiple; structural stop fails `max_loss` -> reject. Contraction present -> breakout candidate.
6. **Volume**: distribution (U/D < 0.8, heavy down days) -> downgrade or reject.
7. **Timing** (one M) picks the bar only; it never overrides 2-6, except that extension means wait for a pullback.
8. **Plan fields** per 10.3; target from structure (`03`, `07`); reward:risk below the profile minimum -> reject.

Report one line each: `name(params, TF, smoothing): value on date [hook | tool | computed from raw/NNN, N bars] -> reading [label]`, e.g. `RSI(14, D, Wilder): 46.8 on 2026-09-25 [computed from raw/002, 250 bars] -> uptrend pullback zone [C]` (hypothetical).

## Sources

- Brock, Lakonishok & LeBaron (1992), J. Finance 47: https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1992.tb04681.x
- Sullivan, Timmermann & White (1999), J. Finance 54(5): https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00163
- Bajgrowicz & Scaillet (2012), J. Financial Economics 106(3).
- McLean & Pontiff (2016), J. Finance 71(1).
- Park & Irwin (2007), J. Economic Surveys 21(4): https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-6419.2007.00519.x
- Jegadeesh & Titman (1993), J. Finance 48(1): https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1993.tb04702.x
- Moskowitz, Ooi & Pedersen (2012), JFE 104(2): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463
- Hurst, Ooi & Pedersen (2017), J. Portfolio Management 44(1): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2993026
- Lim, Wang & Yao (2018), J. Banking & Finance 97.
- George & Hwang (2004), J. Finance 59(5): https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00695.x
- Han, Yang & Zhou (2013), JFQA 48(5): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1656460
- Zakamulin (2017), Market Timing with Moving Averages (Palgrave): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2585056
- Marshall, Nguyen & Visaltanachoti (2017), Quantitative Finance 17(3): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2225551
- Avramov, Kaplanski & Subrahmanyam (2021), Review of Financial Economics 39(2): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111334
- Da, Gurun & Warachka (2014), Review of Financial Studies 27(7): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1777988
- Jegadeesh (1990), J. Finance 45(3); Lehmann (1990), QJE 105(1): https://alphaarchitect.com/quantitative-momentum-research-short-term-return-reversal/
- Avramov, Chordia & Goyal (2006), J. Finance 61(5).
- Gervais, Kaniel & Mingelgrin (2001), J. Finance 56(3): https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00349
- Lee & Swaminathan (2000), J. Finance 55(5): https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00280
- Daniel & Moskowitz (2016), JFE 122(2): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2371227
- Barroso & Santa-Clara (2015), JFE 116(1): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2041429
- Lo, Mamaysky & Wang (2000), J. Finance 55(4): https://www.nber.org/papers/w7613
- Engle (1982), Econometrica 50(4); Bollerslev (1986), J. Econometrics 31.
- Faber (2007), J. Wealth Management 9(4): https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf
- MACD/RSI index tests: https://mpra.ub.uni-muenchen.de/54149/1/MPRA_paper_54149.pdf
- Connors & Alvarez (2008), Short Term Trading Strategies That Work; Connors & Raschke (1995), Street Smarts; Crabel (1990); Bollinger (2001), Bollinger on Bollinger Bands; Keltner (1960); LeBeau (chandelier); Wilder (1978); Blau (TSI); Elder (force index); Kaufman (ER); Shannon (anchored VWAP).
- StockCharts ChartSchool pages for the formulas and defaults above (RSI(2), NR7, Bollinger squeeze, Keltner, chandelier exit, ADX, TSI, force index, KAMA/ER, anchored VWAP), e.g. https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit and https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2
- Supertrend: https://www.luxalgo.com/blog/how-to-use-the-supertrend-indicator-effectively/
- Clenow (2015), Stocks on the Move: https://teddykoker.com/2019/05/momentum-strategy-from-stocks-on-the-move-in-python/
- Mansfield RS / Weinstein (1988): https://www.chartmill.com/documentation/technical-analysis/indicators/35-Mansfield-Relative-Strength
- IBD RS replication: https://github.com/skyte/relative-strength
- Minervini (2013) trend template: https://www.chartmill.com/documentation/stock-screener/technical-analysis-trading-strategies/496-Mark-Minervini-Trend-Template-A-Step-by-Step-Guide-for-Beginners
- Morales & Kacher (2010), Trade Like an O'Neil Disciple (pocket pivots).
- Faith (2007), Way of the Turtle; Brown (1999), Technical Analysis for the Trading Professional; O'Neil, How to Make Money in Stocks; Kaufman, Trading Systems and Methods.
