# 06 - Entering a trade

## How to use this file

- Use after a setup is chosen (`04-strategies-and-setups.md`, "04") and its levels are read (`01-chart-reading.md`, `03-chart-patterns.md`). This file turns "a level P" into an executable entry: trigger, buffer, confirmations, red flags, stale cap, expiry, tranches and plan fields.
- Fast path: section 3.0 (entry state on `as_of`) -> section 12 (per-trade_type table) -> section 15 (checklist) -> section 14 (fields). Open other sections when a checklist item needs detail.
- role.md rules stay authoritative (`max_loss`, `reward_to_risk`, `stale_entry` 3%, `upcoming_earnings`). Extra checks here are applied in addition and reported; never use them to relax a role rule.
- No entry without a written exit and clock: stop, target, invalidation, progress check and max hold (`07-exits.md` 2, `08-trade-plan-and-timeline.md` 4) exist before the entry is final.
- Labels: [A] academic/replicated, [P] practitioner statistical study, [C] convention or house default (a threshold chosen for this playbook, untested), [S] speculative/contested. Examples use made-up tickers and prices.
- Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).

## 1. What the evidence says about entries

| Claim | Evidence | Label | Use |
|---|---|---|---|
| Buying strength has had positive expected returns | 3-12 month momentum (Jegadeesh and Titman 1993); time-series momentum over 1-12 months, partial later reversal (Moskowitz, Ooi, Pedersen 2012); 52-week-high nearness dominates and does not reverse long-run (George and Hwang 2004) | [A] | Prefer breakouts near 52-week highs for swing and longer; the evidence is multi-month returns of ranked stocks, so the trigger rules are [C] |
| Technical trading rules | MA and range-breakout rules predicted Dow returns 1897-1986 (Brock, Lakonishok, LeBaron 1992) but the best rule failed out of sample (Sullivan, Timmermann, White 1999); of 95 modern studies 56 positive, 20 negative, 19 mixed, US stock profits mostly before about 1990 (Park and Irwin 2007) | [A], decaying | A trigger is timing and discipline, not an edge; it needs trend and RS context |
| Short-term reversal | 1-week to 1-month losers bounce, winners give back (Jegadeesh 1990; Lehmann 1990); mostly liquidity compensation, small after costs in large caps (Nagel 2012) | [A] / [C] use | Buy pullbacks in uptrends; do not chase 1-week spikes |
| Limit-order adverse selection | Limits fill disproportionately when price falls through on bad news (Linnainmaa 2010) | [A] | A limit needs a graded zone and a cancel rule |
| Round-number clustering | Stops cluster just beyond, take-profits at round numbers (Osler 2003, 2005, FX); equity buyers overbuy one cent below (Bhattacharya, Holden, Jacobsen 2012) | [A] | Triggers above the round number (section 4) |
| Throwbacks and gaps | Bulkowski (as summarised; varies by pattern): throwbacks common (secondary summaries range from about a third in his multi-pattern study to half or more for some patterns; `03` 2.6), usually within about 10 days, and no-throwback patterns did better on average; heavier breakout volume and breakout-day gaps ("2 out of 3 or better") went with better performance | [P] | Retests buy a better price but a weaker average breakout; do not skip for a gap, the stale cap decides |
| Pilot then add | O'Neil follow-ups 2-3% above the buy point, smaller; Minervini pilot buys; Turtle adds every 1/2 N, max 4 units | [C]; Turtles [P] futures rules | Section 10 |
| Lump sum vs spreading over time | Lump sum beat 12-month cost averaging about two-thirds of the time (Vanguard 2012, 2023) | [P] | Scale in on conditions, never on dates |
| "Entries matter less than exits and sizing" | Tharp's random-entry test; LeBeau and Lucas; not replicated | [S] | Get stop, size and expiry right before polishing the trigger |

## 2. Vocabulary and data constraints

### 2.1 Terms

| Term | Definition |
|---|---|
| P (pivot) | Level whose break completes the setup: flat top, handle high, final-contraction high, neckline, prior-bar high after a pullback (`03` 2.3). |
| b, L | Buffer above P (section 4); L = limit price in a support zone. Stale cap: highest fill that still passes the rules (8.3). |
| e (entry) | Price used in rule checks: the order price for stop/limit orders; the trigger-day close for close confirmation. Tranches: 10.3. |
| s, t, R | Stop, target (chart levels, `07-exits.md`); R = e - s per share. |
| RVOL | Day volume / mean volume of the prior 50 days; RVOL(20) for short_swing (playbook-wide convention; state which); weekly: week volume / mean of prior 10 weeks. |
| CLV | ((C - L) - (H - C)) / (H - L), -1..+1 (0 if H = L). >= 0 upper half; >= 0.5 upper quarter. |
| ATR14 | Wilder ATR from the hook (daily). Weekly ATR: same formula on the hook's weekly bars. ATR% = ATR14 / close x 100. |

### 2.2 What daily-only data means

- A daily bar exists only after 16:00 New York; close triggers are confirmed only on completed bars; the current session is seen at best through a 15-minute-delayed quote.
- Intraday order is unknown: if one bar has high >= trigger and low <= stop, assume "triggered then stopped" [C].
- Fill conventions (write them in the plan so the evaluator uses the same) [C]:

