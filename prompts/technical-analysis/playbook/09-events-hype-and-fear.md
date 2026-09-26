# 09 - Events, hype and fear

## How to use this file

- Use it whenever a dated event (earnings, a filing, an FDA date, an index change, a lock-up, a macro release) falls inside the planned hold, sits in the last ~60 sessions of the chart, or a bar looks climactic (hype) or capitulating (fear).
- Order of work: 2 (dates, gap-risk numbers), 3 (read the last reaction), 7 or 8 if the chart is extended or washed out, then the per-trade_type rules in 4, 12 (execution and time limits) and the checklist in 13.
- Every rule needs only daily OHLCV plus an event date. Options, VIX, put/call, short interest only sharpen a reading "if available" from an upstream folder; never fetch them yourself, never use remembered facts about a company or a past event.
- Labels: [A] academic, [P] practitioner study, [C] convention, [S] speculative or contested. "House default" = this playbook's convention, not a published result.
- Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).
- Neighbours: gap anatomy `03-chart-patterns.md` 5 and gap-and-go 3.18; setups S13 (earnings gap continuation), S14 (gap fill), S15 (capitulation) in `04-strategies-and-setups.md`; gaps at the open `06-entries.md` 7, entries around reports `06` 11; event exits `07-exits.md` 12; per-type summary `05-timeframes-and-trade-types.md` 8, fill ceiling `05` 7.5; event timeline `08-trade-plan-and-timeline.md` 7, sizing `08` 10.1; extension thresholds `01-chart-reading.md` 9.2, regime `01` 12. This file owns event reading; neighbours set the matching entry/exit rules.

## 1. Evidence ledger

