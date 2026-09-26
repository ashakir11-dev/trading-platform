# 03 - Chart patterns and flags

## How to use this file

- Use after the top-down read in `01-chart-reading.md` (sections 3-13): a pattern matters only inside a known trend, stage, regime and level map. Section 2 = shared rules (measure, trigger, stop, target, throwback vs failure, detection, pre-entry discipline); sections 3-5 = one card per pattern; section 6 = decision rules and per-trade_type cheat sheet; section 7 = master table.
- Labels: [A] academic/replicated, [P] practitioner statistical study, [C] convention, [S] speculative/contested. "House default" = a threshold chosen for this playbook, not a published result; say so when used.
- Tiers: `best` (strongest evidence or best fit for this profile), `common` (seen often, average edge), `underrated` (useful, less watched), `weak` (context or exit cue only).
- Card keys: **ID** identification, **Vol** volume, **E/S/T** entry / stop / target, **Inv** invalidation, **Fail** failure signs, **Ev** evidence, **Det** detection from the hook's data. Timeframe per trade_type = the family row in 2.8 unless the card says otherwise.
- Examples are hypothetical (XYZ, made-up prices). Long-only by default: bearish patterns are exit/avoid cues; shorts get mirror notes only.
- Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).

## 1. What the evidence says about patterns

| Finding | Label | Use |
|---|---|---|
| Lo, Mamaysky and Wang (2000): 10 patterns (H&S and inverse, broadening, triangle, rectangle, double tops/bottoms) found by kernel regression in US stocks 1962-1996 shifted the distribution of next-day returns (more for Nasdaq stocks). Distributions only, not profits after costs. | [A] modest | Patterns are information, not a verdict. |
| Savin, Weller and Zvingelis (2007), S&P 500 and Russell 2000 stocks 1990-1999: H&S tops predicted lower excess returns; the gain came from adjusting a market position, not stand-alone pattern trading. | [A] | Bearish patterns = exit/avoid cues. |
| Chang and Osler (1999), FX: H&S profitable for some currencies, dominated by simple MA and momentum rules. | [A] | Trend first, pattern second. |
| Leigh, Modani, Purvis and Roberts (2002): bull-flag template on the NYSE Composite index, significant in their sample. | [A] limited | Supports flag continuation; not proof for single stocks. |
| Range-break rules worked on the DJIA 1897-1986 (Brock, Lakonishok, LeBaron 1992) but not after data-snooping correction out of sample (Sullivan, Timmermann, White 1999). | [A] weakening | A breakout alone is a weak edge; add trend, RS, 52-week-high proximity. |
| Nearness to the 52-week high predicts 6-12 month returns (George and Hwang 2004). | [A] | Prefer pivots near the 52-week high. It picks the stock, not the breakout day. |
| Post-earnings-announcement drift (Ball and Brown 1968; Bernard and Thomas 1989) and drift after the announcement return (Chan, Jegadeesh, Lakonishok 1996); much weaker in large liquid stocks since the mid-2000s (Martineau 2022). | [A], smaller today | Earnings gaps in the surprise direction tend to drift (section 5). |
| Bulkowski (tens of thousands of hand-identified US-stock patterns): measured targets often reached only about half the time; throwbacks common and hurt performance. Averages run to the "ultimate high" (peak before a 20% decline), which no real exit captures; in-sample. | [P] | Base case = 0.5-0.75 of the measured move; never quote his average rise as an expected return. |
| O'Neil, Minervini, Weinstein, Wyckoff, Edwards and Magee definitions. | [C] | Precise vocabulary; untested as stated. |

Bulkowski figures are "as summarised" from thepatternsite.com (pages not opened directly in writing or review): approximate; no rule depends on the exact value. Consequence: a pattern supplies **a pivot, a structural stop and a measured target**; the odds come mostly from context (trend, stage, RS, 52-week-high proximity, regime, earnings timing, liquidity).

## 2. Rules shared by every pattern

### 2.1 Measurements (compute, show inputs)