| Trigger | Triggered when | Assumed fill |
|---|---|---|
| Buy-stop at T | bar high >= T | max(open, T), capped: no fill if open > stale cap (stop-limit) |
| Close confirmation at T | bar close >= T | that close, or next open if the plan says so |
| Weekly close confirmation | weekly close >= T | that week's close or next week's open |
| Buy limit at L | bar low <= L | min(open, L) |

- If `as_of` is mid-week, the last weekly bar is incomplete: a weekly-close trigger cannot have fired in it.

### 2.3 Profile `level_trigger`: close vs intraday [C]

| | `close` (example profile) | `intraday` |
|---|---|---|
| Wording | "daily close above P + b" (weekly types: "weekly close above P + b", b = 0.1 x weekly ATR14) | "buy-stop at P + b" (stop-limit, limit = stale cap) |
| Filters / cost | filters intraday pokes that close back below P (the commonest false break); worse fill, can close past the cap, next-open execution adds gap risk | takes every poke; stop slippage |
| Human executes | near the close on the delayed quote, or next open | resting stop-limit |

Closing confirmation is the classic filter (Edwards and Magee; Murphy), untested either way. A pullback limit (T4) is not a breakout trigger and is allowed under `close`; say so. Costs in R and the close-trigger overshoot: `05` 7.5 (tight stops make costs matter most).

## 3. Entry trigger types

### 3.0 Entry state on `as_of` and trigger choice (decide first)

| State / situation (last completed bar, current price p) | Plan |
|---|---|
| Setup forming, definition not met | no plan; watch note naming what must happen (`03` 2.9) |
| Complete, not triggered, below P; tight base, RS strong | conditional T1/T2 per profile (optional T7 pilot, swing and longer); `valid_until`, cancel rules |
| Triggered on the last bar(s), p <= stale cap, confirmations pass | "triggered": e = trigger (or trigger close); human may act now within the cap |
| Triggered but p > cap, or extended (`01` 9.2) | no entry now; conditional T6 or T4/T5, or wait for a new base |
| Failed (close < P - 0.5 ATR within 1-5 bars of the break) | no long until a new base or reclaim (T9); `03` 2.6 |
| Uptrend pulling back to a rising MA or prior breakout | T5 default; T4 only at a graded zone |
| Weekly-primary (long_swing, investment) | T3, or T4/T5 at a weekly zone |
| Undercut of support in a weekly uptrend, then reclaim | T9 |
| Gap through P on news or results | sections 7 and 11 |
| Range trade (04 S11) | T4 near support or T5 off it; never a breakout trigger inside the range |

### 3.1 Comparison

| # | Trigger | Where it fits | Gains | Costs | Label |
|---|---|---|---|---|---|
| T1 | Buy-stop above breakout, P + b | base, 52-week-high and flag breakouts (S3, S5, S6, S7) with `intraday` | never misses a breakout | slippage; more false breakouts; gap fills | [C] |
| T2 | Daily close > P + b | same, with `close` | filters intraday failures | worse fill; can be stale at once on a wide bar | [C] |
| T3 | Weekly close > P + 0.1 x weekly ATR14 | long_swing, investment breakouts | filters daily noise; matches weekly levels | fill can be several daily ATR above P | [C] |
| T4 | Limit at L in a graded zone (rising MA, prior breakout level, swing low, event AVWAP `02` 7.10) | S1, S2, S10, S11 | best price, tightest stop | adverse selection [A]; misses the strongest names | [A] risk / [C] rule |
| T5 | Pullback reversal: after a touch of support, close above the prior bar's high (or buy-stop above it) | S1, S2, S10 | shows the pullback ended; stop under the pullback low | worse price than T4; can fire just before the pullback resumes | [C] (Elder's trailing buy-stop) |
| T6 | Retest: after a valid breakout, price returns to P +/- 0.5 ATR and holds, then T4 or T5 | S2 | tighter stop; second chance | selects weaker breakouts on average [P]; often no retest | [P] |
| T7 | Anticipatory inside the base, before P breaks: pocket pivot, NR7/inside-bar break in the final contraction (`03` 3.14, 3.19, 3.20) | S3 VCP, flat base | lowest entry, tightest stop | breakout may never come; more failures | [C] |
| T8 | Gap through P at the open | S13, gap-and-go (`03` 3.18) | strongest demand signal [P] | far above P; often stale; earnings gaps carry event risk | [P]/[C] |
| T9 | Reclaim (undercut and rally): close back above broken support, a prior pivot low or SMA50 within 1-3 bars (`03` 4.16, 04 S12) | failed breakdowns, springs | stop just under the new low | fails in stage 4; a second undercut kills it | [C]/[P] (Bulkowski busts) |

### 3.2 Rules per trigger

