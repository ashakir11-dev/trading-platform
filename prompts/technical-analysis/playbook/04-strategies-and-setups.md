# 04 - Strategies and setups

## How to use this file

- A setup is a named recipe: fit, preconditions, trigger, stop, targets, scaling, clocks, failure signs. Pick ONE primary setup per plan and name its ID (S1-S15) in the output's `## Setup` section.
- Order: chart read and knockouts (`01-chart-reading.md` 3, 15, 16.1) -> decision tree (section 4) -> only the qualifying cards (section 3) -> execution checks (1.7) -> plan (`08-trade-plan-and-timeline.md` 12).
- Every card must still pass `role.md` (max loss 8%, reward:risk 2.0, stale entry, earnings). If chart-justified levels fail, reject with a section 7 code; never move levels to fit.
- Labels: [A] academic/replicated, [P] practitioner statistical study, [C] convention (incl. untested "house default" thresholds), [S] speculative/contested. Tiers: best / most common / underrated / high risk. Examples are hypothetical (XYZ).
- Formulas `02-indicators.md`; patterns `03-chart-patterns.md`; entries `06-entries.md`; stops/trails/scale-out `07-exits.md`; clocks and plan format `08`; earnings/news `09-events-hype-and-fear.md`. Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).

## 1. Ground rules shared by all setups

### 1.1 Vocabulary

| Term | Definition (daily bars unless stated) |
|---|---|
| Stage | Weinstein stage 1-4 on the context chart (`01` 5.1). Stage 2 = price above a rising 30-week SMA (~SMA150), weekly HH+HL. |
| Regime | risk_on / neutral / risk_off (`01` 12); panic = market ATR or VIX spiking after a decline. |
| d (extension) | (close - MA) / ATR14; MA and limits per trade_type (`01` 9.2). |
| RVOL | V_t / mean(V, prior 50 days) (20 for short_swing, `01` 1.3); weekly: week V / mean(prior 10 weeks). |
| CLV | ((C - L) - (H - C)) / (H - L); > 0 upper half, > 0.5 top quarter, < -1/3 lower third; 0 if H = L. |
| P (pivot) | level whose breach triggers the setup (base high, handle high, range edge, gap-day high). |
| Buffer | entry 0.1 x ATR14 beyond the level (0.05-0.25 by ATR%, `06` 4; weekly-close triggers 0.1 x weekly ATR14); stop buffer per trade_type (`05` 7.1): 0.25-0.5 daily ATR short_swing, 0.5-1 swing, 0.25-0.5 weekly ATR long_swing, 0.5 weekly ATR investment [C house default]. |
| RC (reversal close) | close > prior bar's high with CLV > 0.5: the standard pullback trigger. |
| R | e - s (long). Blended target = sum(f_i x T_i) when scaling out. |

### 1.2 Triggers (profile `level_trigger`)

`close` (default): "daily close above P + buffer"; the human buys at/near the close or next open, capped by `stale_entry` (<= 3% above `entry`). `intraday`: "buy-stop at P + buffer"; accepts intraday false breaks and cannot be verified until the daily bar prints (say so). Closing triggers filter many false breaks at the cost of a worse fill [C]. Pullback setups use "limit at L" only when L is a grade-A zone (`01` 6.3); otherwise wait for an RC.

### 1.3 Stops and feasibility

Stop = structural level that proves the setup wrong, plus an ATR buffer; use the farther. |e - s| / e > 8% = reject; never tighten into noise [C]. Quick check: stop-in-ATRs x ATR% <= 8 (`01` 10.2).

### 1.4 Targets and reward:risk

- T1 (= role `target`) preference: (1) next resistance zone minus 0.25 ATR; (2) measured-move base case, 0.5-0.75 x height (`03` 2.5); (3) in blue sky (no supply within 2 years) a measured move or ATR projection. T1 must pass reachability k = (T1 - e) / (0.63 x ATR14 x sqrt(max-hold bars)) <= 1.5 [C house default; random-walk scaling, not a forecast] (`05` 5.3). R multiples (2-3R) are runner checkpoints only, never the rule-checked target (`07` 5.1).
- Scaling out: `reward_to_risk` is checked on T1 alone (role.md; `07` 6.4, `08` 10). Blended R:R is information in `## Plan` and cannot rescue a T1 below the minimum.

### 1.5 Clocks by trade_type (canonical: `08` 4; summary `CONVENTIONS.md`)