| Quantity | Formula |
|---|---|
| Pattern high H / low L | highest high / lowest low, first to last pattern bar (`raw/` rows or weekly bars) |
| Depth % / in ATR | (H - L) / H x 100 (O'Neil/Minervini); (H - L) / ATR14, or / weekly ATR (Wilder, 14 weekly bars) |
| Duration | bars or weeks from the first bar at H (left side) to the latest bar; trade only complete patterns |
| RVOL | volume_t / mean(volume of the prior 50 sessions, excluding t); RVOL(20) for short_swing (`01-chart-reading.md` 1.3) |
| Volume dry-up (VDU) | SMA5(volume) at pattern end / SMA50(volume); house default < 0.7 = dried up |
| CLV | ((C - L) - (H - C)) / (H - L) of the bar; > 0 = upper-half close |
| Weekly tightness | (max - min weekly close) / min weekly close over n weeks; 3WT about 1-1.5% [C] |
| Pole | pole high - pole start low, in % and ATR (flags, pennants, HTF) |
| Prior advance / decline | % move from the prior ~6-12 month extreme to H (or L) |
| Stop position | (P - stop) / (H - L); < 0.35 = stop in the upper third (tight, preferred) |

### 2.2 Prior-trend and context requirements

- Continuation: O'Neil wants about 30%+ before a cup [C]; house default for any base: prior advance >= 25% or >= 8 ATR, above a rising SMA200 / 40-week SMA (stage 2, `01-chart-reading.md` 5.1).
- Reversal: needs a trend to reverse [C, Edwards and Magee]; house default prior decline (advance for tops) >= 15% or >= 5 ATR.
- Base count [C, O'Neil/Minervini]: 1st-2nd bases after a stage 1-to-2 transition are most reliable; 3rd+ are late stage and fail more. A new base counts after a breakout that rose >= 20%; undercutting the prior base's low resets the count; base-on-base (new base just above the last, before a 20% move) is one stage, a sign of strength.
- Regime: breakouts fail more in `risk_off` [A for momentum-state dependence, C for patterns]; apply `01-chart-reading.md` 12.2.
- Liquidity: levels are unreliable below $5M 20-day average dollar volume (`01-chart-reading.md` 7.3 [C]): reject short_swing/swing, flag others.
- Earnings inside the hold: a gap can jump the stop [C]; apply `09-events-hype-and-fear.md` 4.1.

### 2.3 Breakout confirmation (the trigger)

| Item | Rule |
|---|---|
| Pivot P | the level whose break completes the pattern: flat top, handle high, final-contraction high, neckline, trendline value on the trigger day |
| Buffer | house default P + 0.1 x ATR14 (O'Neil: P + 0.10 dollars [C]) |
| `level_trigger: close` | valid = daily close > P + buffer. Weekly-primary types: a weekly close above P + 0.1 x weekly ATR14 confirms; a daily close may time it if the week has not closed back below P. The human fills at that close or the next open (gap risk, `06-entries.md` 7). |
| `level_trigger: intraday` | "buy-stop at P + buffer" as a stop-limit, limit = the stale cap (`06-entries.md` 8.3). A close back below P that day = failed breakout (4.15). |
| Volume | RVOL >= 1.4 (short_swing 1.5) by convention (O'Neil: 40-50% above average) [C]. Bulkowski: above-average breakout volume went with larger average moves for many, not all, patterns, and with more throwbacks [P, as summarised]. Low volume = warning, not veto. |
| Close quality | CLV > 0 [C]; >= 0.5 strong (`01-chart-reading.md` 6.5) |
| Chase limit | `stale_entry` rejects > 3% above `entry` (O'Neil: 5% [C]); also the re-price test (`06-entries.md` 8.3). Missed it: retest (3.2) or next base. |
| Daily bars hide intraday order | if one bar spans both trigger and stop, assume the stop was hit |

### 2.4 Stops

- Preference: (1) below the final contraction / handle / flag / tight-area low; (2) below the breakout-bar low (short_swing); (3) below the pattern low only if within the loss limit. Buffer 0.25-0.5 x ATR14 (house default; 0.5 in $5-20M dollar-volume names).
- Weekly-primary types: below a weekly structure (last weekly higher low, 10- or 30-week SMA) with a weekly-ATR buffer, plus a daily-close hard stop inside `max_loss` (`05-timeframes-and-trade-types.md` 7.2).
- `max_loss` 8%: deep patterns (cup 30%, HTF 25%) cannot use the pattern low; use a real inner structure or **reject**. Never move a stop to fit the rule (role.md). Gaps skip stops (`07-exits.md` 4); trailing and scaling: `07-exits.md`.

### 2.5 Targets (measured move) and their realism

- Measured move MM = pattern height (or pole) projected from the breakout level (flags: from the flag low) [C].
- Bulkowski: full targets reached about half the time for several patterns: 51% H&S tops; 49% triple tops, 72% with half the height; some do better (Adam & Adam double bottoms 73%) [P, as summarised].
- Base-case target = min(P + 0.5-0.75 x MM, next major resistance - 0.25 ATR); full MM = stretch. No overhead supply (new high): haircut MM or ATR projection (`07-exits.md` 5).
- Never target a multiple of risk ("2 x risk" passes `reward_to_risk` by construction); the check runs on the base case.
- **Feasibility pre-check [math]:** with entry e = P + buffer, target P + k x MM and risk r = e - s, R:R >= 2.0 only if r <= (k x MM - buffer) / 2; with k = 0.75, roughly r <= 0.375 x MM. A stop at the pattern low (r ~ pattern height) cannot pass on its own MM: use an inner stop or a farther resistance target, else reject. Run this before drafting.
- Time: allow roughly the pattern's own duration for the move [C]; if the base case cannot be reached inside the type's max hold (`08-trade-plan-and-timeline.md` 5), use a longer type or a nearer target.

### 2.6 Throwbacks, pullbacks and busts [P]

- Throwback = after an upward breakout, a return to (near) the breakout level within 30 calendar days (Bulkowski, about 21 bars); pullback = the mirror. Common: secondary summaries of Bulkowski range from roughly a third of upward breakouts (his multi-pattern throwback study, as quoted in `04` S2) to half or more for some patterns; not re-verified, so no rule uses a figure [P, as summarised]. Patterns without one perform better on average; throwbacks holding above the breakout price beat those dropping below it [P]. A retest entry buys a better price and stop but on average selects weaker breakouts.
- Bust = move < 10% after the breakout, then a close beyond the opposite side of the pattern [P, Bulkowski]; busts can run hard the other way (4.15, 4.16).

Throwback or failure? (house rules [C], as `01-chart-reading.md` 6.5)

| After a valid breakout | Read | Long action |
|---|---|---|
| back within 0.5 ATR of P on RVOL < 1; closes hold >= P - 0.5 ATR | throwback | hold; retest entry (3.2) |
| close < P - 0.5 ATR within 1-5 bars, or below the handle/final-contraction low | failed (4.15) | exit; no re-entry until new base or reclaim |
| close below P on RVOL above the breakout day's | distribution | exit or halve now |
| MFE < +0.5R by CP1, or (swing) no close >= P + 1R within 10 bars (`08-trade-plan-and-timeline.md` 4, 4.1) | stall | time stop (`08-trade-plan-and-timeline.md` 6) |

### 2.7 Detecting patterns from the hook's data

1. Hook pivots are daily 5-bar swings (11-bar window), last 6 each; the last 5 bars can never be pivots: read the last 10 `raw/` rows and label a recent swing "unconfirmed".
2. Merge pivots whose swing is < 1.5 x ATR14 (< 1 weekly ATR on weekly) (`01-chart-reading.md` 4.2).
3. Weekly pivots: compute with 2 or 3 bars each side (say which). Mid-week `as_of` = last weekly bar incomplete.
4. "Equal" pivots: within max(1 x ATR14, 1.5%) (house default; LMW used 1.5% of the extrema's average [A]).
5. Five alternating pivots E1..E5 = the LMW template (H&S top: E1 max, E3 > E1 and E3 > E5, E1/E5 and E2/E4 each within 1.5% of their average). LMW used 38-day rolling windows (35 + 3) on a kernel-smoothed curve [A]: a detection window, not a minimum duration; tolerances transfer only approximately. Longer patterns need weekly pivots; more than 6 pivots: recompute from `raw/`.
6. Screens: 3m return > +90% -> check HTF; within 5% of the 52-week high with SMA20 near price -> check flat base / VCP / 3WT; weekly bars give 3WT directly.
7. Every pattern claim lists its defining pivots or bars (dates, prices).

### 2.8 Timeframe validity per trade_type

| Family | short_swing (daily ~6 mo) | swing (daily ~1 yr) | long_swing (weekly ~2 yr) | investment (weekly ~5 yr) |
|---|---|---|---|---|
| Flags, pennants, pocket pivot, NR7/inside bar, gap-and-go, key reversal, failed breakdown | primary (5-15 bars) | primary / trigger | trigger inside a weekly setup | fine-entry trigger only |
| Pullback/retest reference | EMA21/SMA20, breakout level | SMA50, breakout level | 10-week SMA, weekly breakout level | 30/40-week SMA |
| Triangles, rectangles, channels | daily >= 3 weeks | daily >= 4 weeks | weekly >= 8 weeks | weekly >= 13 weeks |
| Bases (flat, cup, VCP, ascending, 3WT, HTF) | final tight area / breakout day only | daily + weekly, 5-26 weeks | weekly, 7-65 weeks | weekly 7-65+ weeks; monthly for multi-year |
| Reversals (double/triple, H&S, rounding, wedges, 1-2-3) | no; failed breakdown/spring only | daily >= 4-6 weeks | weekly >= 3 months | weekly/monthly >= 6 months |
| Climaxes | daily cues | daily + weekly | weekly | weekly/monthly |
| Gaps | daily | daily | daily trigger | context only |

Rule [C]: the higher-timeframe pattern outranks a conflicting lower one; lower-timeframe patterns are triggers inside it. A daily break of a weekly level is unconfirmed until the weekly close.

### 2.9 Before entry: state, expiry, time limit, execution

| State on `as_of` | Test | Plan |
|---|---|---|
| Forming | definition not yet met | no plan; watch note naming what must happen |
| Complete, not triggered | definition met, close <= P | conditional plan: trigger per 2.3, `valid_until` per `06-entries.md` 9; cancel on a close below stop/invalidation, a new pivot above P, earnings entering the no-entry window, or a regime drop |
| Triggered, within cap | close > P + buffer, price <= stale cap | plan at the trigger; re-price test |
| Extended | past the cap or `01-chart-reading.md` 9.2 "extended" | reject now; conditional retest/MA-pullback plan (3.2) or wait for the next base |
| Failed / busted | 2.6 failure rule hit | no long until a new base or reclaim; if a breakdown failed, check 4.16 |

Time budget ([C] house defaults owned by `08-trade-plan-and-timeline.md` 4, summary in `CONVENTIONS.md`; no open-ended trades): entry validity 5 / 10 / 20 / 40 sessions; progress check (MFE >= +0.5R) by bar 5 / bar 10 / week 6 / week 13; max hold 15 bars / 40 bars / 26 weeks / 52 weeks per plan (short_swing / swing / long_swing / investment). Earnings: `09-events-hype-and-fear.md` 4.1.

Execution [C]: a buy-stop fills at the open when price gaps over it (hence the stop-limit); a close trigger acted on next morning carries overnight gap risk; thin names slip more. Write stop, target, invalidation and time stop before entry (`07-exits.md` 2).

## 3. Continuation patterns

### 3.1 Breakout from resistance or base [common; best at a 52-week high]
- **ID:** resistance R = >= 2 equal swing highs (2.7) spanning >= 4 weeks daily / >= 7 weeks weekly; stage 2 or completing a stage-1 base; base depth <= 35% and <= 12 ATR (house default; deeper is a recovery, not a base); close within 1 ATR below R. **Vol:** VDU into R, RVOL >= 1.4 on the break.
- **E/S/T:** close > R + 0.1 ATR / last higher low in the base (short_swing: breakout-bar low) - 0.25-0.5 ATR / base height from R, capped at the next resistance.
- **Inv:** close < R - 0.5 ATR within 5 bars (4.15). **Fail:** breakout CLV < 0; RVOL < 1; gap > 3% above R (stale); late-stage base; lagging its sector; `risk_off`.
- **Ev:** [A] range-break rules (weakening), 52-week-high effect; [P] Bulkowski throwbacks/busts. **Det:** pair swing highs within tolerance, confirm on weekly highs, count weeks since the first touch.

### 3.2 Pullback and retest [best entry for price and stop; not a higher-probability subset]
- **ID, retest:** after a valid breakout, back to within 0.5 ATR of R within ~30 calendar days [P] on RVOL < 1, no close below R - 0.5 ATR. **ID, MA pullback:** close above a rising reference MA (2.8) with higher highs/lows; 2-8 bars down to it (low within 0.5 ATR) on lower volume; depth <= 3 ATR daily or <= 1.5 weekly ATR (house default; deeper = re-read structure).
- **E/S/T:** after the touch, close above the prior bar's high (preferred with `close`), or a limit in the zone / pullback low - 0.25 ATR, or R - 1 ATR for a retest / prior swing high, then the original MM.
- **Inv:** close > 1 ATR below the MA, or a low below the prior swing low. **Fail:** pullback on rising volume; 3rd+ MA touch [C]; MA flattening; pullback caused by bad news (news-driven drops drift, Chan 2003 [A]).
- **Ev:** [P] throwbacks common; holding above the breakout price does better, yet retested breakouts do worse than never-retested ones (2.6). [A, indirect] one-month reversal (Jegadeesh 1990) plus momentum fits buying short no-news dips in uptrends; the reversal effect sits in less liquid stocks and is largely eaten by costs (`02-indicators.md`). MA levels [C].
- **Det:** last swing low vs the MA on that date (the hook gives SMAs for the last bar only; compute history from rows).

### 3.3 Bull flag [common]
- **ID:** pole >= 4 ATR and >= 10% (house default) in <= 15 daily bars on rising volume; flag 5-15 bars (Bulkowski: a few days to 3 weeks; longer = rectangle/channel [P]) drifting down or sideways between near-parallel lines, retracing <= 50% of the pole (ideal <= 38%) [C]. **Vol:** flag average < pole average; VDU at the end.
- **E/S/T:** close above the upper line or the last 3 bars' high + 0.1 ATR / flag low - 0.25 ATR / pole from the flag low; base case 0.5 x pole (Bulkowski's measure-rule summaries: the full pole is often not reached for stock flags [P, qualitative, not re-verified]).
- **Inv:** retrace > 50%, > 3 weeks, or close below the flag low. **Fail:** heavy down-bar volume; up-sloping flag; pole was an earnings gap into resistance. Weekly flag (2-6 weekly bars after a multi-week pole) serves long_swing.
- **Ev:** [P] Bulkowski; [A] limited (Leigh et al. 2002, index). **Det:** pole = last swing low to swing high; flag = bars after that high (confirmed or read from rows).

### 3.4 Bear flag [common; exit/avoid cue]
- **ID:** mirror of 3.3 after a >= 4 ATR drop in <= 15 bars: 5-15 bars of light-volume drift up, retracing <= 50%.
- **Use:** never buy the drift; holders: close below the flag low = sell/tighten (`07-exits.md`). Short mirror: sell-stop below the flag low, stop above its high.
- **Ev:** [P] Bulkowski (often short of the full pole; secondary reports, not re-verified). **Det:** swing high to swing low, then small rising pivots.

### 3.5 Pennant [common, lower quality than flags]
- **ID:** as 3.3 with converging lines, <= 3 weeks (longer = triangle, 3.9).
- **E/S/T:** as 3.3; base case below 0.5 x pole (secondary reports of Bulkowski put full-target attainment well below half [P, qualitative, not re-verified]).
- **Inv:** close below the pennant low. **Fail:** breakout near the apex [C]. **Det:** after the pole, falling swing highs and rising lows within 3 weeks.

### 3.6 High tight flag (HTF; Minervini's "power play" is similar) [best but rare; often fails the loss limit]
- **ID:** rise >= 90% (Bulkowski) or 100-120% (O'Neil/IBD) in <= 8 weeks, then 3-5 weeks (IBD) declining 10-25% [C]; Bulkowski's typical flag decline in the low 20s percent [P, as summarised]. **Vol:** very heavy pole, drying flag.
- **E/S/T:** close above the flag high + buffer; wait for it, many HTFs break down [P, qualitative] / flag low is usually 20-25% away (fails 8%): use a tight final 1-2 weeks inside the flag if real, else reject / next resistance or 0.5 x pole. Bulkowski's newer study (over 2,500 examples): about 27% average post-breakout gain vs 69% in his earlier, smaller sample, and 48% failed to rise 10% [P, as summarised; to ultimate high].
- **Inv:** decline > 25% or flag > 5-6 weeks. **Fail:** pole was one event gap without follow-through; extreme ATR% (`01-chart-reading.md` 10.2).
- **Ev:** [C] O'Neil's "rarest, most powerful base"; [P] huge variance, modest typical outcome. **Det:** 3m > +90% screen; date pole and flag from weekly bars and rows.

### 3.7 Ascending triangle [common]
- **ID:** flat top (>= 2 equal highs), >= 2 rising lows, >= 3 weeks daily (>= 8 weekly), height >= 3 ATR, prior uptrend. **Vol:** contracting into the apex.
- **E/S/T:** close above the top + buffer / last higher low - 0.25 ATR / widest height added to the top, base case 0.5-0.75 x.
- **Inv:** close below the last rising low. **Fail:** repeated failed closes above the top (`01-chart-reading.md` 6.5); apex breakout.
- **Ev:** Bulkowski: upward breakouts about 64%; failure much lower up than down (reported 17% vs 38% break-even failure) [P, as summarised]; the visible top invites throwbacks. **Det:** swing highs flat, swing lows each higher.

### 3.8 Descending triangle [weak for longs]
- **ID:** flat bottom (>= 2 equal lows), >= 2 lower highs; bearish bias in a downtrend [C].
- **Use:** holders exit on a close below the bottom. Longs avoid; a close above the falling line and then above the last lower high = bust (entry there, stop below the last low). Bulkowski: busted descending triangles averaged about a 40% rise to the ultimate high [P, as summarised; not an expected return]. **Det:** swing lows flat, highs each lower.

### 3.9 Symmetrical triangle [common, weak edge]
- **ID:** >= 2 lower highs and >= 2 higher lows converging, >= 3 weeks; breakouts usually two-thirds to three-quarters of the way to the apex [C, Edwards and Magee].
- **E/S/T:** direction unpredictable: only a close outside the line with volume, prior trend as tie-breaker [C] / other side of the last inside swing / widest height from the break.
- **Inv:** close back inside. **Ev:** Bulkowski: downward breakouts bust often in bull markets (reported 48%); repeated two-way breaks [P, as summarised]; LMW triangles informative [A, modest]. **Det:** LMW E1 > E3 > E5, E2 < E4 [A].

### 3.10 Rectangle / trading range [common]
- **ID:** >= 2 equal highs and >= 2 equal lows (LMW 0.75% [A]; house 2.7 rule 4), height >= 3 ATR, >= 3 weeks daily or >= 8 weekly.
- **E/S/T:** close above the top in an uptrend context (range-buying near the bottom on a reversal bar: short_swing in an uptrend only) / midpoint or bottom, whichever is structural within 8% / height from the break (range trade: the top).
- **Inv:** close below the range low (then check 4.16). **Fail:** lower highs inside the range (distribution).
- **Ev:** [A] LMW; [P] Bulkowski (longer rectangles/flat bases did better). **Det:** 2+ swing highs and 2+ swing lows each within tolerance.

### 3.11 Flat base [best fit for this profile]
- **ID:** O'Neil: >= 5 weeks sideways, correction <= about 10-15% [C]; often after a prior breakout of >= 20%. **Vol:** quiet; weekly closes tight near the top.
- **E/S/T:** close above the base high + buffer / base low (fits 8% when depth <= ~7%), else last weekly low inside / small MM: with resistance overhead use 2.5; at a new high an ATR projection or trailing plan, but `reward_to_risk` still needs a structural base case. Bulkowski: longer flat bases (> ~65 days) did better [P, as summarised].
- **Inv:** close below the base low. **Fail:** weekly closes in the lower half; RS line falling.
- **Why best fit:** a structural stop within 8% in a strong second-stage trend. **Det:** 5+ weekly bars with max high / min low <= 1.15, closes in the upper half.

### 3.12 Cup with handle [common; reputation exceeds evidence]
- **ID (O'Neil [C]):** prior advance >= 30%; cup 7-65 weeks, depth 12-33% (to ~50% in severe bear markets), U not V; handle 1-4 weeks in the upper half (ideally third), drifting down, depth <= 10-12%, volume drying.
- **E/S/T:** close above the handle high + buffer / handle low - 0.25 ATR (check 8%) / cup depth from the pivot, haircut; O'Neil takes profits around 20-25% [C].
- **Inv:** handle into the lower half or below the 10-week SMA; close below the handle low. **Fail:** handle wedging up or on heavy volume; V cup; late-stage base.
- **Ev:** Bulkowski ranks it decent, not top (reported just outside his top-10 bullish list), with a sizeable minority (reported 23%) rising no more than 15% [P, as summarised]; O'Neil's case rests on past winners [C].
- **Det:** left lip = weekly swing high; cup low = weekly swing low; right lip within 5% of the left; handle = daily pivots after it.
- **Early ("cheat") entry (Minervini [C], underrated):** a tight 1-2 week pause in the cup's middle or upper third with VDU; entry above its high, stop below its low. Tighter, but under left-lip supply: base case = the left lip; check R:R on that.

### 3.13 Cup without handle [common]
- **ID/E/S/T:** cup as 3.12, no handle; close above left-lip high + buffer [C] / last weekly low or daily higher low near the lip / cup depth, haircut.
- **Fail:** buying straight into left-lip supply; prefer waiting for a handle or a 3WT at the lip. **Det:** as 3.12.

### 3.14 Volatility contraction pattern (VCP) [best fit for this profile; evidence C]
- **ID (Minervini [C]):** stage 2 (trend template, `01-chart-reading.md` 5.1); 2-6 pullbacks, each shallower (e.g. 20%, 10%, 5%); base 3-65 weeks. House defaults: each depth <= 0.7 x the previous; final <= 10% and <= 3 ATR; final VDU < 0.6. **Vol:** the last contraction holds the base's lowest volume.
- **E/S/T:** close above the final contraction high + buffer, RVOL >= 1.4 / final contraction low (often 3-8%) / prior high or resistance, then trail; no standard MM.
- **Inv:** close below the final contraction low; a new contraction deeper than the last. **Fail:** volume rising on down days.
- **Ev:** [C] untested. Volatility is persistent but mean-reverting [A, GARCH-type]: a tight range tends to widen, but timing and direction are not predicted; the contraction only makes the stop tight, the bias must come from trend and RS. **Det:** depth_i = (SH_i - SL_i) / SH_i for each swing-high/next-swing-low pair decreasing, swing lows rising.

### 3.15 Three-weeks-tight (3WT) [underrated]
- **ID (IBD [C]):** three consecutive weekly closes within about 1-1.5% of each other, after a breakout or in a strong uptrend; upper-half weekly closes preferred.
- **E/S/T:** close above the 3-week high + buffer; also an add point / 3-week low - 0.25 weekly ATR / resistance or trail.
- **Inv:** weekly close below the 3-week low. **Fail:** far above the 10-week SMA (extended, `01-chart-reading.md` 9.2). **Det:** the last 3 complete hook weekly closes.

### 3.16 Ascending base [underrated]
- **ID (IBD [C]):** three pullbacks of about 10-20%, each low higher, over about 9-16 weeks, often while the market corrects (RS).
- **E/S/T:** close above the third peak + buffer / third pullback low if within 8%, else last weekly low / resistance or trail.
- **Inv:** close below the third pullback low. **Det:** three rising weekly swing highs and lows, each pullback 10-20%.

### 3.17 Channel (rising / falling) [common]
- **ID:** >= 2 touches on each of two parallel lines (slopes within 20%, house default), >= 3 weeks.
- **Rising (long):** reversal bar within 0.5 ATR of the lower line (short_swing/swing) / lower line - 0.5 ATR / upper line. A close below the lower line = trend damage (exit). **Fail:** rallies stopping short of the upper line.
- **Falling:** a close above the upper line is a first sign only; require a higher low and a close above the last lower high (4.17). **Ev:** [C]. **Det:** line through 2+ swing lows, parallel through 2+ swing highs; report slopes.

### 3.18 Gap-and-go (breakaway gap continuation) [common; best when earnings-driven]
- **ID:** full gap up (Low_t > High_{t-1}) >= 1 ATR, out of a base or through resistance, RVOL >= 2 (house default), upper-half close above the old resistance; not already > 5 ATR above SMA50 before the gap (`04-strategies-and-setups.md` S13).
- **E/S/T:** close above the gap-day high later, or a 1-3 day pullback holding above the gap-day low then a close above the prior bar's high; respect `stale_entry` / below the gap-day low / resistance or base height (earnings: section 5).
- **Inv:** gap filled (close below the prior day's high). **Fail:** gap day closes in its lower half or fills > half the gap (`06-entries.md` 7).
- **Ev:** PEAD and announcement-return drift [A], much weaker in large caps (Martineau 2022); news moves drift, no-news moves reverse (Chan 2003) [A]: prefer a catalyst; classification [P][C]. **Det:** gap test in rows; `ListFilings` 8-K 2.02 on or before the gap day.

### 3.19 Pocket pivot [underrated]
- **ID (Morales and Kacher [C]):** up day whose volume exceeds the highest down-day volume of the prior 10 sessions, inside a base or off/through the 10- or 50-day MA, uptrend, not extended.
- **E/S/T:** the pocket-pivot close (with `close`, only if the plan is written before the next session; else a close above its high) / 50-day SMA or day low - 0.25 ATR, whichever is structural within 8% / base high, then the base breakout target.
- **Inv:** close below the day's low within 3 bars. **Fail:** below a falling SMA50 or extended (`02-indicators.md` 7.15). **Ev:** [C] no independent test. **Det:** day volume vs max down-day volume in the prior 10 rows.

### 3.20 NR7 / inside bar trigger [underrated; trigger only]
- **ID:** NR7 = smallest daily (or weekly) range of the last 7; inside bar = H < H_prev and L > L_prev; both = double compression (`02-indicators.md` 7.2). Valid only inside a base or flag, or at a pullback level in an uptrend.
- **E/S/T:** close (or buy-stop) above the bar high / bar low - 0.1-0.25 ATR (very tight; still >= 0.75 ATR from entry, `07-exits.md` 3.3, else use the host pattern's stop) / the host pattern's target.
- **Inv:** close below the bar low; untriggered in 3-5 bars = cancel (house default [C]). **Fail:** compression just before earnings; illiquid names.
- **Ev:** Crabel (1990) [P for next-day breakouts in futures/indexes; multi-day use C]; direction comes from structure, not the bar [S otherwise]. **Det:** range_t vs the prior 6 ranges; weekly version from hook weekly bars.

## 4. Reversal patterns

Long-only: bullish reversals are setups; bearish ones exit/avoid cues. A bottom in stage 4 is a watch, not a buy, until a close above a flattening 30-week SMA or a higher high (`01-chart-reading.md` 5.1) [C].

### 4.1 Double bottom (W) [best reversal]
- **ID:** two lows within max(1 ATR, 3%), >= 4 weeks apart daily (LMW: > 22 trading days [A]) or >= 8 weeks weekly; middle peak >= 10% or >= 3 ATR above the lows (house default); after a decline. O'Neil variant: the second low slightly undercuts the first [C]. **Vol:** lighter on the second low; rising into the neckline.
- **E/S/T:** close above the middle peak + buffer / second low - 0.25 ATR if within 8%, else the next higher low / height above the neckline.
- **Inv:** close below the second low. **Fail:** second low on heavier volume; neckline break on RVOL < 1.
- **Ev:** Bulkowski, Adam & Adam (sharp troughs): 16% break-even failure, 39% average rise (to ultimate high), 73% reaching target; rounded (Eve) variants at least as good [P, as summarised]; LMW informative [A, modest]. **Det:** two swing lows within tolerance around a swing high.

### 4.2 Double top (M) [common; exit cue]
- Mirror of 4.1, confirmed only by a close below the middle trough (equal highs alone = a range). Holders exit/tighten on that close. **Ev:** [A] LMW; [P] Bulkowski. **Det:** two swing highs within tolerance around a swing low.

### 4.3 Triple bottom / triple top [common]
- **ID:** three lows (highs) within tolerance, each >= 3 weeks apart; confirmed by a close through the highest intervening peak (lowest trough).
- **E/S/T (bottom):** that close / last low - 0.25 ATR / half the height: Bulkowski's triple tops met the full target 49% of the time, 72% with half [P, as summarised]. In an uptrend it is a flat base or rectangle: treat it as such.

### 4.4 Head-and-shoulders top [best bearish evidence; exit cue]
- **ID:** three peaks, head highest; shoulders within ~1.5% (LMW) to 1 ATR; neckline troughs likewise; after an advance; right-shoulder volume usually lighter [C]. Confirm: close below the neckline (sloped: its value that day).
- **Use:** no new buys once the right shoulder forms a lower high; holders exit/tighten on the neckline break. Short mirror target: head-to-neckline height below it.
- **Ev:** Bulkowski (2,800+ tops): break-even failure 19%, average decline 16%, pullback to neckline 68%, full target 51% [P, as summarised]; Savin et al. (2007) and Chang and Osler (1999) [A]. Evidence is modestly lower returns, not crashes: tighten, don't panic. **Det:** LMW E1..E5, highs at E1, E3, E5.

### 4.5 Inverse head-and-shoulders [common bullish reversal]
- **ID:** mirror of 4.4 after a decline; right-shoulder low above the head low.
- **E/S/T:** close above the neckline + buffer / right-shoulder low - 0.25 ATR / height above the neckline, base case 0.5-0.75 x.
- **Inv:** close below the right-shoulder low. **Fail:** neckline break on light volume. **Ev:** [A] LMW; [P] Bulkowski. **Det:** E1..E5 with lows at E1, E3, E5.

### 4.6 Rounding bottom (saucer) [underrated for long_swing/investment]
- **ID:** gradual U-shaped decline and recovery over >= 7 weeks (weekly), no sharp low; volume often U-shaped [C].
- **E/S/T:** close above the left rim, or a handle/3WT near it / handle or last weekly higher low / depth above the rim.
- **Inv:** weekly close below the last weekly higher low. **Ev:** [C][P]. **Det:** weekly lows descending then ascending, no single low > 1.5 weekly ATR below its neighbours.

### 4.7 Rising wedge [weak; caution cue]
- **ID:** up-sloping converging lines, lower steeper, >= 2 touches each, momentum fading.
- **Use:** bearish bias [C], but Bulkowski describes frequent busts of downward breakouts and weak averages [P, qualitative; rate not re-verified]. No new longs near the apex; close below the lower line = tighten. **Det:** rising swing highs and lows, the gap narrowing.

### 4.8 Falling wedge [common]
- **ID:** down-sloping converging lines, upper steeper, shrinking volume, >= 3 weeks.
- **E/S/T:** close above the upper line and the last lower high / wedge low / wedge start, haircut. **Inv:** new low after the break. **Ev:** [C][P]. **Det:** falling swing highs and lows, the gap narrowing.

### 4.9 Broadening formation (megaphone) [weak]
- **ID:** >= 2 higher highs and >= 2 lower lows (LMW top E1 < E3 < E5, E2 > E4 [A]). **Use:** unstable; avoid new positions (stops wide by construction). **Ev:** [A] LMW informative; [P] trades poorly.

### 4.10 Island reversal [weak]
- **ID:** a gap one way, >= 1 bar, then a gap the other way near the same price. **Use:** island top = exit cue; island bottom = watch; enter on later structure.
- **Ev:** Bulkowski: gaps filled in a majority of cases (reported 65-70%); islands rank near the bottom of his tables [P, as summarised]. **Det:** two opposite full gaps in rows with overlapping zones.

### 4.11 Key reversal / outside reversal bar [weak alone; good as a trigger]
- **ID (bullish):** after a decline, a lower low than the prior bar and a close above its high (outside reversal) or at least above its close (key reversal), ideally RVOL >= 1.5. Weekly outweighs daily.
- **Use:** only as a trigger at a pre-identified support, MA or failed-breakdown level; stop below the bar low.
- **Ev:** Bulkowski's key-reversal test won about 58% of trades with a small net gain [P, as summarised]; candlestick signals on DJIA stocks 1992-2002 showed no value (Marshall, Young and Rose 2006) [A, against]: a reversal bar alone is [S].

### 4.12 Climax top / blow-off [underrated as an exit cue]
- **ID (O'Neil [C]):** after a long advance, the largest daily/weekly gain of the move, widest spread, often highest volume, frequently an exhaustion gap; many up days in a row; `01-chart-reading.md` 9.2 "climactic".
- **Use:** no new buys; holders scale out or tighten (`07-exits.md` 10).
- **Ev:** one-month reversal (Jegadeesh 1990) [A], cross-sectional and weakest in large liquid stocks; applying it to O'Neil's criteria is untested [C]. News-driven runs tend to continue (Chan 2003) [A]: a climax without a catalyst is the stronger cue. **Det:** largest weekly gain and volume since the base breakout in hook weekly bars.

### 4.13 Selling climax / capitulation low [underrated; higher risk]
- **ID (Wyckoff [C]):** after a long decline, a wide-range down bar on RVOL >= 2.5 (house default) closing off its low; an automatic rally (AR); a secondary test (ST) holding above the climax low on lower volume.
- **E/S/T:** never on the climax bar; on the ST (reversal bar, higher low) or a close above the AR high / climax low - 0.25 ATR (often > 8%; then the ST low) / AR high, then a base-building phase.
- **Inv:** close below the climax low. **Fail:** ST on heavier volume; falling RS in stage 4.
- **Ev:** [A, indirect] one-month reversal, strongest after no-news drops; bad-news declines keep drifting (Chan 2003) [A]: check filings/news for the climax day; Wyckoff structure [C]. **Det:** max-RVOL down bar of the last 60 rows near the 52-week low.

### 4.14 Wyckoff spring / shakeout [underrated]
- **ID:** in a range after a decline or inside a base, a close (or trade) below support by <= 1 ATR (spring) or more (shakeout), back inside within 1-3 bars; best on a low-volume undercut and higher-volume reclaim [C].
- **E/S/T:** close back above support, or a low-volume test above the spring low / spring low - 0.25 ATR (often fits 8%) / range top, then range height above it.
- **Inv:** close below the spring low. **Ev:** [C]; overlaps 4.16. **Det:** latest swing low below a flat support line, close back above it.

### 4.15 Failed breakout / bull trap [common; exit cue]
- **ID:** a valid close above R, then a close below R - 0.5 ATR within 1-5 bars, worse on volume above the breakout day's (Sperandeo's "2B top" is the same idea [C]).
- **Use:** longs exit (pre-set invalidation, 3.1); no re-entry until a new base or reclaim of R. Short mirror: Turtle-Soup-style sell below the prior 20-day high after a failed new high [P/C].
- **Ev:** Bulkowski busts (often strong moves the other way) [P]; Connors and Raschke (1995) [C/P].

### 4.16 Failed breakdown / bear trap [underrated long setup]
- **ID (Turtle Soup, Connors and Raschke [C]):** a new 20-day low with the prior 20-day low >= 4 sessions old, then a reclaim of that prior low. Daily-close version: close back above the broken support within 1-3 bars. Variants [C]: undercut-and-rally of a prior pivot low or SMA50; Williams' "oops" (gap below the prior low, then back above it).
- **E/S/T:** close above the prior support (buy-stop for `intraday`) / new low - 0.25 ATR / range midpoint, then range top.
- **Inv:** close below the new low. Best when the weekly trend is still up; in stage 4, skip.
- **Ev:** [C/P] practitioner system; [P] Bulkowski busted downward breakouts. **Det:** latest daily swing low below the prior swing low, close back above it.

### 4.17 1-2-3 reversal / trendline break (Sperandeo) [common first sign; weak alone]
- **ID [C]:** (1) close through the trendline (>= 3 touches preferred); (2) a retest fails to make a new extreme (higher low after a downtrend); (3) close through the last pivot (last lower high). Only step 3 completes it.
- **E/S/T (long):** close above the step-3 pivot + buffer / step-2 low - 0.25 ATR / prior resistance, haircut.
- **Use:** step 1 alone never justifies a long (in stage 4 it often becomes a range). Holders of an uptrend: step 1 = tighten, step 3 = exit. **Ev:** [C], no systematic test found. **Det:** break of structure, `01-chart-reading.md` 4.2 rule 4.

## 5. Gaps

Gap up (full) = Low_t > High_{t-1}; size_ATR = (Low_t - High_{t-1}) / ATR14; fill = a later close <= High_{t-1}. Classification is certain only in hindsight: use location, size, volume and the next 1-3 closes [C, Edwards and Magee; P, Bulkowski].

| Type | Criteria | Behaviour | Long action | Label |
|---|---|---|---|---|
| Common / area | inside a range, < 0.5 ATR, normal volume | usually filled within days | ignore | [P] |
| Breakaway | out of a base or through major resistance/support, RVOL >= 2, close near the high | often unfilled for long; gap-day low = support | gap-and-go (3.18) | [P][C] |
| Runaway / measuring | mid-trend after a breakaway | convention: roughly the move's midpoint | hold; trail below the gap | [C] |
| Exhaustion | after a climactic run, huge volume, stalls or reverses within days | filled quickly; ends the move | no new buys; scale out when it fills (4.12) | [P][C] |
| Earnings gap | on a results date (8-K 2.02 / event calendar) | drift in the surprise direction for weeks (PEAD, announcement-return drift) [A], much weaker in large caps since the mid-2000s (Martineau 2022) [A]; one working paper finds the non-fundamental part of earnings-day gaps partly reverses long-run [S], unverified working paper | gap-and-go or first pullback holding the gap; `09-events-hype-and-fear.md` 3-4 | [A], smaller today |

- Gap down through support or the SMA50 on RVOL >= 2 = breakdown cue; an earnings gap down not reclaimed within ~5 bars tends to keep drifting [A for PEAD, C for the 5-bar rule]; its first bounce is not a buy [C].
- A gap over a buy-stop is slippage: re-price (`06-entries.md` 7); a gap through a stop fills beyond the planned loss (`07-exits.md` 4.2).
- An island (4.10) is two gaps. Gap edges are support/resistance zones (`01-chart-reading.md` 6).

## 6. Decision rules and cheat sheet

### 6.1 If X then Y (in order; write each result)

1. No pattern meets its full definition on the primary chart -> no setup; watch note only. Never relax a definition to find one.
2. Context fails (2.2: stage 4, no prior trend, illiquid, late-stage base in `risk_off`) -> reject or lower confidence per `01-chart-reading.md` 12.2.
3. Timeframes conflict -> the higher pattern rules (2.8).
4. State (2.9): forming -> watch; complete -> conditional plan; triggered within cap -> plan; extended -> reject now plus retest/pullback plan; failed -> no long.
5. Structural stop > `max_loss` -> find a real inner structure (handle, final contraction, 3WT, NR7, pocket-pivot low); none -> reject.
6. Base-case R:R < 2.0 (2.5 pre-check) -> reject; never stretch the target or tighten the stop to pass.
7. Base-case move needs longer than the max hold -> longer type (if its chart supports it) or reject.
8. Earnings inside the window -> `09-events-hype-and-fear.md` 4.1.
9. Plan carries pattern invalidation, progress check and max hold (2.9).

### 6.2 Cheat sheet by trade_type

| trade_type | Prefer | Pattern chart | Min size | Stop anchor | Clock (2.9) | Avoid |
|---|---|---|---|---|---|---|
| short_swing | bull flag, pennant, EMA21/SMA20 pullback, breakout retest, failed breakdown/spring, pocket pivot, NR7, gap-and-go | daily | flag 5-15 bars; ranges >= 3 weeks | flag/pullback low, breakout-bar low | bar 5 / 15 bars | weekly bases, stage-4 reversals, broadening, a report inside the hold |
| swing | flat base, VCP, cup with handle, ascending triangle, breakout + retest, SMA50 pullback, inverse H&S, double bottom | daily; weekly context | 5-26 weeks | handle / final contraction / last higher low | bar 10 / 40 bars | deep bases without a tight area, late-stage bases |
| long_swing | weekly flat base, VCP, cup with handle, 3WT, ascending base, weekly double bottom, rounding bottom, 10-week pullback | weekly; daily triggers | 7-65 weeks | weekly tight-area low / 10-week SMA | week 6 / 26 weeks | daily patterns used alone |
| investment | stage 1-to-2 base breakout, multi-year cup or rounding bottom, 30/40-week pullback in stage 2, weekly 3WT to add | weekly; monthly context | >= 13 weeks; multi-year on monthly | final weekly tight area (8% cap) | week 13 / 52 weeks | any structural stop beyond `max_loss` |

### 6.3 Pattern-state line (one per pattern claimed)

name, timeframe, dates, defining pivots | prior trend, stage, base count | depth % and ATR, duration, VDU, tightness | P, trigger, triggered?, RVOL, CLV | stop and % | MM, base case, R:R, feasibility | invalidation, failure signs, clock | evidence, tier.

Hypothetical: XYZ, 7-week flat base 48.20-52.40 (8.0%, 3.8 ATR; ATR14 1.10) after +34%; weekly closes 51.90, 52.05, 51.80. Entry 52.40 + 0.11 = 52.51 (close). Stop: weekly low 50.30 - 0.28 = 50.02; risk 2.49 = 4.7% (passes 8%). MM 4.20; base case = min(52.40 + 3.15 = 55.55, 58.00 - 0.28 = 57.72) = 55.55; R:R 3.04 / 2.49 = 1.22 < 2.0 -> reject, as the pre-check predicts (2.49 > (3.15 - 0.11) / 2 = 1.52). Do not swap in the resistance-based 57.72 (2.09) to pass; reconsider only if a larger weekly structure independently supports a higher base case, or a real tight area gives a stop within 1.52 of entry.

### 6.4 Trader vocabulary map (names you will meet, and where the rule lives)

| Name | Playbook reading | Rule |
|---|---|---|
| Bull trap / fakeout | failed breakout [P, C] | 4.15: exit; no re-entry until a new base or reclaim |
| Bear trap / shakeout / undercut-and-rally | failed breakdown or spring [C] | 4.14, 4.16; `06` T9 |
| Breakout pullback / "second chance" | retest [P] | 3.2; `04` S2 |
| Buyable gap-up / episodic pivot | earnings or news breakaway gap [A drift, C name] | 3.18; `04` S13; `09` 3 |
| Dead-cat bounce | first rebound after a news-driven gap down (D1) or a stage-4 break [C] | not a buy (section 5; `09` 3.1 D1, 8.2) |
| V-bottom | capitulation without a base [C] | 4.13: only a confirmed secondary test or a close above the climax high; half risk |
| Golden / death cross | SMA50 crossing SMA200 [A as momentum, weak alone] | filter only (`02` 6.1, `04` S8) |
| Blow-off top / parabolic run | climax top [C] | 4.12; `09` 7 hype score |
| Base-on-base, cheat entry, power play | base-count and early-entry variants [C] | 2.2, 3.12, 3.6 |
| Diamond, bump-and-run, other rare named shapes | not carded here; no rule depends on them [P, qualitative] | read the parts: broadening (4.9) then triangle (3.9); a steep run then its break (4.12, 4.17) |

A name never replaces the card's objective criteria; if the bars do not meet a card, it is not that pattern.

## 7. Master pattern table

| Pattern | Type | Dir | Min duration | Volume | Entry | Stop | Target | Evidence | Tier |
|---|---|---|---|---|---|---|---|---|---|
| Breakout (resistance/base) | cont | up | 4 wk daily / 7 wk weekly | VDU, then RVOL >= 1.4 | close > R + 0.1 ATR | last higher low / breakout-bar low | base height, capped | A (weakening), P | common (best at 52-week high) |
| Breakout retest | cont | up | <= ~30 days after | light | reversal close near R | retest low / R - 1 ATR | prior high, then MM | P | best (entry) |
| MA pullback | cont | up | 2-8 bars | light | close > prior bar high | pullback low | prior swing high | A indirect, C | best (entry) |
| Bull flag | cont | up | pole <= 15, flag 5-15 bars | heavy pole, light flag | close > flag high | flag low | 0.5-1 x pole | P, A limited | common |
| Bear flag | cont | down | same | mirror | (short: < flag low) | flag high | pole | P | common (exit) |
| Pennant | cont | up | <= 3 wk | light | close > pennant high | pennant low | < 0.5 x pole | P | common |
| High tight flag | cont | up | pole <= 8 wk, flag 3-5 wk | huge pole, dry flag | close > flag high | tight-area low | resistance / 0.5 x pole | P, C | best (rare) |
| Ascending triangle | cont | up | 3 wk | contracting | close > flat top | last higher low | 0.5-0.75 x height | P | common |
| Descending triangle | cont | down | 3 wk | contracting | bust only: > last lower high | last low | - | P | weak (longs) |
| Symmetrical triangle | cont | either | 3 wk | contracting | close outside line | last inside swing | height | A, P | common, weak edge |
| Rectangle / range | cont | either | 3 wk | declining | close > top | midpoint / bottom | height | A, P | common |
| Flat base | cont | up | 5 wk | quiet, tight closes | close > base high | base low / weekly low | haircut MM / resistance / trail | C, P | best fit |
| Cup with handle | cont | up | cup 7 wk, handle 1 wk | dry handle | close > handle high | handle low | depth, haircut | C, P | common |
| Cup without handle | cont | up | 7 wk | dry near lip | close > left lip | last higher low | depth, haircut | C | common |
| VCP | cont | up | 3 wk, 2-6 contractions | lowest in last contraction | close > final contraction high | final contraction low | resistance / trail | C | best fit |
| 3-weeks-tight | cont | up | 3 weekly closes | light | close > 3-week high | 3-week low | trail | C | underrated |
| Ascending base | cont | up | 9 wk | weakness absorbed | close > third peak | third pullback low | trail | C | underrated |
| Rising channel | cont | up | 2 touches per line | - | reversal bar at lower line | lower line - 0.5 ATR | upper line | C | common |
| Gap-and-go | cont | up | 1 bar + follow-through | RVOL >= 2 | close > gap-day high / held pullback | gap-day low | resistance / base height | A (earnings), P | common |
| Pocket pivot | cont | up | 1 bar | up vol > max down vol (10 d) | pocket-pivot close | 50-day SMA / day low | base high | C | underrated |
| NR7 / inside bar | trigger | host | 1 bar | low | > bar high | bar low | host target | P (futures), C | underrated |
| Double bottom | rev | up | 4 wk between lows | light 2nd low | close > middle peak | 2nd low | height | A, P | best reversal |
| Double top | rev | down | 4 wk | mirror | exit cue | - | height | A, P | common (exit) |
| Triple bottom/top | rev | up/down | 3 wk between | light last test | close through peak/trough | last low/high | 0.5 x height | P | common |
| Head-and-shoulders top | rev | down | 4-6 wk daily / 3 mo weekly | light right shoulder | exit on neckline close | - | height (half realistic) | A, P | best bearish (exit) |
| Inverse H&S | rev | up | 4-6 wk daily / 3 mo weekly | rising on right side | close > neckline | right-shoulder low | 0.5-0.75 x height | A, P | common |
| Rounding bottom | rev | up | 7 wk | U-shaped | close > rim / handle | handle / weekly low | depth | C, P | underrated |
| Rising wedge | rev | down | 3 wk | fading | tighten stops | - | wedge start | P, C | weak |
| Falling wedge | rev | up | 3 wk | fading | close > upper line + last lower high | wedge low | wedge start | P, C | common |
| Broadening | rev | either | 5 swings | erratic | avoid | - | - | A, P | weak |
| Island reversal | rev | either | 2 gaps | heavy on gaps | wait | - | - | P | weak |
| Key/outside reversal | rev | either | 1 bar | RVOL >= 1.5 | trigger at support only | bar low | next level | P, S (A against candles) | weak alone |
| Climax top | rev | down | 1-3 wk run | biggest gain/volume | exit/scale-out cue | - | - | A indirect, C | underrated (exit) |
| Selling climax | rev | up | climax + test | RVOL >= 2.5, light test | close > AR high / test hold | climax or ST low | AR high | A indirect, C | underrated |
| Spring / shakeout | rev | up | 1-3 bars | light undercut | close back in range | spring low | range top | C | underrated |
| Failed breakout | rev | down | 1-5 bars | heavy reversal | exit cue | - | range bottom | P, C | common (exit) |
| Failed breakdown | rev | up | 1-3 bars | heavy reclaim | close > support | new low | range mid/top | P, C | underrated |
| 1-2-3 reversal | rev | either | 3 swings | rising on step 3 | close > step-3 pivot | step-2 low | prior resistance | C | common, weak alone |
| Common gap | gap | either | 1 bar | normal | ignore | - | - | P | weak |
| Breakaway gap | gap | trend | 1 bar | RVOL >= 2 | gap-and-go | gap-day low | base height | P, C | common |
| Runaway gap | gap | trend | 1 bar | above average | hold / add on hold | below gap | gap as midpoint | C | common |
| Exhaustion gap | gap | reversal | 1 bar | climactic | exit when filled | - | - | P, C | underrated (exit) |
| Earnings gap | gap | surprise | 1 bar | very heavy | gap hold / pullback | gap-day low | resistance / trail | A (weaker in large caps) | best in smaller names; common in large |

## Sources

Academic
- Lo, Mamaysky, Wang (2000), Foundations of technical analysis, Journal of Finance 55(4) 1705-1765. https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00265 ; https://www.nber.org/papers/w7613 ; templates, tolerances (1.5%; 0.75% rectangles), 38-day window and > 22-day double separation as summarised at https://www.r-bloggers.com/2012/05/classical-technical-patterns/ (not re-checked against the paper).
- Savin, Weller, Zvingelis (2007), Journal of Financial Econometrics 5(2) 243-265. https://academic.oup.com/jfec/article-abstract/5/2/243/785044
- Chang, Osler (1999), Methodical madness, Economic Journal 109(458) 636-661. https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0297.00466
- Leigh, Modani, Purvis, Roberts (2002), Expert Systems with Applications 23(2). https://www.sciencedirect.com/science/article/abs/pii/S0957417402000349
- Brock, Lakonishok, LeBaron (1992); Sullivan, Timmermann, White (1999); George, Hwang (2004); Jegadeesh (1990); Marshall, Young, Rose (2006): `01-chart-reading.md` Sources.
- Ball, Brown (1968); Bernard, Thomas (1989), PEAD: https://en.wikipedia.org/wiki/Post%E2%80%93earnings-announcement_drift ; review https://www.sciencedirect.com/science/article/pii/S2214635020303750
- Chan, Jegadeesh, Lakonishok (1996), Momentum strategies, Journal of Finance 51(5) (not re-checked online).
- Chan, W. S. (2003), Journal of Financial Economics 70 (news vs no-news). https://ideas.repec.org/a/eee/jfinec/v70y2003i2p223-260.html
- Martineau (2022), Rest in peace post-earnings announcement drift, Critical Finance Review 11(3-4). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607
- Engle (1982), Bollerslev (1986) ARCH/GARCH (not re-checked online).
- Ben-Rephael et al., Mind the gap (working paper). https://haslam.utk.edu/wp-content/uploads/2024/11/Ben-Rephael-Paper.pdf

Practitioner statistics
- Bulkowski, thepatternsite.com (figures from search-result excerpts; pages not fetched and unreachable in review, hence "as summarised"; averages to the ultimate high/low, in-sample): hst.html; htf.html, HTFStudy.html; flags.html, pennants.html, measure.html; AdamEvePatterns.html; throwbacks.html, pullbacks.html; volbkout.html; at.html, BustDescTriangles.html, st.html, BustSymTriangles.html; risewedge.html; FlatBase.html; cup.html, top10.html; islandrev.html, KRU.html; gaps.html (all under https://thepatternsite.com/). Encyclopedia of Chart Patterns (book).
- Crabel (1990), Day Trading with Short Term Price Patterns and Opening Range Breakout (NR4/NR7).

Practitioner conventions
- O'Neil / IBD (cup, flat base, ascending base, HTF, 3WT, base count): How to Make Money in Stocks; https://finance.yahoo.com/news/high-tight-flag-rare-pattern-204600066.html ; https://www.nasdaq.com/articles/how-3-weeks-tight-pattern-gives-you-extra-buy-point-2017-12-20 ; https://finance.yahoo.com/news/looking-great-chart-sure-count-203400677.html
- Minervini, Trade Like a Stock Market Wizard (VCP, trend template, cheat entry, power play). https://traderlion.com/technical-analysis/volatility-contraction-pattern/
- Morales, Kacher, Trade Like an O'Neil Disciple (pocket pivots). https://www.virtueofselfishinvesting.com/pocket-pivot
- Connors, Raschke (1995), Street Smarts (Turtle Soup). https://oxfordstrat.com/trading-strategies/turtle-soup-plus-1/
- Sperandeo (1991), Trader Vic: Methods of a Wall Street Master (1-2-3, 2B); Williams (1999), Long-Term Secrets to Short-Term Trading ("oops").
- Wyckoff: https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial
- Edwards and Magee, Technical Analysis of Stock Trends; Murphy, Technical Analysis of the Financial Markets; Weinstein, Secrets for Profiting in Bull and Bear Markets.