- **T1/T2:** section 5 cues on the trigger bar. Human order: stop-limit, stop P + b, limit = stale cap; a plain stop becomes a market order and can fill far above in a gap (SEC bulletin).
- **T3:** a daily close > P + 0.1 ATR14 inside a week whose running bar is above P may time the entry, but only the weekly close confirms; a weekly close back below P = failed (`07-exits.md`).
- **T4:** only at a major/intermediate zone (`01` 6.3) in a stage-2 uptrend; L = upper edge (strong trends rarely reach the middle) [C]. Cancel on a close or open below the stop, or a wide-range drop into the zone on RVOL > 1.5 (switch to T5).
- **T5:** reversal bar CLV >= 0.5 or close above the prior bar's high; pullback volume below the 50-day average (04 S1).
- **T6:** from bar 2 to about bar 21 after a breakout that met section 5 (Bulkowski's throwback window is 30 calendar days); closes must hold >= P - 0.5 ATR; a close below that = failed breakout, not a bargain (`03` 2.6).
- **T7:** all of: risk_on, RS line at/near a new high, 10-day average volume < 50-day (dry-up), a definable low within the loss limit. Pilot size; the add is the real breakout (T1/T2). Invalidation adds "close above P within 10 bars, else exit" (P is overhead supply inside the trade).
- **T8:** section 7.
- **T9:** the undercut is a new low below a prior swing low or support that is >= 4 bars old; entry = close back above that level (buy-stop for `intraday`); stop = new low - 0.25 ATR; weekly trend up (above a rising 30-week SMA); skip in stage 4.

### 3.3 Missed, failed and repeated entries [C]

- **Missed:** never chase past the cap, never lower the confirmation standard, never widen the stop to "make it fit". The next entries are T6, the first pullback to the rising 10/20-day MA (T5), or the next base.
- **Stopped out:** re-entry allowed once per setup, only on a fresh trigger (reclaim T9 of P, or a new base) with fresh levels, full rule checks and a new `valid_until`; never the same day as the stop. Two failures at the same P = drop the name for that setup.
- **Repeated failures at P:** >= 2 closes above P that failed within 3 bars in the last 3 months = require T3/T6 or grade A (section 5.2).

## 4. Where exactly to place the trigger

| Item | Rule | Label |
|---|---|---|
| Buffer (daily) | b = 0.1 x ATR14, minimum 0.02 | [C] house default; O'Neil used P + 0.10 |
| Buffer (weekly-primary) | weekly close > P + 0.1 x weekly ATR14; daily timing close > P + 0.1 x ATR14 | [C] |
| High ATR% (> 4) or low-priced | b = 0.15-0.25 x ATR14 | [C] |
| Quiet (ATR% < 1.5), short_swing | b = 0.05 x ATR14 (min 0.02): 0.1 ATR is a large share of a small R | [C] |
| Round numbers | if P + b lies within 0.25 ATR below a whole number (half dollar under ~$20), trigger just above it (50.07, not 49.97) | [A] clustering; placement [C] |
| Multi-touch resistance | P = highest high among the touches, not the average | [C] |
| Pullback limit L | top of the support zone, or MA + 0.1 ATR | [C] |
| Pullback reversal / T9 | prior bar's high + 0.02 (or + 0.05 ATR); reclaimed level + 0.02 | [C] |
| Show it | "daily close above 50.12 (pivot 50.00 + 0.1 x ATR14 1.20)" | required |

After placing: recompute `max_loss` and `reward_to_risk` with e = trigger. The buffer is part of the risk.

## 5. Confirmation cues

### 5.1 Breakout confirmations (trigger bar and prior 1-3 bars)

| Cue | Pass (daily) | Weekly-primary | Label |
|---|---|---|---|
| Close vs pivot | close > P + b (mandatory in `close` mode) | weekly close > P + 0.1 weekly ATR | [C] |
| Volume | RVOL >= 1.4 (O'Neil: 40-50% above average); short_swing 1.5 | week RVOL >= 1.2, or OBV at a 26-week high | [C]; bigger average moves on heavy volume [P] |
| Close location | CLV >= 0; ideal >= 0.5 | weekly CLV >= 0 | [C] |
| Candle quality | range >= 1 ATR, upper wick < 1/3 of range | weekly range > its 10-week average | [C] |
| Tightness before | NR7/inside bar/contracting ranges in the prior 5-10 bars; base's last 10 bars' volume below average | 3WT or contracting weekly ranges | [C] (`02` 7.2, `03` 3.14-3.15) |
| Relative strength | RS line (close / SPY) at a 3-month high (short_swing, swing) or 52-week high (long_swing, investment), ideally before price | same, weekly | [A] momentum; RS lead [C] |
| 52-week-high proximity | within 10% of the 52-week closing high | within 15% | [A] George and Hwang; cut-off [C] |
| Market regime | not risk_off (`01` 12) | SPY above its 10-month SMA | [P] Faber / [C] |
| Sector | ETF above a rising SMA50; its RS vs SPY not at a 3-month low | ETF above a rising 30-week SMA | [C]; industry momentum [A] (Moskowitz and Grinblatt 1999) |
| Stock follow-through | next 1-3 closes stay above P | next weekly close above P | [C]; the add condition |
| Market follow-through day | after a correction, day 4+ of a rally attempt (day 1 = first up close off the low): SPY/QQQ up about 1.25%+ on higher volume than the prior day, before new breakout entries | same, to resume after risk_off | [C] IBD (threshold varied about 1-1.7%); many fail |

### 5.2 Grading (house rule [C])

- Mandatory: trigger condition met; liquidity (`01` 7.3); stop within `max_loss`; no "reject" red flag (section 6).
- Supporting cues (count, max 7): volume, close location, candle quality, tightness, RS, 52-week proximity, sector.
- Grade A >= 5; B = 3-4; C <= 2.
- Regime gate (`01` 12.2): risk_on any A/B; neutral A or B, prefer RS leaders; risk_off short_swing/swing breakouts grade A only with shorter holds, long_swing/investment only stage 1->2 with RS at new highs.
- Action: A = full planned first tranche; B = pilot or wait for stock follow-through; C = no entry on this bar, re-check next bar inside the validity window.
- Pullback entries (T4/T5/T9) swap the volume cue: pullback volume below the 50-day average, reversal bar volume above the prior bar's (04 S1).

## 6. Red flags: do not enter (or wait)

| Red flag | Test | Action | Label |
|---|---|---|---|
| Extended | above `01` 9.2 "extended" (values in section 12) | no entry; plan T4/T5 or wait for a base | [C] thresholds; short-term reversal [A] |
| Climactic volume | RVOL >= 3 on an up bar already extended, after > 25% from the last base, often wide range or gap | no entry; wait for a new base | [C] (O'Neil climax signs) |
| Hype signs | `09` 7.1 signs present (parabolic run, gap after gap, RVOL spikes on news) | no new entry (`09` 7.3) | [C] |
| Earnings inside the window | section 11 | wait, exit-before plan, or pilot | [C]; role flags it |
| Binary or macro event | FDA date, ruling, index change inside the hold; or a major macro release next session (`09` 10) | binary: wait; macro: prefer T2 over a resting T1 | [C] |
| Gap past the cap | open or close > stale cap | cancel today (section 7) | role rule |
| Overhead supply | nearest major/intermediate resistance lower edge < e + m x R (m = `min_reward_to_risk`) | reject: `reward_to_risk` cannot pass | [C] |
| Weak market | risk_off, or >= 6 distribution days on SPY/QQQ in 25 sessions (down >= 0.2% on volume above the prior day's) | per 5.2 regime gate | [C] IBD; momentum weaker after down markets [A] (Cooper, Gutierrez, Hameed 2004) |
| Weak breakout bar | CLV < 0, or upper wick > 1/2 of range, or RVOL < 1.0 | wait for a second close above P; low volume is a warning, not a veto (Bulkowski: smaller average gains [P]) | [C] |
| Wrong stage | below a falling SMA200 / 30-week SMA | no trend-long entries; only 04 S15-type reversals | [C] |
| Late-stage base | 4th+ base since stage 2 began, or depth > 1.5x the prior base | lower grade; smaller first tranche | [C] (O'Neil) |
| Illiquid | 20-day dollar volume < $5M | reject short_swing/swing; flag others; limits only | [C] (`01` 7.3) |
| Order large vs volume | human's intended order > ~1% of 20-day average dollar volume (if known) | note slippage in Risks; limits, split over days | [C] house default |
| Falling-knife limit | T4 zone sliced by a wide-range bar on RVOL > 1.5 | cancel; wait for T5 | [A] adverse selection / [C] |

## 7. Gaps at the open (daily bars only)

The plan is written before the session and must tell the human what to do at each kind of open. Gaps on open positions: `07-exits.md` 4.

| Case (long) | Buy-stop (T1) | Close confirmation (T2/T3) | Limit (T4) |
|---|---|---|---|
| Opens below trigger | order rests | judge at the close | order rests |
| Opens above trigger, within cap | fills near the open; re-check R:R at the fill; stop and target unchanged | close must also be within the cap | n/a |
| Opens above cap | stop-limit does not fill; cancel for the day | do not act today | cancel |
| Breakaway gap (>= 1 ATR out of a base, RVOL on track for >= 2) above the cap | old plan void; after the close a NEW gap-and-go plan (`03` 3.18): close above the gap-day high or a 1-3 day hold above its low; stop below the gap-day low; all rules re-priced | same | same |
| Opens below the stop, not triggered | cancel: invalidated | cancel | cancel (a fill would be at a bad price) |
| Opens below L, above the stop | n/a | n/a | fills below L (adverse selection); keep only if no cancel rule is hit |
| Earnings gap | section 11 | same | same |

A gap is classified only after its bar closes (`01` 8.3). A gap-up that closes in the lower half of its range or fills more than half the gap on day 1 is not a gap-and-go entry [C].

## 8. Stale entry

### 8.1 Current rule (role.md, apply as written)

`stale_entry` rejects a long when current price <= s, or (price - e) / e x 100 > 3.0. A price that has not reached the entry passes. No current price: flag.

### 8.2 Weakness of a fixed percent

3% is 3 ATR for a 1% ATR% stock (too loose) but 0.6 ATR for a 5% ATR% stock (an ordinary bar makes it stale). It also ignores the plan's geometry. Example (hypothetical XYZ, 10.5: e 50.12, s 47.10, t 57.20): at 51.20 the move is +2.15% (passes 3%) and 0.9 ATR, yet R:R = (57.20 - 51.20) / (51.20 - 47.10) = 1.46 < 2.0 and max loss = 4.10 / 51.20 = 8.01% > 8.0%. A fill at 51.20 fails both profile rules.

### 8.3 Recommended checks (in addition to 8.1; report each)

1. **Re-price test (primary, [C]):** with p = current price or expected fill, check (t - p) / (p - s) >= m and (p - s) / p x 100 <= L. Publish the **stale cap** = min( (t + m x s) / (1 + m), s / (1 - L/100) ), m = `min_reward_to_risk`, L = `max_loss_per_trade_pct`, **rounded DOWN to the cent**. Example: (57.20 + 2 x 47.10) / 3 = 50.4667 -> 50.46; 47.10 / 0.92 = 51.196 -> 51.19; cap 50.46 (at 50.46 R:R = 6.74 / 3.36 = 2.006; at 50.47 = 6.73 / 3.37 = 1.997, fail). The human's stop-limit limit = the cap. Same as `05` 7.5's fill ceiling plus the loss limit.
2. **ATR distance (secondary, [C]):** stale if p - e > k x ATR: k = 0.5 daily ATR (short_swing), 1.0 daily ATR (swing), 0.5 weekly ATR (long_swing, investment); investment also never > 5% above P (O'Neil chase limit). Catches distant-target plans where re-pricing is lenient.
3. **Reporting until role.md adopts these:** the `stale_entry` outcome follows 8.1 exactly. Put the re-price and ATR results in its detail (`"+1.8% <= 3.0%; re-priced at 51.00: R:R 6.20 / 3.90 = 1.59 < 2.0; stale cap 50.46"`) and always write "do not fill above <cap>" into `entry_condition`. If p is already above the cap, say so under Risks and lower confidence; never move stop or target to rescue the plan.

Why: stop and target are chart levels that do not move with the fill, so chasing breaks the ratio rules first.

## 9. Entry validity window (expiry) and cancellation

An untriggered plan must not live forever: the base changes, earnings approach, the regime moves. Every plan carries `valid_until` (harmonised with `08` 4).

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Validity from `as_of` | 5 sessions | 10 sessions | 20 sessions (4 weeks) | 40 sessions (8 weeks) |
| Pullback-limit (T4) validity | 3 sessions | 5 sessions | 10 sessions | 20 sessions |
| After expiry | cancel; re-analyse from scratch | same | same | re-analyse at the next weekly review |

All [C] house defaults (loose analogy: reversal effects live over 1 week to 1 month, momentum over 3-12 months [A]).

Cancel before expiry on the first of [C]: a close below the stop or invalidation; a new swing high above P without a trigger (pivot moved: re-plan); earnings entering the no-entry zone (section 11); regime drops a class (short_swing/swing breakouts, `01` 12.2); a gap past the stale cap (section 7); for T4, the zone broken on a close or RVOL > 1.5 on the drop into it.

After a fill the clocks are the progress check and max hold, counted from the fill (`08` 4, 6), so the latest possible exit = `valid_until` + max hold. Write both before entry.

## 10. All at once vs scaling in

### 10.1 Choose

| Condition | Choose |
|---|---|
| short_swing; stop < 1.5 ATR; single clean trigger | all at once |
| Grade B breakout, or T7 anticipatory | pilot (1/3-1/2) + add on confirmation |
| Grade A breakout, swing and longer | 2/3 on trigger, 1/3 on follow-through or retest hold |
| long_swing/investment with a wide weekly zone | planned tranches inside the zone, one stop below the zone (10.4) |
| Earnings inside the hold, long_swing/investment | pilot (<= 1/3 for long_swing) before, add after the report reacts well (section 11) |
| An add would push the blended plan past a rule | drop the add, or plan it with a stop raise that keeps the rules (10.3) |

Scale in on conditions, never by calendar (Vanguard [P], section 1).

### 10.2 Pyramiding rules (add to a winner)

1. Add only when the open tranche is in profit by a stated amount (close >= e + 0.5R) or a new trigger forms (T6 hold, first T5 pullback, new weekly high after a flag) [C]. O'Neil: follow-ups 2-3% above the buy point, smaller [C]. Turtles: one unit every 1/2 N, max 4 (Faith) [P futures rules].
2. Each add <= the prior tranche (pyramid, never inverted) [C].
3. The stale cap governs the first fill; each add is its own fill state and the blended position must pass both rules (10.3). Breakout plans never add > 5% above P (O'Neil) [C].
4. On each add, raise the whole position's stop to a new structural level (e.g. P - 0.25 ATR, the failed-breakout line) so total open risk after the add <= the initial planned risk [C]. Stricter than the Turtles, whose total risk grows with each unit.
5. Maximum adds: 0 short_swing, 1 swing, 2 long_swing, 3 investment [C].
6. No add inside the earnings no-entry zone (investment: last ~10 sessions before a report, `09` 4.2), in risk_off, or after a close back below P.

### 10.3 How tranches change e, R and the rule checks

- Blended entry E = sum(f_i x e_i) over filled tranches (f_i = fraction of full planned size).
- Risk per share = E - s_current (stop in force after the last fill).
- Check `max_loss` and `reward_to_risk` in EVERY fill state (pilot only; pilot + add 1; ...) and report the worst. Pyramids: worst is usually "all filled". Zone tranches bought lower: worst is usually "first tranche only".
- The role's `entry` stays the first trigger; tranches go in `entry_condition` / `## Plan`; worst-state numbers go in the rule detail. The target does not change (scale-out blends: `07-exits.md` 6.4).

### 10.4 Averaging down

- Adding below entry after a loss without a pre-planned tranche: never, all types [C]. It adds size as the chart weakens, breaks the planned risk and feeds the disposition effect (Odean 1998 [A]).
- Connors and Alvarez report a lower second unit helped in ETF pullback tests [P]; those are small, pre-defined, time-exited ETF rules, not single-stock trend plans [S for stocks].
- Narrow exception (investment, sometimes long_swing): **planned zone tranches**, only if all hold: (a) in the plan before any fill; (b) all prices inside one graded weekly support zone; (c) one stop below the whole zone; (d) every fill state passes both rules; (e) no tranche after a close below the zone.

### 10.5 Worked examples (hypothetical)

**Breakout with pyramid (swing, `close`).** XYZ flat-base top P = 50.00; ATR14 1.20; handle low 47.40; resistance 57.50.
- Trigger: daily close > 50.12. Stop 47.40 - 0.25 x 1.20 = 47.10. Target 57.50 - 0.30 = 57.20.
- Single entry: max loss 3.02 / 50.12 = 6.0%; R:R 7.08 / 3.02 = 2.34; stale cap 50.46.
- Tranches: 60% at 50.12; 40% on a close >= 51.65 (about +0.5R) after >= 2 bars with no close below 50.00.
- Add with the stop left at 47.10: E = 0.6 x 50.12 + 0.4 x 51.65 = 50.73; max loss 3.63 / 50.73 = 7.2% (passes), R:R 6.47 / 3.63 = 1.78 (FAILS). The add must carry a stop raise.
- Stop raised to 49.70 (50.00 - 0.25 ATR): risk 1.03 per share of full size vs 0.6 x 3.02 = 1.81 before; R:R 6.28; max loss 2.0%. Worst state = pilot only (6.0%, 2.34).

**Investment zone tranches.** ABC weekly support zone 95-100, stop 92.50, target (weekly resistance) 118.
- 50% at 100, 50% at 96. First only: 7.5%, R:R 18 / 7.5 = 2.40. Both: E 98, 5.6%, R:R 3.64. Worst passes. A tranche at 93 (outside the graded zone) = averaging down: remove it.

## 11. Entries around earnings

Owner of earnings mechanics and hype/fear: `09-events-hype-and-fear.md` (4.1-4.4). Entry rules:

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Report inside the planned hold | no entry unless max hold ends >= 1 session before the report; else reject | no new entry in the 10 sessions before; earlier entries state exit / halve / cushion rule (`09` 4.2) | pilot (<= 1/3) before; add after | first tranche allowed; next tranche after; no add in the last ~10 sessions before |
| After the report ("let it report") | earliest: close of R+1 (R = reaction day); only a post-report setup (04 S13) | same; favourites: gap-and-go or the first 3-10 day post-report base (`09` 4.4) | first weekly close after R | add when the first post-report weekly close holds above the pre-report level |
| Date unknown | treat as inside the window (role flags it) | same | same | same |

- A stop does not bound an earnings gap: it becomes a market order at the gap (SEC bulletin). Gap-risk check [C] (`09` 2.3): over the last 4-8 reports (dates from 8-K item 2.02 via `ListFilings`), gap % = |first open after the report - last close before it| / that close x 100; median M, largest Mmax. If a report is inside the hold and M > (e - s) / e x 100 or Mmax > `max_loss_per_trade_pct`, the stop is not the worst case: flag it, prefer "let it report".
- Earnings announcement premium (Frazzini and Lamont 2007; Savor and Wilson 2016) [A]: a small portfolio average with large per-stock variance; it does not justify holding a tight-stop swing through a report [C].
- Post-earnings drift (Bernard and Thomas 1989) [A] supports entering after a strong report in the surprise direction, but Martineau (2022) finds it has disappeared recently outside microcaps [A, contested]. Treat post-report entries as momentum/gap-and-go setups with normal confirmations.
- Post-report entry cues: reaction-day close in the upper half and above the pre-report base high, RVOL >= 2, next 1-3 closes hold above the gap-day low (`03` 3.18). A gap up closing in the lower half or filling > half the gap on day 1 = "sell the news": no entry (`09` 5).
- No entries on the session before a report, even "quick" ones [C].

## 12. Per-trade_type entry table

| Item | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Primary setups (04 5.2) | S1, S2, S9, S10, S11, S13 (S14, S15 high risk) | S1, S2, S3, S5, S7, S9, S12, S13 | S3-S7, S12 (weekly) | S4, S5, S6; S1 on the 40-week as zone tranches |
| Trigger chart | daily | daily | weekly (daily timing) | weekly (daily fine entry) |
| Default trigger | T5, T9; T2 (`close`) / T1 (`intraday`) | T2/T1, T5, T6, T9 | T3; T5 on weekly | T3; T4 zone tranches |
| Volume | RVOL >= 1.5 (breakout) or pullback RVOL < 1.0 | RVOL >= 1.4 | week RVOL >= 1.2 | week RVOL >= 1.2 or OBV 26-week high |
| Max extension (`01` 9.2) | d <= 3 vs SMA20/EMA21 | d <= 5 vs SMA50 | d <= 3 weekly ATR vs 10-week | <= 40% above 40-week |
| Stale limit | 3% + re-price + 0.5 ATR | 3% + re-price + 1.0 ATR | 3% + re-price + 0.5 weekly ATR | same, and <= 5% above P |
| Validity | 5 sessions (T4: 3) | 10 (T4: 5) | 20 (T4: 10) | 40 (T4: 20) |
| Tranches | 1 | 1 or 2 (60/40 to 2/3 + 1/3) | 2-3 (1/2 + 1/4 + 1/4) | 2-4 (pilot 1/4-1/2) |
| Add trigger | none | close >= e + 0.5R after >= 2 bars, or T6 hold | weekly close above the post-breakout high, or first pullback holding the 10-week SMA | new weekly base breakout, or post-report weekly close above the pre-report level |
| Max adds | 0 | 1 | 2 | 3 |
| Regime minimum | not risk_off (grade A exception) | same | risk_off: stage 1->2 leaders only | SPY above its 10-month SMA, or stage 1->2 leaders |
| Earnings | exit before the report or wait | no entry in the 10 sessions before; let it report | pilot before, add after | tranche around it |
| Human order | stop-limit (limit = cap), near-close buy, or T4 limit | same | Friday near close or Monday open, within the cap (weekend gap, `05` 7.5) | zone limits; near-close buys on weekly triggers |
| Progress check / max hold after fill (`08` 4) | +0.5R by bar 5 / 15 bars | bar 10 / 40 bars | week 6 / 26 weeks | week 13 / 52-week re-underwrite |
| Pipeline horizon | `swing` | `swing` | `swing` if max hold <= ~3 months, else `long_term` | `long_term` |

All thresholds [C] house defaults unless labelled above.

## 13. Position sizing basics (context only; the pipeline does not size)

- Fixed-fractional [C]: shares = floor(account x risk_pct / (e - s)); e.g. 100,000 x 1% / 3.02 = 331 shares (about 16,590). `max_loss_per_trade_pct` limits stop distance, not portfolio risk; the human picks risk_pct.
- Tranches: size the full position from the worst fill state's risk, or size the pilot from the full risk budget and let adds use only risk freed by the stop raise (10.2 rule 4) [C].
- Event or gap risk inside the hold: realised loss can exceed e - s (section 11); practitioners size down [C].
- Kelly (1956) needs a known edge [A]; chart edges are too uncertain for it [C]. Details: `08` 10.1.

## 14. Entry fields a plan should carry

`08-trade-plan-and-timeline.md` 12 owns the schema. role.md requires `entry` and `entry_condition` today; put the rest in `entry_condition` and `## Plan` until the schema adopts them.

```yaml
plan:
  entry: 50.12                      # first trigger; used by the rule checks
  entry_condition: "daily close above 50.12 (pivot 50.00 + 0.1 x ATR14 1.20); do not fill above 50.46; valid until 2026-10-09"
  entry_plan:
    state: pending                  # pending | triggered (section 3.0)
    trigger_type: close_breakout    # buy_stop_breakout | close_breakout | weekly_close_breakout | limit_pullback | reversal_pullback | retest | anticipatory | gap | reclaim
    pivot: 50.00
    buffer: {value: 0.12, basis: "0.1 x ATR14 1.20"}
    confirmations: "RVOL >= 1.4; CLV >= 0; SPY not risk_off; grade A (5 of 7)"
    fill_assumption: trigger_close  # max(open,trigger) | trigger_close | next_open | min(open,limit)
    stale_cap: 50.46                # section 8.3
    order_hint: "buy stop-limit 50.12 / limit 50.46, or buy near the close if 50.12 <= price <= 50.46"
    gap_rule: "open > 50.46: cancel for the day; open < 47.10: cancel the plan"
    valid_until: 2026-10-09         # as_of + validity window (section 9)
    cancel_if: ["close below 47.10", "new swing high above 50.60 without a trigger", "earnings within 10 sessions", "regime drops a class"]
    tranches:
      - {fraction: 0.6, trigger: "the entry above"}
      - {fraction: 0.4, trigger: "close >= 51.65 after >= 2 bars, no close below 50.00", stop_after: 49.70}
    worst_fill_state: {state: "tranche 1 only", max_loss_pct: 6.0, reward_to_risk: 2.34}
    earnings_rule: "report 2026-12-10 (confirmed) is after the latest max-hold date; no action"
  invalidation: "close below 49.40 (P - 0.5 ATR) within 5 bars of entry; MFE < +0.5R by bar 10; max hold 40 bars"
```

Show every number's inputs in the analysis (`shared.md`).

## 15. Entry checklist

1. Setup named (04 ID); levels from the trade_type's primary chart; context trend agrees (`01` 13); entry state decided (3.0).
2. Trigger chosen (3.0) in the profile's `level_trigger` mode; P, buffer and ATR shown (4); round-number adjustment applied.
3. Exit plan written before entry: chart stop, target, invalidation (incl. failed-breakout line), progress check and max-hold date (`07` 2, `08` 4). No open-ended trade.
4. `max_loss` and `reward_to_risk` at e = trigger; stale cap computed (8.3); current price checked against the 3% rule, the re-price test and the ATR distance.
5. Confirmations graded (5.2); mandatory cues pass; regime and sector read from SPY/QQQ and the sector ETF, not assumed.
6. Every red flag in section 6 checked: a "reject" row -> reject; a "wait" row -> no trigger now, keep the plan only inside the validity window.
7. Gap instructions written for the human (section 7): above the cap, below the stop.
8. Earnings date found (role step 4); section 11 applied; M and Mmax computed if a report is inside the hold.
9. `valid_until` is a date; cancel conditions listed (section 9).
10. Tranches decided (10.1); add conditions, stop raises, max adds stated; every fill state checked, worst reported; no averaging down.
11. Re-entry status noted if this setup was already stopped out (3.3).
12. Plan fields filled (14); horizon mapped to `swing` / `long_term`; nothing dated after `as_of` used.

## 16. Shorts (mirror notes, only if `allow_short: true`)

Mirror every rule: sell-stop below support P - b; close confirmation below; limit sells into resistance; stale when price has fallen past the cap; add only to a short in profit; never add to a losing short. Extra cautions [C]: squeezes and positive news gaps exceed stops; check short interest and borrow if available; avoid shorts into earnings. With the long-only default, `profile_short` rejects these plans.

## Sources

- Bernard, V. and Thomas, J. (1989). Journal of Accounting Research 27 (post-earnings drift).
- Bhattacharya, U., Holden, C. and Jacobsen, S. (2012). Management Science 58(2), 413-431. https://pubsonline.informs.org/doi/10.1287/mnsc.1110.1364
- Brock, W., Lakonishok, J. and LeBaron, B. (1992). Journal of Finance 47(5), 1731-1764. https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1992.tb04681.x
- Bulkowski, T. Encyclopedia of Chart Patterns (2nd ed., 2005); https://thepatternsite.com/TrickThrow.html , https://thepatternsite.com/throwbacks.html , https://thepatternsite.com/Volume.html , https://thepatternsite.com/studystudy.html (read via search summaries; figures labelled "as summarised")
- Connors, L. and Alvarez, C. High Probability ETF Trading (2009). Connors, L. and Raschke, L. Street Smarts (1995) (Turtle Soup).
- Cooper, M., Gutierrez, R. and Hameed, A. (2004). Market states and momentum. Journal of Finance 59.
- Edwards, R. and Magee, J. Technical Analysis of Stock Trends. Murphy, J. Technical Analysis of the Financial Markets. Elder, A. Trading for a Living.
- Faber, M. (2007). A quantitative approach to tactical asset allocation. Journal of Wealth Management.
- Faith, C. The Original Turtle Trading Rules. https://oxfordstrat.com/coasdfASD32/uploads/2016/01/turtle-rules.pdf
- Frazzini, A. and Lamont, O. (2007). NBER w13090 (earnings announcement premium). https://www.nber.org/papers/w13090
- George, T. and Hwang, C.-Y. (2004). The 52-week high and momentum investing. Journal of Finance 59, 2145-2176. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00695.x
- IBD follow-through and distribution days: https://finance.yahoo.com/news/day-tells-time-buy-stocks-215900253.html
- Jegadeesh, N. (1990). Journal of Finance 45. Lehmann, B. (1990). QJE 105. Jegadeesh, N. and Titman, S. (1993). Journal of Finance 48.
- Kelly, J. (1956). Bell System Technical Journal.
- Linnainmaa, J. (2010). Journal of Finance 65(4), 1473-1506. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2010.01576.x
- Martineau, C. (2022). Rest in peace post-earnings announcement drift. Critical Finance Review 11(3-4). https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607
- Minervini, M. Trade Like a Stock Market Wizard (2013); https://traderlion.com/lesson/lesson-7-progressive-exposure-the-minervini-method/ . Morales, G. and Kacher, C. Trade Like an O'Neil Disciple (2010).
- Moskowitz, T. and Grinblatt, M. (1999). Journal of Finance 54. Moskowitz, T., Ooi, Y. H. and Pedersen, L. H. (2012). Journal of Financial Economics 104(2). https://www.sciencedirect.com/science/article/pii/S0304405X11002613
- Nagel, S. (2012). Evaporating liquidity. Review of Financial Studies 25(7).
- Odean, T. (1998). Journal of Finance 53. https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00072
- O'Neil, W. How to Make Money in Stocks. https://en.wikipedia.org/wiki/CAN_SLIM , https://marketsmithin.substack.com/p/3-smart-ways-to-manage-your-portfolio
- Osler, C. (2003). Journal of Finance 58; (2005) Journal of International Money and Finance 24. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf
- Park, C.-H. and Irwin, S. (2007). Journal of Economic Surveys 21, 786-826. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-6419.2007.00519.x
- Savor, P. and Wilson, M. (2016). Journal of Finance 71.
- SEC Investor Bulletin: Stop, Stop-Limit, and Trailing Stop Orders. https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15
- Sullivan, R., Timmermann, A. and White, H. (1999). Journal of Finance 54. https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00163
- Tharp, V. Trade Your Way to Financial Freedom. LeBeau, C. and Lucas, D. Technical Traders Guide to Computer Analysis of the Futures Market.
- Vanguard Research (2012) Dollar-cost averaging just means taking risk later: https://static.twentyoverten.com/5980d16bbfb1c93238ad9c24/rJpQmY8o7/Dollar-Cost-Averaging-Just-Means-Taking-Risk-Later-Vanguard.pdf ; (2023) Cost averaging: invest now or temporarily hold your cash? https://corporate.vanguard.com/content/dam/corp/research/pdf/cost_averaging_invest_now_or_temporarily_hold_your_cash.pdf
