# Technical analysis cheat sheet

## How to use this file

- Read every run; depth in the cited section (`06` 8.3 = `06-entries.md` 8.3). Numbers = `CONVENTIONS.md`, [C] house defaults unless labelled. role.md wins; never move a level to pass a rule: reject.
- [A] academic, [P] practitioner study, [C] convention, [S] speculative; no [C]/[S] item alone decides. Defaults assume L = max loss 8%, m = min R:R 2.0: use the brief's profile.
- ATR = daily ATR14, wATR = weekly; P pivot; b = 0.1 ATR (weekly 0.1 wATR); R = e - s; HL higher low; d = (close - MA)/ATR; RVOL = V/mean(prior 50) (short_swing 20; weekly 10 wk); CLV = ((C-L)-(H-C))/(H-L); RC = close > prior high, CLV > 0.5; E = expected bars to T1.

## 1. Procedure (one line each, in order; `01` 3, 15)

1. Regime: SPY/QQQ vs SMA200, SMA50, 10-month SMA; sector ETFs over SMA200; distribution days. risk_off: short_swing/swing grade A only; long_swing/investment only stage 1->2 with RS at new highs [C; momentum's regime dependence A].
2. Sector ETF vs SPY. 3. Context stage (30-week SMA): 3/4 = no longs.
4. Structure: hook pivots (last 5 bars unconfirmed), drop swings < 1.5 ATR; levels = zones +/- 0.25-0.5 ATR; stops/targets on major/intermediate levels (`01` 6.3).
5. Volume: breakout RVOL; U/D 50d > 1.2 good, < 0.8 bad; dry-up < 0.7. 6. Extension d; ATR%; max stop = L/ATR% ATRs; non-earnings gaps.
7. RS vs SPY and sector ETF; RS high before price [C]; 3-12 m momentum [A].
8. Next report vs max hold; setup ID, state (forming/complete/triggered/extended/failed); alignment (`01` 13).

Knockouts: stage 3/4; stop > `max_loss`; major resistance < 2R, no clean break; 20-day $vol < $5M (short_swing/swing); bad data (split?). Quality (`01` 16): 12 criteria 0/1/2; 19+ A, 14-18 B, 9-13 C, <= 8 reject; 0 on regime, stage, momentum or RS caps at C. Mid-week: last weekly bar provisional.

## 2. Trade types (`05` 14, `08` 4)

|Item|short_swing|swing|long_swing|investment|
|---|---|---|---|---|
|Hold / max hold (renewals)|3-15 sessions / 15 bars (1)|2-8 wk / 40 bars (1)|2-6 mo / 26 wk (1)|6 mo+ / 52 wk per plan (unlimited)|
|Charts primary / context|D 6 mo / W 1 yr|D 1 yr / W 2 yr|W 2 yr + D / W-M 5 yr|W 5 yr / M 10 yr|
|`horizon`, `chart_timeframe`, earnings window|swing, 1d, 45 d|swing, 1d, 45 d|swing if max hold <= ~13 wk else long_term; 1w; 45/30 d|long_term, 1w, 30 d|
|Trigger; breakout RVOL|D close > P + b; >= 1.5|same; >= 1.4|W close > P + b; week >= 1.2|same, or OBV 26-wk high|
|Max extension at entry|d <= 3 vs EMA21|d <= 5 vs SMA50|d <= 3 wATR vs 10-wk|<= 40% over 40-wk|
|Stop buffer / width / min|0.25-0.5 / 1.5-2.5 / 0.75 ATR|0.5-1 / 2-3.5 / 1 ATR|0.25-0.5 / 1-2 wATR + D hard stop|0.5 / 1.5-3 wATR + hard stop|
|T1 distance (k <= 1.5 cap); R:R; max stop for 2R|3-3.7 ATR; 2-2.5; 1.8 ATR|4-6.0 ATR; 2-3; 3.0 ATR|2-4.8 wATR; 2-4; 2.4 wATR|3-6.8 wATR; 2-4; 3.4 wATR|
|Entry validity (T4) / watch expiry|5 (3) / 10 sessions|10 (5) / 20|20 (10) / 8 wk|40 (20) / 13 wk|
|CP1 MFE >= +0.5R: fail action|bar 5: exit|bar 10: halve, stop to last HL|wk 6: halve, tighten|wk 13: reduce|
|CP2: +1R close or new high, else breakeven/exit|bar 10|bar 20|wk 13|wk 26|
|Tranches / max adds|1 / 0|1-2 / 1|2-3 / 2|2-4 / 3|
|Scale-out (trend)|all at T1, or 1/2 + tight trail|1/2 T1, rest T2 or trail|1/3 T1, 1/3 T2, 1/3 trail|1/4-1/3 T1, rest trail|
|Trail|2-bar pivot - 0.25 ATR or EMA10 close|EMA21 close, 5-bar pivot - 0.5 ATR, or HH22 - 3 x ATR22|W close < 10-wk; HH10W - 2.5-3 wATR|W close < 30/40-wk; HH26W - 3 wATR|
|Trail starts|T1 or +1.5R|T1 or first HL above e|first weekly HL above e|same|
|Earnings (`09` 4)|none in hold + 2 sessions: shorten max hold or reject|no entry last 10 sessions; cushion rule at last close before|pilot <= 1/3 before, add after; name each|first tranche ok; next after; no add last ~10 sessions|
|Setups (`04` 5.2)|S1 S2 S9 S10 S11 S13 S14 S15|S1 S2 S3 S5 S7 S9 S12 S13|S3-S7, S12|S4 S5 S6|

Choose (`05` 11): allowed horizon -> structure duration nominates the type -> context passes -> stop fits (else SHORTER type, nearer structure) -> T1 >= 2R and k = (T1 - e)/(0.63 x ATR x sqrt(max-hold bars)) <= 1.5 (else LONGER) -> events -> tie: longer. Weekly types: wATR and weeks in k.

## 3. Patterns (`03`; target 0.5-0.75 x measured move MM: full MM hit ~half the time [P, Bulkowski as summarised])

|Pattern|Criteria|Entry|Stop|Target|Invalid|Ev; tier|
|---|---|---|---|---|---|---|
|Breakout|>= 2 equal highs, >= 4 wk D/7 wk W, <= 35% deep, stage 2|close > R + b, RVOL, CLV >= 0|base HL - 0.25-0.5 ATR|base height, to resistance|close < R - 0.5 ATR in 5 bars|A weak, P; common|
|Pullback / retest|2-8 bars to rising MA, <= 3 ATR, light volume; retest P +/- 0.5 ATR in bars 2-21|RC; limit at grade-A zone|low - 0.25 ATR; retest min(low, P - 1 ATR)|prior high|1 ATR under MA / < P - 0.5 ATR|A ind., C, P; best entry|
|Bull flag / pennant|pole >= 4 ATR, >= 10%, <= 15 bars; flag 5-15 bars, <= 50% retrace; pennant converging <= 3 wk|close > high + b|flag low - 0.25 ATR|0.5 x pole (pennant less)|> 50%, > 3 wk|P; common|
|Asc. triangle|flat top, >= 2 rising lows, >= 3 wk, >= 3 ATR|close > top + b|last HL - 0.25 ATR|0.5-0.75 x height|< last low|P; common|
|Flat base|>= 5 wk, <= ~15%, tight weekly closes|close > high + b|base low if <= ~7%, else weekly low|haircut MM|< base low|C, P; best fit|
|Cup w/ handle|+30% prior; cup 7-65 wk, 12-33%, U; handle 1-4 wk, upper half, <= 10-12%|close > handle + b|handle low - 0.25 ATR|depth, haircut|handle in lower half|C, P; common|
|VCP|2-6 contractions each <= 0.7 x prior; last <= 10%, <= 3 ATR, VDU < 0.6|close > last high + b|last contraction low|resistance, trail|deeper contraction|C; best fit|
|Double bottom|lows within max(1 ATR, 3%), >= 4 wk apart; peak >= 10% or 3 ATR|close > peak + b|2nd low - 0.25 ATR|height|< 2nd low|A, P; best reversal|
|Inv. H&S / H&S top|head below / above ~equal shoulders|close > neckline + b / exit on neckline close|right shoulder - 0.25 ATR|0.5-0.75 x height|< right shoulder|A, P; top = exit cue|
|Breakaway gap|full gap >= 1 ATR from base, RVOL >= 2, upper-half close, d50 <= 5|close > gap-day high, or hold + RC|gap-day low - 0.25-0.5 ATR|resistance|gap filled|A earnings, P; common|
|Spring / failed breakdown|undercut <= 1 ATR, back in 1-3 bars, weekly up|reclaim close (T9) or test + RC|spring low - 0.25-0.5 ATR|range top|< spring low|C, P; underrated|

At 0.75 x MM, 2R needs R <= ~0.375 x MM; throwback holding closes >= P - 0.5 ATR = hold. Also: HTF (+90% in <= 8 wk, 3-5 wk flag 10-25%; its low usually > 8% away) [P, C]; 3WT (3 weekly closes within 1-1.5%: entry/add), ascending base, rising channel [C]; rectangle, sym. triangle (break with trend only) [A, P]; falling wedge (close > upper line and last LH, stop wedge low) [C, P]; pocket pivot, NR7/inside bar = triggers, cancel after 3-5 bars [C]; triple bottom (0.5 x height) [P]; rounding bottom (weekly) [C, P]. Double top, H&S top, bear flag, rising wedge, island top, broadening = exit cues [P; A for H&S, double top]; descending triangle: bust only; 1-2-3 step 1 [C] and a lone key reversal [S] are not buys.

## 4. Setups (`04`; one per plan, name its ID; trade_types: section 2 last row)

|ID|Setup|Trigger|Stop|T1|Clock|
|---|---|---|---|---|---|
|S1|pullback to rising MA|RC after touch|low - 0.5 (swing 0.5-1) ATR|swing high|RC in 3-5 bars|
|S2|breakout retest|RC at P, bars 2-21|min(low, P - 1 ATR)|post-breakout high|reclaim in 15 bars|
|S3|base breakout|close > P + b|handle/contraction low|0.5-0.75 x depth|+1R by bar 10 / 3 wk|
|S4|momentum/RS leader|filter; weekly 10-wk reclaim|weekly low - 0.5 wATR|entry setup's|RS 26-wk low: no adds|
|S5|52-week high|close > 52-wk closing high + b|consolidation low - 0.5 ATR|MM, k <= 1.5|below old high 10 bars = failed|
|S6|stage-2 breakout|W close > base, over 30-wk, vol >= 2x|week low - 0.5 wATR + hard stop|weekly resistance|new weekly high in 6 wk|
|S7|Donchian 20/55 D, 20/52 W|close > N-bar high|2N or structure|resistance/MM|opposite channel|
|S9|squeeze|close > squeeze high, RVOL >= 1.5|squeeze low|resistance|inside at bar 5: exit|
|S10|RSI(2) < 5 over SMA200|that close, no news|structure - 0.5-1 ATR|prior high|5-8 bars|
|S11|range|RC in lowest ~25-30%|zone - 0.5-1 ATR|midpoint/top|median traverse|
|S12|spring|reclaim or test + RC|spring low - 0.5 ATR|range top|SOS in ~10-15 bars|
|S13|post-earnings gap|from close R+1|gap-day low - 0.25-0.5 ATR|resistance|>= 5 sessions pre-report|
|S14|no-news gap fill|close > gap-day high|gap-day low - 0.5 ATR|prior close|5 bars|
|S15|capitulation: -25%/3 mo or -15%/1 mo, climax bar RVOL >= 2.5, range >= 2 ATR, CLV > 0|close > climax high in 1-5 bars, or test + RC|climax low - 0.5 ATR|falling EMA21|CP 5, max 10-15|

risk_off: only grade-A S1/S2/S5, S4/S6 with RS highs, S10 leaders, S11 floor, S12 if the market bases, S13; S15 half risk. Ev: S4, S5 [A]; S13 [A, weak large caps]; S7 [A old, P]; S1-S3 [C/P]; S9 [A vol, C dir]; S6, S11 [C]; S12 [C/S]; S10, S14 [P]; S15 [S]; S8 filter. S10, S11, S14, S15 exit fully at target; trend setups keep a runner.

## 5. Indicators (`02`)

- Best: price vs rising MA + slope [A index, C stock]; 12-1 momentum [A]; 52-week-high proximity [A]; RS/Mansfield [A concept, C form]; ATR% [C; clustering A]; Donchian [A old, S alone]; RVOL [A effect, C level]; chandelier [C].
- Common, misused [C]: EMA crosses; MACD(12,26,9); RSI(14) (uptrend 40-80; 70/30 [S]); Stoch(14,3,3); Bollinger(20,2); ADX(14); OBV. Candle names, Fibonacci: [S].
- Underrated: RSI(2); NR7/inside day; squeeze; Keltner(20,2,ATR10); HV ratio; SMA21/SMA200 [A, one study]; frog-in-the-pan [A]; ER(10/20); AVWAP (daily typical price); U/D volume(50); pocket pivot; CMF(20).
- Stacks by type (+ ATR, RVOL, RS): short_swing EMA10/21, SMA50, RSI(2)/Stoch, NR7; swing SMA50/200, EMA21, 12-1, RSI(14)/MACD, squeeze, OBV; long_swing 10/30/40-wk, 12-1, weekly MACD/RSI(14), OBV, Mansfield 52 W; investment 40-wk, 10-month, 12-1, weekly RSI(14) context.
- One vote per group; trend + 12-1 + RS = one block; ~4 independent votes (trend, volume, contraction, structure). Oscillators only time; divergence alone [S].

## 6. Entries (`06`)

- Triggers (IDs, not targets): T1 buy-stop P + b; T2 daily close > P + b; T3 weekly close; T4 zone limit; T5 RC after pullback; T6 retest; T7 anticipatory pilot; T8 gap; T9 reclaim. b >= 0.02 (ATR% > 4: 0.15-0.25 ATR; quiet short_swing 0.05); above round numbers.
- Confirmations: RVOL; CLV >= 0; range >= 1 ATR; prior tightness; RS at 3-month (weekly types 52-week) high; within 10% (15%) of 52-week high; sector over rising SMA50. 5+ full tranche; 3-4 pilot or wait; <= 2 none.
- Red flags: extended; RVOL >= 3 after > 25%; hype >= 2; report or binary event; past cap; resistance < e + 2R; risk_off; weak bar (wait); below falling SMA200; 4th+ base.
- Stale cap = min((T1 + m s)/(1 + m), s/(1 - L/100)), rounded down: "do not fill above X"; by type also stale past 0.5 ATR / 1.0 ATR / 0.5 wATR / 0.5 wATR + 5% over P. Open above cap or below stop: cancel; breakaway gap above cap = new S13 plan after the close. Role `stale_entry` unchanged.
- All at once: short_swing, stop < 1.5 ATR, one trigger. Pilot 1/3-1/2: grade B, T7. 2/3 + 1/3: grade A, swing+. Zone tranches, one stop: weekly types.
- Pyramid: add at close >= e + 0.5R or new trigger; add <= prior; stop raised so total risk <= initial; every fill state passes; <= 5% over P; none near reports, in risk_off, after close < P. No averaging down. Re-entry once per setup, fresh trigger, not same day.

## 7. Exits (`07`)

- Stop: structure = where, ATR = how far, cap = whether; beyond round numbers; % placement [S]. Weekly types: weekly invalidation + daily-close hard stop >= e(1 - L/100). Disclose ~0.5 ATR close overshoot and worst gap; >= 3 stop-skipping gaps in 252 bars = reject or longer type.
- Targets: graded resistance - 0.25 ATR, under round numbers; first of 2+ levels; MM base case; blue sky: MM/ATR projection, k <= 1.5. R multiples = runner checkpoints; blended R:R information only.
- At the close, first match: stop/trail/invalidation -> exit; time limit -> exit or re-underwrite; event next session -> event plan; mean reversion at target -> exit; climax or hype >= 4 -> sell 1/2-all into strength; trend at T1 -> fraction, trail rest; CP1 fail -> type action; 2 cues in 3 bars -> exit (weekly types halve); 1 cue -> tighten.
- Breakeven only to structure; after T1 partial stop = max(e, last HL - buffer). Regime after entry: neutral = larger T1 fraction; risk_off = trails one notch tighter, no adds, short_swing/swing exit at CP1 unless +0.5R.
- Cues (`07` 10): climax (largest gain and volume of the move, 7 of 8 up); exhaustion gap filled in ~5 bars; largest down day; gap through support; failed breakout (close < P - 0.5 ATR in 1-5 bars); lower low; stall at target; MA break on RVOL >= 1.5; RS breakdown; stage 3; bearish pattern completes.
- At a limit: R < 0 exit; < 1R, no fresh setup: exit; >= 1R and longer type qualifies now with its stop >= e: graduate (T1 partial, clocks restart); fresh setup: NEW plan. Never extend, widen or rescue a loser.
- Evaluate (`07` 14): R vs initial stop, MFE/MAE, give-back, capture, post-exit move, exit-reason mix, E vs actual bars.

## 8. Events, hype, fear (`09`)

- Reaction R: U1 gap up >= max(1 ATR, 0.5 HEM), CLV >= 0.5, GR >= 0.75, RVOL >= 2 = S13. U2: wait for base. U3 CLV < 0 or GR < 0.3 = sell the news: no entry, scale out. U4 new high, close < prior = exit. D1 held gap down: no longs 4-8 wk. D2/D3 washout: buy only confirmed. GR = (C_R - C_P)/(O_R - C_P); HEM = median abs move, last 4-8 reports.
- PEAD [A], weak in large caps; news moves drift, no-news reverse [A]; follow the close.
- Hype score [C] (`09` 7), 1 each: climactic d; 70%+ over 200-day; parabolic; 3 gaps up in 10; 7 of 8 up; largest up day; RVOL >= 3 or churn; exhaustion gap; key reversal; RSI > 80/band walk; squeeze; supply (offering, insiders); sentiment (upstream); +1 speculative name. 2-3: no entries, tighter trail; >= 4: sell into strength (short_swing exit, swing 1/2, long_swing 1/4-1/3, investment weekly climax only).
- Fear [C] (-25%/3 mo, -15%/1 mo, climax): confirmed entries only, half risk; news-driven D1 = no long. short_swing S15; swing only stage-2 names after the market follow-through; long_swing a weekly base first; investment pilot at multi-year support after a weekly reversal.
- Run-up RU20 >= 3 ATR into an event (buy rumor, sell news): short_swing/swing exit or halve before, long_swing trim 1/4-1/3; no new long.
- Cushion (OP = open profit in R): OP >= 1R, stop raisable to >= e, HEM < stop distance -> hold; OP >= 0.5 or only HEM fails -> halve; else swing exit, long_swing halve. Release after close T: act at T's close; pre-open: T-1. Cancel resting orders the session before; unknown date = inside.

## 9. Must-haves and caveats

- Plan: trade_type and setup ID (in `## Setup`); `entry_condition` with "valid until <date>" and "do not fill above <cap>"; stop arithmetic; `target` = T1 (+T2); `invalidation` with structure line, CP1, T1 deadline = min(max hold, 2E), max hold bars and latest date; scale-out, trail, report actions, worst gap. No expiry, time stop or max-hold date = reject. Stops only rise; losers never renewed.
- Time (`08` 5-7): E = M3 (d/ATR / median ATR-per-bar of the last 2-4 legs), else M4 (pattern duration), else M2 5.5 x (d/ATR)^2 halved (low confidence); floor d/ATR. CP1 = min(E/3, default) >= bar 2; CP2 = min(2E/3, default). Reject if E > 2/3 max hold or k > 1.5. `## Plan` line: "Timeline: valid until | CP1 | CP2 | decide <date> before report | T1 by bar N | max hold bar N (latest <date>)".
- No drift: P(T1 first) = 1/(1 + R:R) [math]: the edge is trend, momentum or drift, never the ratio.

## Sources

None new; see `01`-`09`.