| Finding | Label | Plan meaning |
|---|---|---|
| Post-earnings-announcement drift (PEAD): prices keep moving in the direction of the surprise for roughly 60 trading days (Ball and Brown 1968; Bernard and Thomas 1989) | [A] | Trade with a strong reaction, not against it. |
| Drift also follows the price reaction itself (Chan, Jegadeesh and Lakonishok 1996); the 3-day announcement return (EAR) drift is reported not to reverse (Brandt, Kishore, Santa-Clara and Venkatachalam 2008, working paper) | [A] (CJL); no-reversal detail = working paper | The reaction is the chart agent's surprise measure. |
| PEAD has weakened sharply: essentially absent in large caps since the mid-2000s, later fading in microcaps (Martineau 2022; others with different surprise measures report residual drift); drift concentrates in illiquid stocks where costs eat much of it (Chordia, Goyal, Sadka, Sadka and Shivakumar 2009) | [A], extent contested | Large caps: post-report continuation = momentum/breakout logic, not guaranteed drift. |
| More drift when attention is low: Friday announcements (DellaVigna and Pollet 2009), crowded announcement days (Hirshleifer, Lim and Teoh 2009) | [A] | Minor tilt. |
| Earnings announcement premium: higher average returns in announcement windows (Frazzini and Lamont 2007; Barber, De George, Lehavy and Trueman 2013; Savor and Wilson 2016) | [A] | Portfolio average; no reason to hold one tight-stop position through a report (6). |
| Past winners earn positive abnormal returns just before earnings and negative ones after (Aboody, Lehavy and Trueman 2010) | [A] | Academic form of "buy the rumor, sell the news". |
| High-expectation growth stocks react much more to negative than to positive surprises (Skinner and Sloan 2002) | [A] | Hyped stocks carry asymmetric report risk. |
| Big moves WITH news drift; WITHOUT news reverse (Chan 2003; Savor 2012); stale re-reported news reverses (Tetlock 2011) | [A] | The cause of a gap decides follow vs fade. |
| Horizon effects: short-term reversal (Jegadeesh 1990; Lehmann 1990; weaker in high-turnover stocks, Medhat and Schmeling 2022; larger in high volatility, Nagel 2012); 3-12 month momentum (Jegadeesh and Titman 1993; Moskowitz, Ooi and Pedersen 2012; weaker for jumpy paths, Da, Gurun and Warachka 2014; crashes in rebounds, Daniel and Moskowitz 2016); 3-5 year reversal (De Bondt and Thaler 1985); high-volume return premium (Gervais, Kaniel and Mingelgrin 2001; volume-conditioned reversal results differ, Cooper 1999: no rule); bubble crash odds (Greenwood, Shleifer and You 2019); sentiment (Baker and Wurgler 2006) | [A] | Reconciled by horizon in section 11; hype and fear use them in 7-8. |
| Heavily shorted stocks underperform on average, mainly where short-sale constraints bind (Asquith, Pathak and Ritter 2005); lightly shorted ones earn positive abnormal returns (Boehmer, Huszar and Jordan 2010) | [A] | High short interest is bearish on average; squeezes are violent exceptions [S]. |
| Gap types and gap fills (Bulkowski [P]; Caporale and Plastun 2017 [A], index-level); non-fundamental part of earnings gaps (Ben-Rephael et al. [S], working paper); "all gaps get filled" [S] | mixed | Section 3.4: fade only no-news common gaps. |
| Climax top, exhaustion gap, selling climax, "bad news priced in" (O'Neil, Wyckoff, Edwards and Magee) | [C] | Use only with the objective criteria below and a confirming bar. |

Event-specific evidence (offerings, analysts, M&A, index changes, lock-ups, macro) sits in sections 9-10.

## 2. Event calendar and gap-risk measurement

### 2.1 Dates and causes (point in time)

| Item | Source | Rule |
|---|---|---|
| Next earnings | deep dive `next_earnings`; else `GetUpcomingInvestorEvents`; else estimate from 8-K item 2.02 dates (`ListFilings`): same fiscal quarter last year, marked "estimated" (`08` 7.1) | Estimated: treat +-7 calendar days as the event [C]. A confirmed date later than last year's pattern is a mild negative signal (Johnson and So 2018) [A]; earlier than usual, mildly positive. |
| Past results dates | 8-K 2.02 filing dates | Locate reaction days; a filing counts from the day after it is filed (shared.md). |
| Investor day, product event, conference | `GetUpcomingInvestorEvents` | Small earnings event for short_swing/swing. |
| FDA dates, index changes, IPO/lock-up dates, macro calendar, short interest, put/call, VIX, option chains | upstream folder only | Else `NOT CHECKED: <what> (not in technical tools)`. Never from memory. |

Filings that name a gap's cause (name a cause only if filed on or just before the gap day):

| Filing | Meaning | Read |
|---|---|---|
| 8-K 2.02 | results | reaction classes (3) |
| 8-K 7.01 / 8.01 | Reg FD / other (guidance, pre-announcements, trial data) | read like earnings |
| 8-K 1.01, 2.01; SC TO-T, SC 14D9, DEFM14A, 425 | agreement, acquisition, tender, merger proxy | M&A (9) |
| 424B*, S-1, S-3, 8-K 3.02 | prospectus / registration / unregistered sale | dilution, usually bearish [A] |
| 8-K 4.02 | non-reliance (restatement) | strongly bearish [A]; no longs |
| 8-K 4.01; 5.02 | auditor change; officer departure | caution [C] (abrupt CEO/CFO exit) |
| 8-K 2.05 / 2.06 | restructuring / impairment | often priced in if the chart already fell [C] |
| NT 10-K / NT 10-Q | late filing notice | red flag [C]; no new long until the filing arrives |
| 8-K 3.01; 1.03 | delisting notice; bankruptcy | no longs |
| SC 13D (or SCHEDULE 13D) | activist/control stake | gap up, follow-through risk both ways [C] |

### 2.2 Reaction day and per-event numbers (last 4-8 reports)

R = reaction day: release before the open or intraday -> release date; after the close -> next session. Timing unknown: compute both, use the larger absolute close-to-close move, say so. P = R - 1.

| Measure | Formula (daily bars) | Use |
|---|---|---|
| Open gap | G% = O_R / C_P - 1; ATR units (O_R - C_P) / ATR14_P | the jump no stop controls |
| True gap (window) | up L_R > H_P; down H_R < L_P | unfilled window = support/resistance |
| Reaction | ER1% = C_R / C_P - 1; ER1_ATR = (C_R - C_P) / ATR14_P | day-1 verdict |
| EAR (3-day) | C_{R+1} / C_{R-2} - 1 minus SPY's same window | surprise proxy (Brandt et al. use a matched benchmark; SPY simplifies) [A] |
| Gap retention | GR = (C_R - C_P) / (O_R - C_P), if abs(O_R - C_P) >= 0.25 ATR | > 1 extended; 0.5-1 held; 0-0.5 faded; < 0 reversed |
| Close location | CLV_R = ((C - L) - (H - C)) / (H - L) | +1 at high, -1 at low |
| Volume | RVOL_R = V_R / mean(V, 50 sessions before P) | participation |
| Excess reaction | ER1 - beta_proxy x SPY return on R (beta_proxy = 1 unless computed from 250 daily returns) | strips market gaps (10) |
| Historical move | HEM = median abs(ER1%); HEMmax = largest adverse abs(ER1%) or abs(G%) (down for a long); if < 2 reports moved adversely, the largest abs move of either sign | the stock's own "implied move" |
| Pre-event run-up | RU20 = C_P / C_{P-20} - 1; RU20_ATR = (C_P - C_{P-20}) / ATR14_P; also RU5 | anticipation (5) |

If an upstream option chain exists: implied move ~= ATM straddle for the first expiry after the event / price [C] (it also holds non-event time value, so it overstates the event part for longer expiries; the event component can be isolated from the IV term structure, Dubinsky, Johannes, Kaeck and Seeger 2019 [A]). Use it in place of HEM for magnitude and say which. A reaction smaller than the implied move is a non-event for magnitude.

### 2.3 Gap-risk test (any plan holding through an event)

- D% = (C_now - stop) / C_now. Gap risk is material when HEM > D% [C]. When HEMmax > D%, the realised loss can exceed `max_loss_per_trade_pct`: write it in Risks.
- Worst plausible loss: WL% = (e - C_now x (1 - HEMmax)) / e. `level_trigger: close`: the stop is acted on at the gap day's close (worse or better than the open); `intraday`: a resting stop becomes a market order and fills at or through the gap (SEC bulletin) [C].
- Fewer than 4 past reports: HEM unknown; apply the strictest rule for the trade_type.

## 3. Reading an earnings (or other news) reaction

### 3.1 Reaction classes (day R, confirmed over R+1..R+5)

| Class | Day-R criteria (all) | Follow-through test | Read | Label |
|---|---|---|---|---|
| U1 Strong acceptance | gap up >= max(1 ATR14_P, 0.5 x HEM x C_P); CLV >= +0.5; GR >= 0.75; RVOL >= 2; close above the pre-event base high or nearest resistance | no close below the gap-day low in R+1..R+5; window unfilled | continuation candidate (S13; "episodic pivot") | [A] direction; [C] thresholds |
| U2 Held but tired | gap up; CLV -0.2 to +0.5; GR 0.3-0.75 | holds the gap midpoint 3-5 closes | wait for a post-event base (4.4) | [C] |
| U3 Sell the news | gap up >= 1 ATR; CLV < 0 or GR < 0.3; RVOL >= 2 | close below the gap-day low or C_P within 5 sessions confirms | distribution into good news; no entry; holders scale out | [C]; [A] Aboody et al. for pre-run winners |
| U4 Bearish key reversal | new high above pre-event highs, then C_R < C_P, RVOL >= 1.5 | next close below L_R | strong distribution; exit cue | [C] |
| M Muted | abs(ER1%) < 0.5 x HEM and RVOL < 1.5 | n/a | non-event; prior chart governs | [C] |
| D1 Gap down and held | gap down >= 1 ATR; CLV <= -0.3; RVOL >= 2 | no close above the gap-day high in R+1..R+5 | negative drift likely; no longs 4-8 weeks; holders exit | [A] drift; [C] timing |
| D2 Washout | gap down >= 1 ATR (often >= 2); CLV >= +0.3 or C_R > O_R; GR <= 0.5; RVOL >= 2 | no new closing low in R+1..R+10; higher low; volume falls | sellers exhausted; watch-list, buy only on confirmation (8.3) | [C]; news drops still drift (Chan 2003) [A] |
| D3 Bullish key reversal | new low below pre-event lows, then C_R > C_P, RVOL >= 2 | next close above H_R | strongest washout form | [C] |

Thresholds are house defaults [C]; scale "large" with the stock's own HEM (1 ATR is large for a utility, routine for a volatile growth stock). Day R+1 matters as much as day R: a U1 that closes R+1 below the gap midpoint is downgraded to U2; a D2 that makes a new low on R+1 is D1.

### 3.2 Good news, bad price; bad news, good price

- Upstream states the result (beat/miss, guidance): "good" news + U3/U4/D1 = the market expected more or holders are distributing; the next ~4-8 weeks favour weakness [C] (consistent with drift following the price, not the headline [A]). "Bad" news + D2/D3 or an up day = washed out, bad news was expected [C].
- No upstream verdict: the price reaction IS the surprise (EAR logic [A]). Never infer the news from the move; describe it by date and size (shared.md).

### 3.3 Follow-through ladder

| Days | Continuation evidence | Failure evidence |
|---|---|---|
| R+1 | inside day or higher close above the gap midpoint; RVOL >= 1.2 | close below the gap midpoint |
| R+2..R+5 | no close below the gap-day low; pullback volume below the 50-day average | close below the gap-day low (S13 fail); window filled |
| R+5..R+15 | tight range (daily range < 0.7 ATR most days) above the gap; AVWAP from R rising and held | close below AVWAP from R and the window |
| R+15..R+60 | new highs above the gap-day high; RS vs SPY and sector rising | full retrace to C_P: reaction void, read the chart as before |

AVWAP from R (daily typical price x volume, `02-indicators.md` AVWAP) = gap buyers' average cost [C]; a close below it after R+5 weakens continuation.

### 3.4 Gap-and-go versus gap-fill

| Gap context | Tendency | Label | Plan |
|---|---|---|---|
| Earnings/8-K news, U1 or D1, high RVOL | continuation over weeks | [A] PEAD/EAR, Chan 2003 | trade with it (long only if up); never fade |
| News gap closing weak (U3/U4) or strong (D2/D3) | the close beats the headline | [C] | follow the close, not the open |
| No-news gap <= ~2 ATR inside a range | partial/full fill within days common | [P] Bulkowski; [A] no-news reversal (monthly horizon, not gap-specific) | S14 only, stage 2 into support |
| Gap after an extended run on the move's largest volume | exhaustion if filled within ~5 sessions | [P]/[C] | holders scale out |
| Market-wide gap | stock gap ~= beta x SPY gap, no stock news | [C] | judge the excess (10) |
| Peer's report gaps this stock (no own filing) | sympathy move, partial information | [A] (9, Thomas and Zhang) | not an own-earnings reaction; re-read at the stock's own report |
| Huge gap (several x HEM) | part may revert long-run | [S] | targets from structure, not "gap doubled" |

## 4. Earnings rules per trade_type

### 4.1 Before the report

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Report inside hold (entry to max hold + 2 sessions) | not allowed: max hold ends >= 1 session before, or reject | no new entry in the last 10 sessions (`06` 11); earlier entries state exit / halve / cushion rule | expected; name each report and the action | expected; name every report in year 1 and a review after each |
| Entry before report | no | no (last 10 sessions) | pilot <= 1/3 | first tranche; next after the report; no add in the last ~10 sessions |
| Run-up (RU20 >= 3 ATR or >= own 90th percentile of 20-day returns over 2 years) | n/a | stronger case to exit before | trim 1/4-1/3 before [C]; Aboody et al. [A] | Risks note; trim only if climactic (7) |
| Resting orders | none open across the report | cancel resting entry orders the session before (12) | same | same |
| Role flag | `upcoming_earnings` 45 days | same | 45 or 30 days by pipeline horizon | 30 days |

### 4.2 Hold-through decision (cushion rule)

For a swing or long_swing position open when a report approaches (investment: step 5 only):

1. Open profit in R: OP = (C_now - e) / (e - s).
2. Cushion test: OP >= 1.0 AND the stop can be raised to >= entry (s' >= e) AND HEM < (C_now - s') / C_now. All pass -> hold full size with s'.
3. Partial (OP >= 0.5, or only the HEM test fails) -> halve at the last close before the release; keep the rest with s' >= e if possible.
4. Fail (OP < 0.5, or s' cannot reach e) -> swing: exit at the last close before. long_swing: halve; hold the rest only if the thesis is weekly-chart based and WL% is in Risks.
5. investment: hold; if HEMmax > stop distance, say realised loss can exceed `max_loss` and lower confidence.

Timing: release after the close on T -> act at T's close; before the open on T -> at T - 1's close (`07` 12). [C]: gap risk is mechanical; 1R is a house default.

### 4.3 After the report

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Earliest entry | close of R+1 | same | first weekly close after R | first weekly close after R above the pre-report level |
| Setup | S13 (a) close above gap-day high in R+2..R+5, or (b) first pullback holding the gap-day low | post-earnings base (4.4) or S13 (b) | weekly base 2-6 weeks after | stage 2 continuation after a report-driven weekly breakout |
| Stop | gap-day low - 0.25-0.5 ATR | base low or gap-day low | weekly base low or the window | weekly structure; window = warning line |
| Holder after U1 | trail to prior 2-day low | trail to gap-day low; drift favours holding [A] | stop below the window | none; note new support |
| Holder after U3/U4 | exit next close | sell 1/2; rest out on a close below the gap-day low | trim 1/3; out on a weekly close below the window | thesis review; no add |
| Holder after D1 | stop already gone | exit (gapped stop = exit at the close with `close`) | exit or reduce to a review stub | review with upstream; exit on weekly structure break |
| Max hold | before the next report | >= 5 sessions before the next report | name the next report and action | name each report |

Why "let it report" [C]: the next report is ~60 sessions away, that window matches the measured drift [A], and day R supplies clean levels (window edges, R high/low, AVWAP from R).

### 4.4 The post-earnings base

- Definition (house default [C]): after U1/U2, 3-15 sessions (short_swing/swing) or 2-6 weeks (long_swing) of consolidation with the low above the gap midpoint, depth <= ~2.5 daily ATR (or <= ~2 weekly ATR), volume drying up (most bars RVOL < 1).
- Trigger: close above the base high, RVOL >= 1.5 (`06`). Stop: below the base low (or below the window if the base low is in noise).
- Invalid: a close into the window, a close below the gap-day low, or a report inside the remaining hold. Expiry: no trigger by R+20 (swing) or R+8 weeks (long_swing) -> the event edge is spent; read it as an ordinary base [C].

## 5. "Buy the rumor, sell the news" (and its fear mirror)

### 5.1 Anatomy on daily bars

| Phase | Criteria | Read |
|---|---|---|
| Run-up | RU20 >= 3 ATR or >= own 90th percentile; >= 3 of the last 5 closes up; at/near a 52-week high; RVOL rising into the date | anticipation being bought [C]; pre-announcement gains of past winners [A] |
| Event day | U3 fade or U4 reversal on the run's heaviest volume | holders sell to late buyers [C] |
| Aftermath | lower high within 5-15 sessions; close below the pre-event breakout level | distribution confirmed; run-up given back [C]; negative post-announcement returns for past winners [A] |

Applies to earnings, product launches, investor days and conferences (no robust study for non-earnings events [C]/[S]), FDA/trial dates (binary, either direction), index inclusion (9). Event-type rules: section 9.

### 5.2 Rules

- Known event inside the hold and RU20 >= 3 ATR: short_swing/swing exit (or at least halve) at the last close before; long_swing trim 1/4-1/3; investment note only [C].
- No new long during a run-up into a dated event; the post-event chart supplies the entry (4.3) [C].
- U3/U4 after a run-up: holders sell >= 1/2 at R's close or R+1; the rest on a close below the gap-day low or the pre-event breakout level [C].
- A pre-event run-up that stalls before the date (RU5 <= 0 with RU20 >= 3 ATR) = sellers front-running: tighten before the event [C].

### 5.3 Fear mirror: "sell the rumor, buy the news"

- Pattern [C]: the stock falls into a feared dated event (report after a warning, ruling, trial, FDA date): RU20_ATR <= -3, closes near lows. When the event resolves, bad-but-expected news gives D2/D3 or an up day (uncertainty removed, shorts cover).
- Rules: never buy before the event; after it, only a D2/D3 with the 8.3 confirmation. If the reaction is D1 (gap held down), the fear was justified: news-driven drift [A] (Chan 2003); no long.

## 6. Announcement premium versus gap risk; sizing for the gap

- The small average announcement premium [A] is a diversified-portfolio average with huge per-stock variance. For one position with a stop 1-2 HEM away, the report is mainly a jump risk the stop cannot control; the premium never justifies holding a short_swing or an un-cushioned swing through a report [C].
- If a plan does hold through (long_swing, investment, cushioned swing), the human should size for the gap, not the stop [C] (`08` 10.1 gap allowance): per-share risk for sizing = max(e - s, e - C_now x (1 - HEMmax)). State both numbers; never tighten the stop to compensate.

## 7. Hype: reading and handling excess

### 7.1 Hype signs (computable)

| Sign | Criteria (daily unless stated) | Label |
|---|---|---|
| Extension from the average | d = (C - MA) / ATR14 beyond the "climactic" column of `01` 9.2: short_swing d20 > 4 or 5-day gain > 4 ATR; swing d50 > 7; long_swing > 4 weekly ATRs above the 10-week SMA | [C] house default |
| Far above the 200-day / 40-week | 70-100%+ above (O'Neil climax-top criterion) | [C] |
| Parabolic acceleration | each of the last 3 swing legs steeper (gain per bar in ATR) than the one before; ROC10 > ROC10 of 10 bars ago > 0; log price curving up | [A] industry level (Greenwood et al.); [C] single stock |
| Consecutive gaps up | >= 3 true gaps up in 10 sessions | [C] |
| Up-day streak | 7 of 8 or 8 of 10 up closes | [C] O'Neil |
| Largest up day of the move | biggest one-day gain since the advance began, late in it | [C] O'Neil |
| Climactic volume / churning | highest volume of the advance (RVOL >= 3) with the widest range; or RVOL >= 2 with close change < 0.3 ATR | [C] Wyckoff/O'Neil |
| Exhaustion gap | gap up with d50 > 5, RVOL >= 2, filled within ~5 sessions | [P]/[C] |
| Key/outside reversal at highs | new high, close below prior close (or engulfing), CLV < -0.3, RVOL >= 1.5 | [C] |
| Oscillator extremes | RSI(14) (Wilder) daily or weekly > 80; closes above the upper Bollinger band (20, 2 population SD) 5+ of 8 sessions with bandwidth at a 1-year high | [C]; RSI > 70 is normal in uptrends and "walking the band" is strength (`02`): count only alongside other signs |
| Squeeze profile | vertical move, multiple gaps, RVOL >= 5 without a results filing, in a stock flagged upstream as heavily shorted | [S]; heavily shorted stocks underperform on average [A] |
| Supply into strength | offering filing (424B*, S-3, 3.02), lock-up expiry, or large insider sales (upstream) during the run | [A] issuance raises crash odds (Greenwood et al.); SEO underperformance (Loughran and Ritter 1995) |
| Sentiment extremes (upstream) | equity put/call at multi-month lows; option volume surging; short interest collapsing after a squeeze | [C]/[S]: public put/call as a contrarian gauge is weakly supported; stock-level put/call from non-public opening trades predicts in the SAME direction, and public ratios carried little of it (Pan and Poteshman 2006) [A] |

Hype score = count of rows present (max 1 each). 0-1 normal trend; 2-3 extended: no new entries; >= 4 climactic: holders act (7.2). House default [C]. Hype in a speculative name (small, young, unprofitable, volatile) counts one extra point (Baker and Wurgler 2006 [A] direction; the point is [C]).

### 7.2 Exiting and scaling out into hype

Sell into strength: on up days at or above the prior high (a limit for the human), not after the first down day [C] (Minervini, O'Neil). Hype is not a reason to reject a trend or short: run-ups do not reliably predict negative average returns [A] and momentum persists [A].

| Hype score | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| 2-3 | trail to the prior 2-day low; take T1 early if within 0.5 ATR | 1/3 at T1 or into the next up day; trail rest to EMA10/SMA20 close | trail to the 10-week SMA close | none |
| >= 4 | exit into the next up open or on the first close below the prior day's low | sell 1/2 into strength; trail rest to the prior 2-day low; exit on a key reversal or exhaustion-gap fill | sell 1/4-1/3; trail rest to the prior weekly low | trim only on weekly climax (>= 70% above the 40-week, widest weekly range and volume of the run); keep the core |
| Confirmed reversal (key reversal + next close below its low, or exhaustion gap filled) | out | exit remainder | exit to a core, or fully on a weekly close below the prior weekly low | trim further; full exit only on weekly structure break (`07`) |

Scale-out math and trails: `07-exits.md`. With a report ahead AND hype >= 2, apply 5.2 before 4.2 (a hyped stock's downside reaction is the larger one [A] Skinner and Sloan).

### 7.3 Hype and new entries; squeezes

- No new long at hype score >= 2 (extended entry, wide stop); wait for a pullback to the reference MA or a new base (`06`).
- After a climax top, a first rebound to the prior high on lower volume is a lower-high risk, not a buy [C].
- Holding a stock that turns into a squeeze: treat it as hype >= 4 at once and sell into the vertical bars; squeezes typically end with a key reversal or a gap fill and round-trip toward the pre-squeeze base [S]. No longs after the collapse until a new base forms.

## 8. Fear: reading and buying it safely

### 8.1 Fear signs (computable)

| Sign | Criteria | Label |
|---|---|---|
| Extent of decline | >= 25% in 3 months or >= 15% in 1 month; close >= 3 ATR below SMA50 (S15) | [C] house default |
| Capitulation / selling climax bar | RVOL >= 2.5-3, range >= 2 ATR, new low of the decline, CLV > 0 | [C] Wyckoff; [A] high-volume premium weakly supportive |
| Gap-down reversal | gap down >= 1 ATR, close above the open with CLV >= +0.3 (D2) or above the prior close (D3) | [C] |
| Waterfall | >= 3 gaps down in 10 sessions, closes near lows | [C]; still falling until a reversal bar |
| Oscillator extremes | RSI(14) < 20-25; RSI(2) < 5; 3+ closes below the lower Bollinger band | [C]; oversold stays oversold. Connors' RSI(2) tests [P] were for stocks ABOVE their SMA200; below it the reading is only [C] |
| Washout / priced in | after bad news, no new closing low for 5-10 sessions, falling volume, a higher low | [C] |
| Weekly climax | largest weekly volume in 1-2 years, weekly close in the upper half | [C] |
| Market fear (upstream) | VIX far above its 20-day average or at a multi-month high; SPY d50 <= -4 with several gaps down; equity put/call at multi-month highs | [C]; reversal pays more in high volatility (Nagel 2012) [A] |

### 8.2 Is the fear news-driven?

| Cause | Evidence | Action |
|---|---|---|
| Stock-specific fundamental news (results, guidance cut, 4.02, downgrade), gap held (D1) | drift continues [A] (Chan 2003; PEAD; Womack 1996) | no long 4-8 weeks; wait for a base and RS improvement |
| No filing or event; liquidity or sector-wide drop | reversal more likely [A] (Chan 2003; Jegadeesh 1990) | S15 eligible (short_swing) with confirmation |
| Market-wide selloff (small excess move) | leaders often recover first once the market turns [C] | buy only after the market follow-through day (`06` 5) [C] |
| Dilution (424B*, S-3, 3.02) | announcement drop plus long-run underperformance [A] | no long for ~5 sessions; later only if price reclaims the pre-deal close on volume and holds the offer-price area |

"No filing" does not prove "no news" (sector or macro news moves stocks too): the no-news branch also needs the sector ETF not to have fallen similarly.

### 8.3 How to buy fear safely

1. Never buy the climax/gap day. Require (a) a close above the climax (or R) high within 1-5 sessions; or (b) a secondary test holding above the climax low on lower volume, then a reversal close; or (c) weekly types: a weekly close above the prior week's high after a weekly climax [C] (S15).
2. Stop below the climax low - 0.5 ATR (daily) or the weekly low; if > `max_loss_per_trade_pct`, use (b) with the stop below the test low - 0.25-0.5 ATR, or reject. Never widen.
3. Half risk (house default [C]; `08` 10.1).
4. Targets: partial at the declining SMA20/EMA21 or the gap edge above; plan target (for R:R) at the breakdown level, the declining SMA50 or the 50% retracement [C]. R:R >= 2 often fails on day 1; waiting for (b) usually fixes it.
5. Time stop: no progress in 5 sessions; max 10-15 (short_swing). A D2/D3 watch-list entry expires if no trigger by R+10.

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Buy fear? | yes: S15 with confirmation, half risk | only a stage 2 stock correcting on market-wide fear, after the market follow-through, RS holding | not on fear alone; wait for a weekly base (4-12 weeks) and a weekly higher low | pilot at multi-year weekly support after a weekly reversal bar if upstream fundamentals are intact; add only on a stage 1 -> 2 breakout; long-horizon reversal supports patience [A] |
| Forbidden | stage 4 with falling SMA200 AND news-driven drop | D1 news gaps within 20 sessions | stage 4 | 8-K 4.02, 3.01, 1.03, going-concern flags upstream |

## 9. Event and news types

| Event | Detect | Typical chart behaviour | Evidence | Long-plan rule |
|---|---|---|---|---|
| Earnings / guidance | 8-K 2.02, 7.01 | classes in 3 | [A] PEAD/EAR | section 4 |
| Earnings date moved | confirmed date vs last year's | later than usual precedes worse news | [A] Johnson and So 2018 | later date: lower confidence, no pre-report pilot |
| Peer / sector report | peers' dates upstream; sector ETF gap on a day with no own filing | sympathy gap; late reporters' reaction to early peers tends to be an overreaction, partly reversed at their own report | [A] Thomas and Zhang 2008 | no S13 on a sympathy gap; treat peer dates in the hold as small events for short_swing |
| Analyst upgrade | upstream | small gap, short drift | [A] Womack 1996 | not a setup |
| Analyst downgrade | upstream | gap down, drift lasting months | [A] Womack 1996 | no long ~1-2 months unless D2/D3 plus a base |
| M&A target | 8-K 1.01, SC TO-T, DEFM14A, 425 | gaps toward the offer, then flat just below it; gap down on deal failure | [A] target premia; [C] arbitrage pinning | reject technical setups: price is pinned to the deal |
| M&A acquirer | 8-K 1.01, 2.01 | often negative, more for stock-financed deals | [A] Andrade, Mitchell and Stafford 2001 | news gap; follow the class |
| Offering / dilution | 424B*, S-1, S-3, 8-K 3.02; ATM programs upstream | gap toward the offer price, which becomes a reference level | [A] Asquith and Mullins 1986; Masulis and Korwar 1986; Loughran and Ritter 1995 | no long ~5 sessions; first positive sign = close above the pre-deal close on RVOL >= 2 [C] |
| IPO lock-up expiry | IPO date upstream (or the first bar, if the history starts within the last year) + stated lock-up (commonly 180 days [C]) | small negative abnormal return and a lasting volume rise around the unlock | [A] Field and Hanka 2001 | treat as a supply event inside the hold; no breakout entry in the week before |
| Product launch, investor day, conference | `GetUpcomingInvestorEvents` | run-up into the date, flat-to-down after | [C]/[S] | short_swing exit before; swing: treat as a report if RU20 >= 3 ATR |
| FDA / trial readout / ruling | 8-K 7.01/8.01; calendar upstream | binary gap, can be a large fraction of value | [C] mechanical | never hold a chart-based plan through it; enter after, on a post-event base |
| Index inclusion/deletion | upstream index changes | announcement gap, effective-date volume spike; reversal in some samples | [A] Harris and Gurel 1986 (reversal), Shleifer 1986 (persistent); effect now near zero (Greenwood and Sammon) | do not chase; effective-date volume is not accumulation |
| Mechanical volume days | S&P rebalance / quarterly options expiration (third Friday Mar/Jun/Sep/Dec), Russell reconstitution (`08` 7.1) | volume spikes with no information | [C] | ignore RVOL on those sessions; no volume-confirmed trigger on them alone |
| Buyback, split | upstream / 8-K 8.01 | small positive gap; post-split drift not robust | [A] Ikenberry, Lakonishok and Vermaelen 1995; Ikenberry, Rankine and Stice 1996; Byun and Rozeff 2003 | tailwind only, never a setup; use split-adjusted bars |
| Lawsuit, probe, recall, abrupt executive exit | 8-K 8.01, 5.02 or upstream | gap down; partly priced in if the chart already fell | [C] | news-driven fear (8.2); follow the class |
| Restatement | 8-K 4.02 | severe gap down, further weakness common | [A] reaction (Palmrose, Richardson and Scholz 2004); [C] drift | no longs |
| Ex-dividend | dividend history upstream | mechanical drop of roughly (on average somewhat less than) the dividend (Elton and Gruber 1970) | [A] | not a signal; `08` 7.3 |

Unknown cause: write "gap of X% (Y ATR) on DATE, no filing found"; apply the no-news branch only when `ListFilings` was checked (nothing within 2 sessions) and the sector ETF did not gap similarly.

## 10. Macro events and market-wide gaps

- Scheduled releases (FOMC, CPI, payrolls) carry higher average market returns [A] (Savor and Wilson 2013); a pre-FOMC index drift (Lucca and Moench 2015) [A] was later reported to have faded (Kurov, Wolfe and Gilbert 2021) [contested]. The average premium does not help a single stop; macro days add jump risk.
- No economic calendar in the technical tools: use dates only from an upstream folder; else `NOT CHECKED: macro calendar (not in technical tools)`.
- Market-wide gap: SPY abs(O / C_prev - 1) >= 1 SPY ATR%. Stock excess gap = stock G% - beta_proxy x SPY G%; only the excess is stock information.

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Known macro release inside hold | no entry on the session before; Risks note; stop < 1.5 ATR away can be hit by the release (`08` 7.1) | Risks note | ignore unless the regime is fragile | ignore |
| Market-wide gap down through the stop | `close`: wait for the close; a close back above the stop keeps the trade | same | weekly close decides | weekly close decides |
| Market-wide fear (SPY d50 <= -4, VIX spike if available) | S15 on leaders only after the market's own reversal | no new breakout entries until the market follow-through (`06` 5) | pause adds | stage buys in strong names at weekly support [C] |

## 11. Overreaction versus underreaction: reconciling by horizon

| Horizon | Dominant effect | Condition | Evidence | Use |
|---|---|---|---|---|
| 1-5 days | reversal of no-news, liquidity moves; continuation of news moves | filing vs none; low vs high turnover | [A] Jegadeesh 1990, Lehmann 1990, Chan 2003, Medhat and Schmeling 2022 | fade only no-news extremes (S14/S15); follow news gaps |
| 1 week - 3 months after news | underreaction: drift with the reaction | stronger in illiquid, low-attention stocks; weak in large caps now | [A] Bernard and Thomas 1989; Brandt et al.; Martineau 2022; Chordia et al. 2009 | post-report entries in the reaction direction (short_swing, swing) |
| 3-12 months | momentum; nearness to the 52-week high | stronger for gradual paths; crashes in bear-market rebounds | [A] Jegadeesh and Titman 1993; George and Hwang 2004; Da et al. 2014; Daniel and Moskowitz 2016 | hold winners (long_swing), trail rather than sell "overbought" |
| 3-5 years | reversal of extreme winners and losers | extreme cumulative moves | [A] De Bondt and Thaler 1985 | investment context only; still needs a weekly base |
| Bubbles | crash risk up, average returns not reliably negative | acceleration, volatility, turnover, issuance, young firms | [A] Greenwood et al. 2019; Baker and Wurgler 2006 | scale out and trail; no shorts |

Rule of thumb [A synthesis; each row keeps its caveats]: the shorter the horizon and the less news behind a move, the more it reverses; the more fundamental news and the longer the horizon up to ~1 year, the more it continues; beyond several years extremes revert. Reconciling theories (for reasoning only): Barberis, Shleifer and Vishny 1998; Daniel, Hirshleifer and Subrahmanyam 1998; Hong and Stein 1999 [A].

## 12. Execution, liquidity, regime and time limits around events

| Issue | Rule (tell the human in the plan) | Label |
|---|---|---|
| Resting entry orders | cancel any resting buy-stop/limit at the close of the session before a report or binary event; a buy-stop at X fills at the gap open, possibly far above X, turning 2R into < 1R. Every entry_condition carries "void if the open is above the fill ceiling" (`05` 7.5, `06` 7) | [C] |
| Reaction-day open | no market orders at R's open: spreads are wide and the first minutes whipsaw; the live quote is 15-min delayed. Post-report triggers are close-based (earliest close of R+1) | [C] |
| Resting sell-stops | `intraday`: fills at or through the gap; `close`: acted on at R's close, which can be worse (D1) or better (D2 recovers) than the open. State which applies | [C] SEC bulletin |
| Liquidity | read 20-day median dollar volume (price hook); thin names drift more after reports but costs eat much of it [A] (Chordia et al. 2009): add cost in R (`05` 7.5); reject if the gap-day stop implies slippage beyond the cap | [A]/[C] |
| False post-event breakouts | a U1 that closes below the gap-day low within 5 sessions is a failed breakout (`03` 4.15): exit, no re-entry until a new base | [C] |
| Regime (`01` 12) | risk_off: U1/S13 confidence one notch lower, D1 drift trusted more, hype actions taken from the next-higher 7.2 row, fear buys only after the market follow-through; risk_on: D2 washouts in stage 2 leaders are the best fear buys | [C]; momentum regime dependence [A] |
| Shorts (only if `allow_short` true; brief mirror) | mirror U3/U4 and D1: short a failed rebound to the gap midpoint or AVWAP from R, stop above the gap-day high; never short a hype score alone (no negative average returns [A]); high short interest adds squeeze gap risk [S] | [C] |

Time limits for event trades (planned before entry; clocks from `05` 9 / `08` 4; no event trade is open-ended):

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| S13 / post-earnings base entry | CP bar 5 (MFE >= +0.5R, gap-day low held); max 15 bars and before the next report | CP bar 10; max 40 bars and >= 5 sessions before the next report | CP week 6; max 26 weeks; each report named with its action | per `05` 9; each report a checkpoint |
| Watch-list validity after R | S13 (a) R+2..R+5; (b) to R+15 | base trigger by R+20 | base trigger by R+8 weeks | first weekly close rule, else wait a quarter |
| Fear buy (8.3) | CP 5 sessions; max 10-15 | CP bar 10; max 40 bars (`05` 9) | weekly base only | pilot reviewed at week 13 |
| Hype holdings | trail per 7.2; no extension of max hold | same | same | trims per 7.2 |

## 13. Event calendar checklist per trade_type

Run before writing the plan; one line per item in Factors or Risks (shared.md), e.g. `- [event] Earnings 2026-10-29 (confirmed) inside hold; HEM 5.8% (8 reports) > stop distance 4.9%: exit before the report. Weighed: sets max hold, verdict unchanged`.

| Check | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Window scanned | entry to latest max hold + 2 sessions | same (role window 45 d); S13 trades end >= 5 sessions before the next report | full hold + 2 sessions; every report | first 12 months; every report |
| Next earnings (confirmed / estimated / unknown; moved vs last year?) | outside the window, else shorten or reject | outside, or exit/halve/cushion stated | named, with action | named, with review |
| Last reaction class (3) and date | if R within 60 sessions | required | last 2 | last 4, weekly view |
| HEM, HEMmax, WL%, gap-sized risk (6) | if any event in window | when a report is in the hold | required | required |
| Run-up RU20 / RU5 | if event in window | required | required | note |
| Other company events, peer reports, lock-up | treat as report | cushion rule if RU20 >= 3 ATR | Risks | Risks |
| Filings in last 20 sessions (offering, M&A, 4.02, 5.02, NT 10-K/Q) | required | required | required | required |
| Mechanical volume days in the window (9) | flag RVOL | flag | note | note |
| Upstream-only data (FDA, index, macro, short interest, put/call, VIX, implied move) | use if present, else NOT CHECKED | same | same | same |
| Hype score (7.1) / fear read (8.1) | required | required | weekly version | weekly version |
| Resting orders across the event (12) | none | cancel before | cancel before | cancel before |
| Max-hold constraint | ends >= 1 session before the next event | >= 5 sessions before the next report unless cushion rule | actions at each report | review points |

## 14. Worked examples (hypothetical)

**A. Holding through a report (swing).** XYZ long, e = 50.00, s = 46.50 (risk 3.50, 7.0%), t = 58.00. Report after the close in 12 sessions; past 8 reactions: HEM 6.0%, HEMmax adverse 14%. At T's close C_now = 54.20: OP = 4.20 / 3.50 = 1.2R. Raise stop to 50.00; distance (54.20 - 50.00) / 54.20 = 7.7% > HEM 6.0%: cushion passes, hold full size. WL% = (50.00 - 54.20 x 0.86) / 50.00 = 6.8% (about -1R): a repeat of the worst reaction skips the raised stop and loses about the original risk, still inside `max_loss` 8%; state it in Risks. Keep the resting 58.00 sell-limit: on a gap up it fills at or above 58.00.

**B. Sell the news (reading R).** XYZ ran from 40.00 to 47.50 in 20 sessions (ATR14 1.50, RU20 = 5.0 ATR). R: O = 50.00 (gap +5.3%, 1.7 ATR), H = 50.40, L = 46.90, C = 47.20, RVOL 3.4. GR = (47.20 - 47.50) / (50.00 - 47.50) = -0.12; CLV = ((47.20 - 46.90) - (50.40 - 47.20)) / 3.50 = -0.83. Class U4: no entry; a holder sells at least half at R's close and exits on a close below 46.90.

**C. Washout (short_swing).** XYZ fell 30% in 3 months. R: O = 21.00 vs C_P = 24.00 (-12.5%, 2.4 ATR, so ATR 1.25), L = 20.40, H = 23.60, C = 23.30, RVOL 4.1. GR = (23.30 - 24.00) / (21.00 - 24.00) = 0.23 (77% of the gap recovered); CLV = +0.81: D2. R+3 closes 23.80 above H_R with RVOL 1.6, but stop 20.40 - 0.5 x 1.25 = 19.78 is 16.2% below 23.60: too far for 8%. Secondary test: R+8 low 22.10 holds, reversal close 22.90 = entry; stop 21.60 (22.10 - 0.4 ATR; risk 1.30 = 5.7%). Partial at the pre-gap close 24.00; plan target the declining SMA50 at 26.00 (R:R 3.10 / 1.30 = 2.4). Half risk; CP 5 sessions, max 12 sessions.

## 15. Common errors

- Holding a short_swing or an un-cushioned swing through a report because "the numbers will be good".
- Reading the headline instead of the close: gap up closing weak = distribution; gap down closing strong = washout candidate.
- Buying the climax or gap-down day; averaging down into news-driven drift.
- Fading earnings gaps because "gaps get filled" [S]; treating a sympathy gap as the stock's own reaction.
- Calling event-day or rebalance-day volume "accumulation" without CLV and follow-through.
- Selling a strong trend on one "overbought" reading instead of scaling out on a hype score.
- Leaving a resting buy-stop across a report; assuming a stop caps a gap loss; omitting WL% when HEMmax exceeds the stop distance.
- Naming the cause of a move from memory; only filings and upstream data may name it.

## Sources

Web search and publisher sites were unavailable during research and reviews; findings are cited qualitatively and no unattributed statistic is quoted. "[r]" = added in a review from the literature, not re-checked online. Working papers are not peer-reviewed.

- Aboody, Lehavy, Trueman (2010), Limited attention and the earnings announcement returns of past stock market winners, Review of Accounting Studies 15.
- Andrade, Mitchell, Stafford (2001), New evidence and perspectives on mergers, Journal of Economic Perspectives 15(2).
- Asquith, Mullins (1986), Equity issues and offering dilution, JFE 15.
- Asquith, Pathak, Ritter (2005), Short interest, institutional ownership, and stock returns, JFE 78.
- Baker, Wurgler (2006), Investor sentiment and the cross-section of stock returns, Journal of Finance 61.
- Ball, Brown (1968), An empirical evaluation of accounting income numbers, Journal of Accounting Research 6.
- Barber, De George, Lehavy, Trueman (2013), The earnings announcement premium around the globe, JFE 108. https://webuser.bus.umich.edu/rlehavy/BDLT.pdf
- Barberis, Shleifer, Vishny (1998), A model of investor sentiment, JFE 49.
- Ben-Rephael et al., Mind the gap: the non-fundamental role of earnings days (working paper; not re-checked). https://haslam.utk.edu/wp-content/uploads/2024/11/Ben-Rephael-Paper.pdf
- Bernard, Thomas (1989), Post-earnings-announcement drift: delayed price response or risk premium? JAR 27. https://ideas.repec.org/a/bla/joares/v27y1989ip1-36.html
- Boehmer, Huszar, Jordan (2010), The good news in short interest, JFE 96.
- Brandt, Kishore, Santa-Clara, Venkatachalam (2008), Earnings announcements are full of surprises (working paper). https://www.anderson.ucla.edu/documents/areas/fac/finance/ear.pdf
- Bulkowski, Encyclopedia of Chart Patterns (2nd ed. 2005); https://thepatternsite.com/gaps.html (qualitative; not re-verified).
- Byun, Rozeff (2003), Long-run performance after stock splits: 1927 to 1996, Journal of Finance 58 [r].
- Caporale, Plastun (2017), Price gaps: another market anomaly? (SSRN). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2850057
- Chan, W. S. (2003), Stock price reaction to news and no-news: drift and reversal after headlines, JFE 70. https://ideas.repec.org/a/eee/jfinec/v70y2003i2p223-260.html
- Chan, Jegadeesh, Lakonishok (1996), Momentum strategies, Journal of Finance 51(5) [r].
- Chordia, Goyal, Sadka, Sadka, Shivakumar (2009), Liquidity and the post-earnings-announcement drift, FAJ 65(4).
- Cooper (1999), Filter rules based on price and volume in individual security overreaction, RFS 12. https://academic.oup.com/rfs/article-abstract/12/4/901/1580996
- Da, Gurun, Warachka (2014), Frog in the pan: continuous information and momentum, RFS 27.
- Daniel, Hirshleifer, Subrahmanyam (1998), Investor psychology and security market under- and overreactions, Journal of Finance 53.
- Daniel, Moskowitz (2016), Momentum crashes, JFE 122. https://www.sciencedirect.com/science/article/pii/S0304405X16301490
- De Bondt, Thaler (1985), Does the stock market overreact? Journal of Finance 40.
- DellaVigna, Pollet (2009), Investor inattention and Friday earnings announcements, Journal of Finance 64.
- Dubinsky, Johannes, Kaeck, Seeger (2019), Option pricing of earnings announcement risks, RFS 32.
- Elton, Gruber (1970), Marginal stockholder tax rates and the clientele effect, Review of Economics and Statistics 52 [r].
- Field, Hanka (2001), The expiration of IPO share lockups, Journal of Finance 56 [r].
- Frazzini, Lamont (2007), The earnings announcement premium and trading volume, NBER w13090. https://www.nber.org/papers/w13090
- George, Hwang (2004), The 52-week high and momentum investing, Journal of Finance 59. https://www.bauer.uh.edu/tgeorge/papers/gh4-paper.pdf
- Gervais, Kaniel, Mingelgrin (2001), The high-volume return premium, Journal of Finance 56. https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00349
- Greenwood, Sammon, The disappearing index effect (NBER working paper; later Journal of Finance; details not re-checked).
- Greenwood, Shleifer, You (2019), Bubbles for Fama, JFE 131.
- Harris, Gurel (1986), Price and volume effects associated with changes in the S&P 500 list, Journal of Finance 41.
- Hirshleifer, Lim, Teoh (2009), Driven to distraction: extraneous events and underreaction to earnings news, Journal of Finance 64.
- Hong, Stein (1999), A unified theory of underreaction, momentum trading, and overreaction, Journal of Finance 54.
- Ikenberry, Lakonishok, Vermaelen (1995), Market underreaction to open market share repurchases, JFE 39.
- Ikenberry, Rankine, Stice (1996), What do stock splits really signal? JFQA 31.
- Jegadeesh (1990), Evidence of predictable behavior of security returns, Journal of Finance 45; Lehmann (1990), Fads, martingales and market efficiency, QJE 105. https://alphaarchitect.com/quantitative-momentum-research-short-term-return-reversal/
- Jegadeesh, Titman (1993), Returns to buying winners and selling losers, Journal of Finance 48.
- Johnson, So (2018), Time will tell: information in the timing of scheduled earnings news, JFQA 53 [r; also cited in `08`].
- Kurov, Wolfe, Gilbert (2021), The disappearing pre-FOMC announcement drift, Finance Research Letters 40 [r].
- Loughran, Ritter (1995), The new issues puzzle, Journal of Finance 50.
- Lucca, Moench (2015), The pre-FOMC announcement drift, Journal of Finance 70.
- Martineau (2022), Rest in peace post-earnings announcement drift, Critical Finance Review 11. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607
- Masulis, Korwar (1986), Seasoned equity offerings: an empirical investigation, JFE 15.
- Medhat, Schmeling (2022), Short-term momentum, RFS 35. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3150525
- Moskowitz, Ooi, Pedersen (2012), Time series momentum, JFE 104. https://www.sciencedirect.com/science/article/pii/S0304405X11002613
- Nagel (2012), Evaporating liquidity, RFS 25.
- Palmrose, Richardson, Scholz (2004), Determinants of market reactions to restatement announcements, Journal of Accounting and Economics 37.
- Pan, Poteshman (2006), The information in option volume for future stock prices, RFS 19 [r].
- Savor (2012), Stock returns after major price shocks: the impact of information, JFE 106.
- Savor, Wilson (2013), How much do investors care about macroeconomic risk? JFQA 48; (2016), Earnings announcements and systematic risk, Journal of Finance 71.
- Shleifer (1986), Do demand curves for stocks slope down? Journal of Finance 41.
- Skinner, Sloan (2002), Earnings surprises, growth expectations, and stock returns, Review of Accounting Studies 7.
- Tetlock (2011), All the news that's fit to reprint: do investors react to stale information? RFS 24.
- Thomas, Zhang (2008), Overreaction to intra-industry information transfers? Journal of Accounting Research 46 [r].
- Womack (1996), Do brokerage analysts' recommendations have investment value? Journal of Finance 51.
- SEC Office of Investor Education, Investor Bulletin: Stop, Stop-Limit, and Trailing Stop Orders. https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15
- Practitioner conventions: O'Neil, How to Make Money in Stocks (climax top, follow-through day); Minervini, Trade Like a Stock Market Wizard (selling into strength); Wyckoff method (climaxes, secondary test; https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial); Edwards and Magee, Technical Analysis of Stock Trends (gap types, key reversals); Connors (RSI(2)).