CP1 (MFE >= +0.5R and trigger level held, else the type's fail action) bar 5 / bar 10 / week 6 / week 13; CP2 (close >= +1R or new swing high, else stop to breakeven or exit) bar 10 / bar 20 / week 13 / week 26; max hold (exit or re-underwrite as a NEW plan) 15 bars / 40 bars / 26 weeks / 52 weeks per plan (short_swing / swing / long_swing / investment). Pipeline horizon: short_swing, swing -> `swing`; long_swing -> `swing` if max hold <= ~13 weeks, else `long_term`; investment -> `long_term`.

[C house defaults.] A clock must not outlast the effect the setup relies on: short-term reversal 1 week-1 month [A], momentum 3-12 months [A], PEAD about one quarter [A]. Card-specific clocks apply when earlier (`08` 4.1).

### 1.6 Scaling (all cards)

- In: short_swing all at once. Longer types add only to a winner on a new trigger (close >= e + 0.5R, retest hold, new high), each add <= the prior tranche, stop raised so total open risk <= initial plan risk; max adds 1/2/3 for swing/long_swing/investment (`06` 10.2). No averaging down except a card's pre-planned tranche that shares ONE stop and passes the rules in every fill state (`06` 10.3-10.4).
- Out (fractions: `07` 6.5): trend setups (S3-S7, S13) keep a runner on a trail because their payoff comes from a few large winners [P] (S7); mean-reversion setups (S10, S11, S14, S15) exit fully at target. Never add and scale out at the same level.

### 1.7 Execution realities (check before any plan)

| Issue | Rule |
|---|---|
| False breakout | The card's failure rule is the exit. One re-entry per setup, only on a fresh trigger with fresh levels: a reclaim of P after a new higher low (`06` T9) or a new pivot (new handle, S2 hold, new base); never the same day [C] (`06` 3.3). |
| Gap over trigger | Within the 3% cap: fill, re-check R:R at the fill. Above: cancel; a breakaway gap may be re-planned after the close as S13 (`06` 7). State the fill ceiling e_max = (T1 + 2s) / 3 at R:R 2.0, rounded down to the cent: "void above e_max" (`05` 7.5, `06` 8.3). |
| Gap through stop | Realised loss can exceed 8%. >= 3 non-earnings gaps in 252 bars that alone would skip the stop = stop inside gap noise: wider-stop type or reject (`07` 4.2). |
| Liquidity, slippage | 20-day dollar volume < $5M: reject short_swing/swing; $5-20M: limits, wider buffers (`01` 7.3). cost_R = cost% / stop%: tight-stop setups (S2, S9, S10, S14) suffer most. |
| Earnings | short_swing: no report from entry to max hold + 2 sessions (shorten max hold to end >= 1 session before it only if T1 stays reachable, else reject); swing: no new entry in the 10 sessions before a report and a pre-stated exit/halve/cushion decision; long_swing/investment: name each report and the action (`09` 4.1-4.2). |
| Weekly triggers | Friday-close signals fill Friday late or Monday open and carry the weekend gap; check the cap on the actual fill. |
| Plan before entry | Setup ID, trigger, `valid_until` (`08` 4), stop, invalidation, T1 (+T2), CP1/CP2 dates, max-hold date, action at each report. No exit date = incomplete plan. |

## 2. Setup index and state of evidence

| ID | Setup | Family | Tier | Label | Best trade_types |
|---|---|---|---|---|---|
| S1 | Pullback to rising MA | trend continuation | most common | [C]; [A] behind it | short_swing, swing (weekly: longer) |
| S2 | Breakout retest | trend continuation | underrated | [P] Bulkowski; [C] | short_swing, swing |
| S3 | Base breakout (flat, cup with handle, VCP) | trend continuation | most common; best with S4/S5 | [C]; [P]; [A] underlying | swing, long_swing |
| S4 | Momentum / RS leadership | filter + entry | best | [A] | swing, long_swing, investment |
| S5 | 52-week-high proximity / new high | trend continuation | best | [A] George-Hwang; [P] | swing, long_swing, investment |
| S6 | Weinstein stage-2 breakout | trend start | underrated | [C]; [A] behind it | long_swing, investment |
| S7 | Donchian / turtle trend following | trend following | best as a system; most common | [A] historic; [P] stocks | swing, long_swing |
| S8 | MA crossovers | filter | most common | [A] mixed, failed out of sample | filter only |
| S9 | Bollinger / Keltner squeeze | volatility breakout | most common | [A] vol clustering; [C] direction | short_swing, swing |
| S10 | RSI(2) dip in an uptrend | mean reversion | underrated | [P] Connors; [A] reversal | short_swing |
| S11 | Range trading | mean reversion | most common | [C]; [A] limited | short_swing, swing |
| S12 | Wyckoff spring / failed breakdown | base reversal | underrated | [C]/[S] | swing, long_swing |
| S13 | Post-earnings drift / gap continuation | event continuation | underrated; best small/mid caps | [A], decayed in large caps | short_swing, swing |
| S14 | Gap fill | mean reversion | most common | [P]; [S] direction | short_swing |
| S15 | Capitulation reversal | counter-trend | high risk | [S], mixed [A] | short_swing |

Candid summary: the strongest evidence is for buying strength (S4, S5, S7, and S1/S3 when they execute S4/S5) and for event drift (S13) where it survives. S3 base types, S6, S9, S11, S12 are coherent conventions without rigorous out-of-sample tests; their thresholds are house defaults. Searching many rules inflates in-sample results: the best classic Dow rules survived a data-snooping correction in-sample (1897-1986) but did not outperform out of sample (1987-1996) (Sullivan, Timmermann and White 1999) [A]. Use card defaults; never tune parameters to the chart in front of you.

## 3. Setup cards

Fields: Fit | Pre (all must hold) | Trigger | Stop | Targets | Scale | Clock | Fail | Evidence. Clock = setup-specific; 1.5 otherwise.

### S1. Pullback to a rising MA (EMA10/EMA21, SMA50, 10/30/40-week SMA)  [most common]

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Pullback MA | EMA10 (strong trends), EMA21 | EMA21, SMA50 | 10-week, 30-week SMA | 40-week / 10-month SMA |
| Slope required | EMA21 up over 5 bars | SMA50 up over 20 bars | 10-week up over 4 weeks | 40-week up over 8-13 weeks |
| Typical pullback / hold | 2-8 bars / 3-10 bars | 3-15 bars / 2-6 weeks | 2-6 weeks / 2-5 months | 1-4 months / months |
| Stop buffer below pullback low | 0.5 ATR | 0.5-1 ATR | 0.5 weekly ATR | beyond weekly swing low; 8% usually binds |

- **Fit:** risk_on/neutral; risk_off only grade-A leaders. Stage 2.
- **Pre:** primary HH+HL; MA touched (low <= MA + 0.25 ATR), no close > 1 ATR below it; pullback volume below its 50-day average [C] (Cooper 1999 [A] conditions short-term reversal on volume in large NYSE/AMEX stocks; the direction of that effect was not re-verified here, so no rule rests on it); retrace ~38-62% of the prior leg [C]; RS line not at a 3-month low; d within `01` 9.2.
- **Trigger:** RC after the touch; `intraday`: buy-stop above the high of the pullback's lowest bar. Raschke's "Holy Grail" (strong trend, pullback to EMA20, buy-stop over the touch bar) and a pocket-pivot day off the MA (`03` 3.19) are S1 trigger variants [C].
- **Stop:** pullback low minus table buffer. **Targets:** T1 = swing high the pullback started from, minus buffer; T2 only near the 52-week high with no supply: prior leg added to the pullback low [C]. T1 < 2R and no justified T2 = reject.
- **Scale:** swing+: 2/3 on trigger, 1/3 on close >= e + 0.5R. Out per `07` 6.5 (short_swing all or 1/2; swing 1/2; long_swing 1/3 at T1), trail the rest under the MA (`07` 8).
- **Clock:** short_swing: no close above the trigger bar's high within 3 bars = suspect.
- **Fail:** close > 1 ATR below the MA on RVOL > 1.2; lower low under the pullback low; down bars heavier than the prior advance.
- **Evidence:** touch rule and 38-62% band [C]. Logic: buy intermediate winners (momentum [A]) after a short-term loss (reversal [A]; Jegadeesh 1990, Lehmann 1990); the effects were documented separately, their combination is inference [C]. In high-turnover large caps last month's return shows momentum, not reversal (Medhat and Schmeling 2022) [A]: a sharp high-volume pullback there is weaker than a quiet one.

### S2. Pullback to the prior breakout level (retest)  [underrated]

- **Fit:** risk_on/neutral; stage 2 or fresh 1->2. All types (weekly retest for long_swing/investment).
- **Pre:** a valid S3/S5/S6/S7 breakout (close > P + buffer, RVOL >= 1.4, short_swing 1.5) 2-21 bars ago (about Bulkowski's 30 calendar days; weekly 2-10 weeks) (`06` T6); price in P +/- 0.5 ATR on below-average volume; no close below P - 0.5 ATR; above a rising SMA50 (10-week).
- **Trigger:** RC off the zone, or a limit in a grade-A zone. **Stop:** lower of retest low and P - 1 ATR (or handle/last contraction low); usually the tightest trend stop.
- **Targets:** T1 = post-breakout high; T2 = base depth added to P [C].
- **Scale:** natural second tranche for a held breakout (only if the first is not below plan); new entrants single entry.
- **Clock:** no reclaim of the post-breakout high within 15 bars (6 weeks weekly) = exit.
- **Fail:** close below P - 0.5 ATR = failed breakout (`03` 2.6, 4.15); exit, re-entry only per 1.7.
- **Evidence:** Bulkowski's throwback study (19 pattern types, 1991-2005, 10,348 patterns, 3,167 with throwbacks, i.e. about 31%; as summarised, not re-verified; single-pattern pages are summarised as "about half or more", `03` 2.6): upward breakouts WITHOUT a throwback did better in almost all types, and throwbacks staying above the breakout price did better than those falling below [P]. A retest trades a lower average outcome for a better price and tighter stop; losing P is a warning, not a bargain. Weinstein's second-chance buy [C].

### S3. Base breakout: flat base, cup with handle, VCP  [most common; best with S4/S5]

- **Fit:** risk_on; neutral grade A; not risk_off (momentum profits appeared only after up markets measured by the prior 3-year market return, Cooper, Gutierrez and Hameed 2004 [A]). swing, long_swing; short_swing only the first 1-3 weeks.
- **Pre:** Minervini trend template [C] (`01` 5.1). His RS rating >= 70 is a universe percentile we cannot compute: substitute 6m and 12m return above SPY and sector, RS line within 5% of its high (S4). Also: prior advance >= ~25-30%; 1st-2nd base of the stage preferred [C]; final-contraction volume below the 50-day average; base up/down volume >= 1.

| Base (`03`) | Duration | Depth | Pivot | Tell |
|---|---|---|---|---|
| Flat [C O'Neil] (3.11) | >= 5 weeks | <= ~15% | base high | tight weekly closes; often after a prior base |
| Cup with handle [C; P] (3.12) | cup 7-65 weeks | 12-33% | handle high | handle in upper half, low-volume drift, 1-2+ weeks (house cap 4), ~8-12% deep in bull markets (O'Neil) |
| VCP [C Minervini] (3.14) | weeks-months | 2-6 shrinking contractions (e.g. 20, 10, 5%) | last contraction high | volume dry-up in the last contraction |
| Variants | 3WT (3.15), base-on-base: pivots or add points; ascending base (3.16); "cheat" early entry (3.12); bull flag / pennant (3.3, 3.5): short_swing/swing continuation, flag low as stop; high tight flag (3.6): high risk, flag low usually beyond 8% | | | |

- **Trigger:** close above P + buffer, RVOL >= 1.4, CLV > 0 [C: O'Neil asks 40-50% above-average volume]; never > 3% above P (`stale_entry`; O'Neil allows 5%).
- **Stop:** handle / last contraction low minus 0.25-0.5 ATR; deep handle-less cups often fail 8%. O'Neil's 7-8% loss cap matches [C].
- **Targets:** T1 = measured-move base case (0.5-0.75 x base depth from P, `03` 2.5), or an older high below it; full depth = T2. O'Neil takes most gains at 20-25% but holds a stock up >= 20% within 3 weeks of breakout for >= 8 weeks [C] (for a swing that is a graduation, `05` 13).
- **Scale:** 1/2 at P, 1/2 on the first S2 hold or a close above the breakout-day high within 5 bars; no add > 5% above P. Out per `07` 6.5 (swing 1/2, long_swing 1/3 at T1), trail.
- **Clock:** not above P + 1R within 10 bars (swing) / 3 weeks (long_swing) = exit or halve [C].
- **Fail:** close below P - 0.5 ATR within 5 bars (`03` 4.15); breakout on RVOL < 1 with CLV < 0; breakout day closing in the lower third.
- **Evidence:** O'Neil/Minervini criteria [C] (anecdotal, untested out of sample). Bulkowski's cup statistics [P] measure to the ultimate high: never quote as expected returns. Lo, Mamaysky and Wang (2000) [A]: some patterns carry modest distributional information (not profits; cup with handle untested). Strongest support is indirect: the template selects momentum and 52-week-high stocks [A].

### S4. Momentum / relative-strength leadership  [best]

- **Fit:** risk_on/neutral; not in a high-volatility rebound after a sharp decline (momentum crashes, Daniel and Moskowitz 2016 [A]). swing, long_swing, investment; weak for short_swing (1-month reversal).
- **Compute:** 12-1 = C_{t-21} / C_{t-252} - 1 (weekly C_{w-4} / C_{w-52} - 1), vs SPY and sector on the same dates. RS = C_stock / C_SPY; RS new high = RS >= max(RS, 252 days). Frog-in-the-pan ID = sign(12-1) x (% negative days - % positive days); lower = smoother = more persistent (Da, Gurun and Warachka 2014 [A]).
- **Pre:** 12-1 > 0 and above SPY's and sector's; 12-month return > 0 (TSMOM, Moskowitz, Ooi and Pedersen 2012 [A], is futures/forwards evidence: on one stock a consistent filter, not a tested rule); RS within 5% of its 52-week high; ID <= 0 preferred; stage 2; sector ETF above SMA200 (industry momentum explains much of stock momentum, Moskowitz and Grinblatt 1999 [A]). Stocks making RS new highs while SPY corrects are first candidates when the regime turns [C].
- **Trigger:** primarily a FILTER; entries come from S1/S2/S3/S5. Standalone (long_swing, investment): weekly close back above the 10-week SMA after a 1-4 week pullback that held the 30-week.
- **Stop:** entry setup's; standalone: pullback weekly low minus 0.5 weekly ATR. **Targets:** none natural: entry setup's structural target for the rule check, trail the rest.
- **Scale:** investment thirds over 2-3 weekly triggers; long_swing halves.
- **Clock:** re-check 12-1 and RS monthly; stop adding / exit on an RS 26-week low or 12-1 below SPY's. Returns concentrate in 3-12 months and partly reverse after [A]: long_swing max 26 weeks, investment re-underwrite at 52.
- **Fail:** RS breaks its 50-day (10-week) average with a lower low while price stalls. Very high recent turnover is a caution, not an exit (Lee and Swaminathan 2000 [A]: high-volume winners are later in the momentum life cycle and reverse sooner, over multi-year horizons).
- **Evidence:** cross-sectional (Jegadeesh and Titman 1993) and time-series momentum are among the most replicated effects [A]; 12-7 month returns carry much of it (Novy-Marx 2012) [A]. They are portfolio averages: one name can fail, so stops stay mandatory. "RS new high before price" is [C] (IBD).

### S5. 52-week-high proximity and new-high breakout  [best]

- **Fit:** risk_on/neutral. swing, long_swing, investment (short_swing only the breakout's first days).
- **Compute:** PTH = close / highest close of 252 bars (George and Hwang 2004 used the highest daily CRSP price, a close); the intraday-high version is slightly lower: say which. Longer types: also multi-year high on weekly bars.
- **Pre:** PTH >= 0.90 [C threshold; effect monotonic in PTH, George and Hwang 2004 [A]]; stage 2; consolidation >= 3 weeks (daily) / >= 5 weeks (weekly) just below the high; no report in the first 10 bars.
- **Triggers:** (a) close above the 52-week closing high + buffer, RVOL >= 1.4 (short_swing 1.5); (b) S1 or S2 trigger with PTH >= 0.90.
- **Stop:** consolidation low or last swing low minus 0.5 ATR. **Targets:** blue sky: consolidation measured move or an ATR projection with k <= 1.5 (R objectives only as runner checkpoints); an old all-time high from years ago is T1.
- **Scale:** in halves (breakout, retest); out per `07` 6.5, trail.
- **Clock:** close back below the old high within 5 bars = suspect, within 10 = failed.
- **Fail:** new high on RVOL < 1 and CLV < 0; repeated intraday probes above the closing high that do not close there.
- **Evidence:** George and Hwang (2004) [A]: nearness to the 52-week high predicts returns, subsumes much of momentum, does not reverse long run; it is a cross-sectional ranking held 6-12 months, not a breakout-day rule, so card thresholds are [C]. Buying all-time/52-week highs with ATR trails was profitable on US stocks in practitioner tests (Wilcox and Crittenden 2005; Zarattini, Pagani and Wilcox 2025) [P]. Near-high is strength, not "overbought".

### S6. Weinstein stage-2 breakout on the weekly 30-week MA  [underrated]

- **Fit:** risk_on/neutral (SPY weekly above its 30/40-week SMA [C]). long_swing, investment; swing only if the base is short and the stop fits.
- **Pre:** stage 1 base of roughly 3+ months [C]; 30-week SMA flat and turning up (4-week slope >= 0); Mansfield RS rising toward/above 0 (`01` 1.3); light supply in the next ~15-20% (no heavy weekly volume shelf above).
- **Trigger:** weekly close above base resistance + 0.1 weekly ATR and above the 30-week, week volume >= 2x the prior 4-10 week average [C Weinstein]. Daily fine entry (`01` 13): first close above the breakout week's high, or the first S2 retest.
- **Stop:** Weinstein's (below the base's last significant low [C]) often exceeds 8%; then the S2 retest entry or breakout week low minus 0.5 weekly ATR if structural; else reject. Daily-close hard stop plus weekly invalidation (`07` 4.3).
- **Targets:** next major weekly resistance (prior stage-3 zone); blue sky: base height added to the breakout. Weinstein trails: structural rule-check target, runner under the rising 30-week / last weekly swing low.
- **Scale:** 1/2 breakout, 1/2 on the retest or first 10-week pullback [C].
- **Clock:** no weekly close above the breakout week's high within 6 weeks = exit (long_swing).
- **Fail:** weekly close below the 30-week within 4 weeks; breakout week volume below average; Mansfield negative and falling.
- **Evidence:** stage analysis [C] (coherent, untested). Behind it: time-series momentum [A], index MA timing (Faber 2007) [P], 52-week-high effect when the base top is the 52-week high [A].

### S7. Donchian / turtle channel breakout and time-series trend following  [best as a system; most common]

| Variant | Entry | Exit (trail) | Initial stop | Source |
|---|---|---|---|---|
| Turtle System 1 | above 20-day high | 10-day low | 2N, N_t = (19 N_{t-1} + TR_t) / 20 | [C]; skip if the prior System 1 signal was a winner (then take the 55-day break) |
| Turtle System 2 | above 55-day high | 20-day low | 2N | [C] |
| Weekly channel | weekly close above 20-week (or 52-week) high | weekly close below 10-week low, or HH10W - 3 weekly ATR | 2 weekly ATR or structure | [C] adaptation of LeBeau's chandelier (daily HH22 - 3 x ATR22) |
| New-high trend following | new all-time / 52-week closing high | wide ATR trail, never lowered | the trail | [P] Wilcox and Crittenden 2005; Zarattini et al. 2025 |
| TSMOM filter | 12-month return > 0 | 12-month return < 0 | n/a | [A] Moskowitz, Ooi and Pedersen 2012 |

- **Fit:** filter in any regime; initiate risk_on/neutral. swing (20/55-day), long_swing (weekly). Poor for short_swing (whipsaw) and when ATR% > ~4% (2N fails 8%).
- **Pre:** 12-month return > 0; SMA200 rising; stop within 8%; liquidity (1.7).
- **Scale:** turtles added a unit per 0.5N up to 4 [C]; here <= 3 tranches, each after a new 0.5-1 ATR advance, stop raised so total risk <= initial.
- **Targets:** none by design; the edge is the right tail. Rule check: T1 = next resistance, measured move or ATR projection with k <= 1.5; 3R is a runner checkpoint only; trail the rest and say T1 is a first objective, not the exit plan.
- **Clock:** opposite channel exits flat trends; plus 1.5 max hold. **Fail:** breakouts reversing to the opposite channel (range, ADX < 20 [C]); expect loss strings.
- **Evidence:** channel rules were profitable on the Dow 1897-1986 (Brock, Lakonishok and LeBaron 1992) [A] but did not outperform out of sample 1987-1996 (Sullivan et al. 1999) [A]; index, no costs. Futures trend following behind TSMOM is [A] but not single-stock. On US stocks (survivorship-free 1950-2024, > 66,000 simulated long-only trades) Zarattini, Pagani and Wilcox (2025) report a win rate of about 44%, average win about 1.9R vs loss about 0.7R, and fewer than 7% of trades producing essentially all cumulative profit [P, as summarised; not re-verified]. So fixed 2R exits on the whole position cut off the edge; low win rates are normal.

### S8. Moving-average crossover systems  [most common; filter, not a setup]

- **Forms:** SMA50 x SMA200, EMA10 x EMA21, 10-week x 30-week, price x 10-month SMA (Faber).
- **Evidence:** any MA rule is a weighted sum of past price changes, i.e. momentum (Zakamulin 2017) [A]; MA rules and TSMOM mostly give the same signal, differing in timing (Marshall, Nguyen and Visaltanachoti 2017) [A], so a cross is NOT extra confirmation next to price-vs-MA, slope or 12-month momentum. Early index studies were positive (Brock et al. 1992), the best rules failed out of sample (Sullivan et al. 1999) [A]; Park and Irwin's (2007) survey: most modern studies positive but with frequent snooping, ex-post selection and cost problems [A]. Faber's 10-month rule mainly cut index drawdowns [P]. MA timing pays more on high-volatility portfolios (Han, Yang and Zhou 2013) [A]. Single-stock crosses whipsaw in ranges and fire late.
- **Use:** as a required filter (e.g. "SMA50 > SMA200, both rising"), counted once in the trend group (section 8). As an entry (discouraged): swing/long_swing, cross with price above both rising MAs, stop last swing low - 0.5 ATR within 8%, target next resistance; the opposite cross is too late an exit, the plan's stop governs. **Fail:** cross inside a flat range (ADX < 20, low efficiency ratio [C]).

### S9. Bollinger / Keltner squeeze breakout  [most common]

- **Fit:** risk_on/neutral. short_swing, swing (weekly for long_swing).
- **Definitions:** BandWidth(20, 2) at its lowest of ~125 bars (Bollinger) [C]; TTM-style: Bollinger(20, 2) inside Keltner (20-period mid +/- 1.5 ATR) (Carter) [C], platforms differ (EMA/SMA mid, ATR 10/20): state yours (`02` 7.3-7.4). NR7 / inside-bar / inside-week clusters are the short-term cousin (`03` 3.20). One volatility factor: count once.
- **Pre:** stage 2 above a rising SMA50 (direction comes from the trend); upper half of the 3-month range; squeeze range (high-low of squeeze bars) <= ~3-4 ATR [C house default]; earnings rules of 1.7 (a pre-earnings squeeze is the event waiting).
- **Trigger:** close above the squeeze high + buffer, BandWidth rising, RVOL >= 1.5. **Stop:** squeeze low, or SMA20 - 0.5 ATR if closer and structural.
- **Targets:** next resistance; else squeeze height x 2 [C house default, untested], k <= 1.5. **Scale:** swing: add on the first hold of the squeeze high.
- **Clock:** expansion within 3-5 bars; back inside the range at bar 5 = exit.
- **Head fake [C, Bollinger]:** a first break DOWN that returns inside within 1-2 bars makes a later upside break in an uptrend higher quality; a first break UP that closes back below the range midpoint = exit.
- **Evidence:** volatility clustering and mean reversion of volatility [A]: quiet precedes busy, but not when; direction [C]/[S]. Crabel's NR7-type statistics [P] are next-day opening-range breakouts in futures/indexes; multi-day daily use is [C].

### S10. Mean reversion within an uptrend (RSI(2))  [underrated]

- **Fit:** risk_on/neutral; reversal pays more when volatility is high (Nagel 2012) [A], but only with the long trend intact. short_swing (swing only with a prior-high target).
- **Connors' rules [P]:** close > SMA200; buy when RSI(2) closes < 5 (< 10 looser); exit on a close above SMA5 (`02` 7.1).
- **Pre (added):** stage 2, SMA200 rising; 3+ down closes or a drop to a graded zone / rising SMA50; declining volume [C]; NO news or earnings behind the drop (news moves drift, no-news moves reverse, Chan 2003 [A]); liquid large/mid cap; no report inside the hold (1.7).
- **Trigger:** "daily close with RSI(2) < 5 and close > SMA200"; conservative: next RC.
- **Stop:** Connors reported stops hurt his results [P]; this profile requires one: structural level minus 0.5-1 ATR, <= 8%.
- **Targets:** the SMA5 exit usually gives well under 2R with a structural stop, so the plan FAILS unless the target is the prior swing high and the stop sits tight at a zone; reject rather than stretch.
- **Scale:** Connors' variants average down [P]; here only a pre-planned 2-tranche entry sharing one stop (1.6). Exit fully at target.
- **Clock:** 5-8 bars (reversal is a days-to-weeks effect [A]). **Fail:** close below SMA200 or a news gap; RSI(2) < 10 for 4+ bars with lower lows.
- **Evidence:** short-term reversal (Jegadeesh 1990; Lehmann 1990) [A], strongest in low-turnover stocks; high-turnover stocks show 1-month momentum (Medhat and Schmeling 2022) [A]. Connors and Alvarez's tests are in-sample, stop-free, pre-publication [P]: their win rates do not transfer to a stopped 2R version; assume decay. Structural misfit: high win rate, small R vs min R:R 2.0.

### S11. Range trading between support and resistance  [most common]

- **Fit:** neutral best, risk_on fine, risk_off floor only with a tight stop. short_swing, swing.
- **Pre:** range >= 4 weeks, >= 2 reaction lows and >= 2 highs (zones `01` 6); SMA50 flat (+/- 1% over 20 bars, `01` 4.3) or ADX(14) < 20 [C]; height >= 4 x stop distance; not stage 4; prefer ranges inside a weekly uptrend or late stage 1. Lower highs inside the range = skip.
- **Geometry:** s = support zone bottom - 0.5 ATR; require (resistance zone bottom - buffer - e) >= 2 x (e - s): e must sit in the lowest ~25-30% of the range.
- **Trigger:** RC at support after a lower-volume test; limit only in a grade-A zone. **Stop:** support zone minus 0.5-1 ATR.
- **Targets:** T1 midpoint (optional), T2 below resistance; out 1/2 each. A close above resistance on RVOL >= 1.5 converts to S3/S5 as a NEW plan.
- **Clock:** median bars of prior support-to-resistance traverses; not at midpoint by then = exit. **Fail:** close below the support zone.
- **Evidence:** [C]. Limited [A]: published S/R levels interrupted intraday FX trends (Osler 2000); S/R coincides with order-book depth (Kavajecz and Odders-White 2004); round numbers acted as Dow barriers (Donaldson and Kim 1993). No rigorous test on daily stock ranges.

### S12. Wyckoff spring / failed breakdown  [underrated]

- **Fit:** risk_on/neutral or regime turning up. swing, long_swing; investment only to start a staged entry.
- **Pre:** stage 1 range after a decline with selling-climax low and automatic-rally high (`01` 5.2), >= 6 weeks; SMA200 flattening; down-swing volume shrinking.
- **Spring:** undercut of range support by <= ~1 ATR (deeper = shakeout, `03` 4.14) [C house default], back inside the same day or within 3 bars; low-volume undercut is the tell [C]; a high-volume spring needs a test (`03` 4.14). Failed-breakdown variants [C] (`03` 4.16): Turtle Soup (new 20-day low, prior low >= 4 sessions old, reclaim), undercut-and-rally of a pivot low or SMA50 inside a weekly uptrend.
- **Triggers:** aggressive: close back above support; standard: a lower-volume test holding above the spring low, then a close above the test bar's high; conservative: sign of strength (close above midpoint/AR on RVOL >= 1.5), then a quiet higher-low pullback (last point of support).
- **Stop:** spring low - 0.5 ATR (conservative: LPS low). **Targets:** T1 = AR / range top; T2 = range height added to the top [C]; no point-and-figure counts.
- **Scale:** thirds: reclaim, test, SOS/LPS or range-top break (then S6/S3 as a new plan).
- **Clock:** SOS within ~10-15 bars; back at the spring low or 20 bars in the lower half = exit.
- **Fail:** close below the spring low; second undercut on expanding volume (stage 4 continuation).
- **Evidence:** [C]/[S]: rich vocabulary, no rigorous test, subjective phases. Only with objective levels and this stop.

### S13. Post-earnings drift / earnings gap continuation  [underrated]

- **Fit:** any regime (risk_off lowers odds). short_swing, swing; long_swing until the next report. `09` 3 owns the reaction reading.
- **Pre:** confirmed results release (8-K item 2.02 via `ListFilings`, or event date) on or the evening before the gap day; true gap (open > prior high) or >= ~2 ATR move [C]; RVOL >= 2 [C]; CLV > 0 and most of the gap held; the gap clears a base or resistance (`03` 3.18), from a stock not already > 5 ATR above SMA50 (exhaustion); upstream fundamentals consistent.
- **Triggers (earliest: close of R+1, `09` 4.3):** (a) days 2-5: close above the gap-day high; (b) first pullback 2-15 bars later holding the gap-day low or gap top, then an RC; (c) gap-day AVWAP (`02` 7.10) as the (b) support. "Episodic pivot" names are this card [C].
- **Stop:** gap-day low - 0.25-0.5 ATR; if > 8%, the gap's lower edge only if well defined; full gap fill = thesis void.
- **Targets:** next resistance; blue sky: gap-day range added to the gap-day high [C] or an ATR projection, k <= 1.5.
- **Scale:** swing: 1/2 on (a)/(b), 1/2 on a later AVWAP hold; out 1/2 at T1 (`07` 6.5), trail.
- **Clock:** drift was measured over ~60 trading days (Bernard and Thomas 1989) [A]; max hold ends >= 5 sessions before the next report.
- **Fail:** close below the gap-day low within 5 bars; full fill; gap day closing in the lower third.
- **Evidence:** PEAD (Bernard and Thomas 1989) and drift after announcement returns (Chan, Jegadeesh and Lakonishok 1996) [A], reported not to reverse (Brandt, Kishore, Santa-Clara and Venkatachalam, 2008 working paper, not peer-reviewed); news drift vs no-news reversal (Chan 2003) [A]. Martineau (2022) [A]: large-stock PEAD essentially absent since about 2006, more recently gone in microcaps, as prices absorb surprises largely on the announcement day. On large caps S13 rests mainly on momentum/breakout logic; rate it lower.

### S14. Gap fill  [most common]

- **Fit:** risk_on/neutral; short_swing only. Also a TARGET for other setups: an open gap above price is resistance (use its lower edge).
- **Pre:** no-news gap DOWN in a stage 2 stock into graded support, above a rising SMA200; no 8-K, earnings or company event (Chan 2003 [A], monthly horizon; "no 8-K" does not prove "no news": market/sector news can drive gaps); gap <= ~2 ATR [C]; CLV > 0. Never fade breakaway or earnings gaps.
- **Trigger:** close above the gap-day high (days 1-3). **Stop:** gap-day low - 0.5 ATR. **Target:** prior close (partial at half fill); needs a tight stop for 2R, else reject.
- **Clock:** 5 bars. **Fail:** second gap down or close below the gap-day low.
- **Evidence:** Bulkowski [P]: common/area gaps usually close quickly (typically within about a week), breakaway gaps much later. Caporale and Plastun (2017), Plastun et al. (2020) find some abnormal post-gap moves [A limited: largely index-level, period-dependent]. "All gaps get filled" is [S].

### S15. Capitulation / oversold reversal  [high risk]

- **Fit:** short_swing only (longer types wait for S12/S6). Regime neutral, or a market washout after a follow-through up day [C]. Forbidden: stage 4 with falling SMA200 AND a news-driven drop.
- **Pre:** decline >= ~25% in 3 months or >= ~15% in 1 month [C]; close >= 3 ATR below SMA50; climax bar RVOL >= 2.5, range >= 2 ATR, new low but CLV > 0 (`03` 4.13); at weekly support; ideally a corrected former leader, not a broken company.
- **Trigger:** NOT on the climax day: (a) close above the climax high within 1-5 bars, or (b) a lower-volume test holding the climax low, then an RC.
- **Stop:** climax low - 0.5 ATR; (a) often fails 8%, (b) usually fits; neither = reject.
- **Targets:** T1 = declining EMA21/SMA20 or 38.2% retracement [C]; T2 = breakdown level or 50%; the falling SMA50 is heavy resistance. **Scale:** single entry at half risk [C, `08` 10.1]; 1/2 at T1, rest at T2.
- **Clock:** CP 5 bars, max 10-15. **Fail:** new closing low; low-volume rebound into the declining MA that rolls over.
- **Evidence:** mixed [S]. For: short-term reversal [A], larger in high volatility (Nagel 2012) [A], high-volume return premium (Gervais, Kaniel and Mingelgrin 2001) [A]. Against: volume-conditioned reversal results (Cooper 1999) [A] are not re-verified here and may cut against high-volume climaxes; news drops drift (Chan 2003) [A]; past losers rally hard but unpredictably in rebounds (Daniel and Moskowitz 2016) [A]. "Selling climax" as a rule is [C].

## 4. Setup selection decision tree

Write one line per step.

1. **Knockout** (`01` 16.1) -> reject, `plan: null`.
2. **Regime:** risk_off -> only S4-filtered S1/S2/S5 grade A, S6 with RS at new highs, S10 in leaders, S13 (lower confidence). Panic -> no trend entries; S15 short_swing, half risk.
3. **Stage:**
   - Stage 2: report 1-15 bars ago with a qualifying gap -> S13. Tight base near the 52-week high -> S3 / S5 (weekly base -> S3 weekly or S6 continuation); squeeze -> S9. Pullback to the type's MA or a breakout level -> S1 / S2; quiet 3+ day dip, RSI(2) < 5 -> S10. d beyond `01` 9.2 -> no entry now: conditional S1/S2 plan at a graded zone, or `extended`. Always test S4; failing it lowers the grade one notch.
   - Stage 1: undercut-and-reclaim -> S12; weekly breakout with volume and a turning 30-week -> S6 or weekly S7; clean range and short type -> S11; else `no_setup` with a watch condition.
   - Stage 3 -> no longs. Stage 4 -> S15 only if every precondition holds.
4. **trade_type fit** (5.2): drop "-" cards; change type only per `05` 11.
5. **Feasibility:** stop <= 8%; T1 alone >= 2R (blend is information only) and k <= 1.5 over max hold; liquidity and gap count (1.7). All fail -> reject with the code.
6. **Events** (1.7): short_swing drops any card whose hold spans a report; swing drops S9, S10, S14, S15 near a report and applies `09` 4.2 to others; S13 ends >= 5 sessions before the next report.
7. **Build** from the best remaining card: higher evidence tier, then tighter structural stop. If it fails a rule, try the next card only if independently valid; never reshape levels.

## 5. Matrices

### 5.1 Setup vs regime

| Setup | risk_on | neutral | risk_off | panic |
|---|---|---|---|---|
| S1 | yes | grade A/B | grade A leaders | no |
| S2 | yes | yes | grade A | no |
| S3 | favoured | grade A | no | no |
| S4 | favoured | yes | RS-new-high leaders | do not initiate |
| S5 | favoured | yes | leaders | no |
| S6 | yes | yes | RS at new highs | no |
| S7 | yes | expect whipsaw | no new entries | no |
| S8 | filter | filter | filter says no | filter says no |
| S9 | yes | yes | no | no |
| S10 | yes | favoured | leaders above rising SMA200 | small, leaders |
| S11 | yes | favoured | floor only, tight stop | no |
| S12 | yes | yes | if the market is also basing | no |
| S13 | yes | yes | lower confidence | no |
| S14 | yes | yes | no | no |
| S15 | rarely applies | yes | half risk | half risk, after follow-through |

### 5.2 Setup vs trade_type (P primary, ok allowed, - not used; mirrored in `05` 10)

| Setup | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| S1 | P (EMA10/21) | P (EMA21/SMA50) | ok (10-week) | ok (40-week, staged) |
| S2 | P | P | ok (weekly) | ok (weekly) |
| S3 | ok (first weeks) | P | P | ok (weekly base) |
| S4 | - | ok (filter) | P | P |
| S5 | ok | P | P | P |
| S6 | - | ok | P | P |
| S7 | - | P (20/55-day) | P (weekly) | ok (TSMOM filter) |
| S8 | filter | filter | filter | filter (10-month) |
| S9 | P | P | ok (weekly) | - |
| S10 | P | ok (prior-high target) | - | - |
| S11 | P | ok | - | - |
| S12 | ok | P | P | ok (staged start) |
| S13 | P | P | ok (until next report) | - |
| S14 | P | - | - | - |
| S15 | P (high risk) | - | - | - |

### 5.3 Setup vs volatility state (`01` 10)

| State | Favoured | Avoid |
|---|---|---|
| Contracting (ATR ratio < 0.8, squeeze) | S3, S9, S5, S12 test | S15 |
| Expanding on up bars | S13, S5, S7 | S10 (few dips), S11 (ceilings give way) [C] |
| Expanding on down bars | S15 (strict), S10 in leaders | new S3, S9, S7 |
| ATR% > 5 | usually nothing fits 8%; S2/S9 with tight structure | S6, S7, S15 |

## 6. Worked examples (hypothetical)

**Pass (S1, swing, `close`).** XYZ weekly stage 2; daily HH+HL; 52-week closing high 64.00; 7-bar pullback on declining volume to rising EMA21 at 58.40, low 58.10; ATR14 1.50 (2.6%); S4 passes. Trigger: close above prior high 59.30 -> e = 59.35 (d = 0.6). s = 58.10 - 0.75 = 57.35 (2.00 = 3.4%, passes). T1 = 64.00 - 0.30 = 63.70 (4.35 = 2.2R; reachability over the 40-bar max hold k = 4.35 / (0.63 x 1.50 x 6.32) = 0.73). e_max = (63.70 + 114.70) / 3 = 59.4667 -> 59.46. All at once; 1/2 at T1, rest trailed under EMA21 - 0.5 ATR. CP1 bar 10 (close >= 60.35), CP2 bar 20 (>= 61.35 or above 64.00), max hold bar 40; no report inside.

**Reject (S10, short_swing).** RSI(2) = 3 above a rising SMA200; SMA5 target 1.8 ATR above e, structural stop 1.5 ATR below = 1.2R; prior swing high 2.5 ATR above = 1.7R. Reject `target_too_close`; watch: a dip into the rising SMA50 zone.

## 7. Rejecting when no setup qualifies

One code, the closest setup and what would make it qualify, in one line.

| Code | When | Output |
|---|---|---|
| `no_setup` | no card's preconditions hold | `plan: null`; "watch: <condition>" |
| `extended` | stage 2 beyond `01` 9.2, no S1/S2 zone in reach | null, or a conditional plan at a graded zone |
| `stop_too_wide` | chart stop > 8% (S6, S7, S15, deep cups) | levels, `max_loss` reject |
| `target_too_close` | resistance < 2R (S10, S14, S1 under supply) | levels, `reward_to_risk` reject |
| `regime` | card not allowed (5.1) | null or levels with regime noted |
| `event` | report inside a hold that forbids it | per `09` 4.1 |
| `liquidity_gaps` | < $5M dollar volume or >= 3 stop-skipping gaps | null |
| `conflict` | higher timeframe contradicts the entry setup | null |

A pending plan (price below the trigger) is not a reject. Rejecting a good company on chart grounds is correct.

## 8. Combining setups without double counting

- **One primary setup** supplies entry, stop, target and clocks; others are factors only.
- **Same-information groups count once** (`02` 8): {S4, S5, S7, S8, price above rising MAs, trend template} = one trend factor; {S9, NR7, VCP tightening, 3WT} = one volatility factor; {S10, S11, S14, S15} = one mean-reversion view.
- **Independent confirmations** (once each): trend, volume/accumulation, location (breakout level + rising MA + AVWAP at one zone = ONE stronger level), event (S13), regime. Two agreeing groups raise confidence modestly; five indicators from one group do not.
- **No family mixing:** do not exit a trend entry on a mean-reversion signal (RSI(2) > 90), or keep a mean-reversion entry as a trend trade past its target without a new plan.
- **Conflicts:** higher timeframe wins (`01` 13): a daily S10 buy under weekly stage 3/4 is rejected; a daily S11 range inside weekly stage 2 is a base, and its breakout (S3) is the better trade.
- **Upgrades are new plans:** S11 break up -> S3/S5; S12 range-top break -> S6/S3; S2 after S3 = an add under the original stop logic. Never silently move the old target.

## 9. Shorts: mirror notes (only if `allow_short: true`)

- Mirrors: S1 -> rally to a falling EMA21/SMA50 in stage 4; S2 -> retest of broken support from below; S3/S5 -> breakdown from a top or below the 52-week low; S6 -> stage 4 break below a rolling-over 30-week; S7 -> 20/55-day low; S12 -> upthrust after distribution; S13 -> negative gap continuation (bad-news drift was strong in Chan 2003 [A]).
- Risks: unbounded news gaps; squeezes (short interest if available); borrow cost and recalls; momentum-crash rebounds hit shorts of past losers hardest (Daniel and Moskowitz 2016) [A]. short_swing/swing only, regime risk_off or neutral. Never mirror S10 or S15.

## Sources

Looked up for this file:
- Wilcox and Crittenden (2005), "Does Trend Following Work on Stocks?", Blackstar Funds. https://www.cis.upenn.edu/~mkearns/finread/trend.pdf
- Zarattini, Pagani and Wilcox (2025), "Does Trend-Following Still Work on Stocks?", SSRN 5084316. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5084316 (figures as summarised in https://quantpedia.com/strategies/trend-following-effect-in-stocks and https://concretumgroup.com/does-trend-following-still-work-on-stocks/)
- Turtle rules. https://oxfordstrat.com/coasdfASD32/uploads/2016/01/turtle-rules.pdf ; https://www.theturtletrader.com/turtle-trading-rules/
- Connors and Alvarez (2008), Short Term Trading Strategies That Work; RSI(2): https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2
- Minervini trend template and VCP: https://www.chartmill.com/trading-ideas/645-Mark-Minervinis-Trend-Template-TTP ; https://traderlion.com/technical-analysis/volatility-contraction-pattern/
- O'Neil rules (5% of pivot, 7-8% loss cut, 20-25% profit, 8-week hold): https://traderlion.com/trading-strategies/the-8-week-hold-rule/ ; cup with handle: https://www.luxalgo.com/library/concept/cup with handle-base/
- Weinstein stage analysis: https://traderlion.com/trading-strategies/stage-analysis/
- Bollinger squeeze: https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/bollinger-band-squeeze ; TTM squeeze: https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/ttm-squeeze
- Bulkowski: throwbacks https://thepatternsite.com/throwbacks.html ; gaps https://thepatternsite.com/GaugingGaps.html , https://thepatternsite.com/gaps.html
- Wyckoff method: https://www.wyckoffanalytics.com/wyckoff-method/
- Chan (2003), JFE 70, 223-260. https://ideas.repec.org/a/eee/jfinec/v70y2003i2p223-260.html
- Bernard and Thomas (1989), JAR 27, 1-36. https://ideas.repec.org/a/bla/joares/v27y1989ip1-36.html
- Brandt, Kishore, Santa-Clara and Venkatachalam (2008 working paper), "Earnings Announcements are Full of Surprises". https://www.anderson.ucla.edu/documents/areas/fac/finance/ear.pdf
- Martineau (2022), "Rest in Peace Post-Earnings Announcement Drift", Critical Finance Review 11. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607
- Cooper (1999), RFS 12, 901-935. https://academic.oup.com/rfs/article-abstract/12/4/901/1580996
- Nagel (2012), "Evaporating Liquidity", RFS 25(7). https://www.nber.org/papers/w17653
- Medhat and Schmeling (2022), "Short-term Momentum", RFS 35(3). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3150525
- George and Hwang (2004), "The 52-Week High and Momentum Investing", JF 59(5). https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf
- Caporale and Plastun (2017) https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2850057 ; Plastun et al. (2020) https://ideas.repec.org/a/eee/ecofin/v52y2020ics1062940820300747.html

Standard references (not re-fetched; qualitative findings as described in the cards): Chan, Jegadeesh and Lakonishok (1996, JF); Jegadeesh and Titman (1993, JF); Jegadeesh (1990, JF); Lehmann (1990, QJE); Moskowitz, Ooi and Pedersen (2012, JFE); Moskowitz and Grinblatt (1999, JF); Novy-Marx (2012, JFE); Da, Gurun and Warachka (2014, RFS); Daniel and Moskowitz (2016, JFE); Cooper, Gutierrez and Hameed (2004, JF); Lee and Swaminathan (2000, JF); Gervais, Kaniel and Mingelgrin (2001, JF); Brock, Lakonishok and LeBaron (1992, JF); Sullivan, Timmermann and White (1999, JF); Park and Irwin (2007, J. Economic Surveys); Zakamulin (2017); Marshall, Nguyen and Visaltanachoti (2017, Quantitative Finance); Han, Yang and Zhou (2013, JFQA); Faber (2007, J. Wealth Management); Lo, Mamaysky and Wang (2000, JF); Osler (2000, FRBNY EPR); Kavajecz and Odders-White (2004, RFS); Donaldson and Kim (1993, J. Financial Research); Crabel (1990). Practitioner conventions: LeBeau (chandelier); Connors and Raschke (1995), Street Smarts (Turtle Soup, Holy Grail); Morales and Kacher (2010) (pocket pivot); O'Neil, How to Make Money in Stocks; Minervini, Trade Like a Stock Market Wizard; Weinstein, Secrets for Profiting in Bull and Bear Markets; Bollinger, Bollinger on Bollinger Bands; Carter, Mastering the Trade; Faith, Way of the Turtle; Edwards and Magee.
