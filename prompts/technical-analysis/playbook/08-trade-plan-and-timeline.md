# 08 - Trade plan and timeline

## How to use this file

- Every plan carries three barriers (stop, target, time) and five clocks: entry expiry, progress time stop, checkpoints CP1/CP2, T1 deadline, max hold. Defaults: section 4 (setup overrides 4.1); time to target: 5; checkpoints: 6; events: 7; when a clock runs out: 8.
- Build the plan by filling the YAML template (12.1; examples 13), then run the checklist (14). `[current]` fields exist in role.md's output today; `[proposed]` fields go into `entry_condition`, `invalidation` and one-line items in `## Plan` until the pipeline adopts them (12.2).
- Labels: [A] academic/replicated, [P] practitioner study, [C] convention or house default (a starting value chosen for this playbook, not a published result), [S] speculative/contested; [A math] = exact under its model (random walk, continuous monitoring), approximate for real prices. All examples are hypothetical.
- Neighbours: `01-chart-reading.md` (RS 11, regime 12), `02-indicators.md`, `03-chart-patterns.md` (failed breakout 4.15), `04-strategies-and-setups.md` (cards S1-S15), `05-timeframes-and-trade-types.md` (type choice 11, reachability k 5.3, fill ceiling 7.5, graduation 13), `06-entries.md` (re-entry 3.3, stale cap 8, validity 9, tranches 10, earnings 11), `07-exits.md` (stops, trails, scale-out), `09-events-hype-and-fear.md`. "Sizing: 08" in siblings means 10.1. Canonical names, notations and default numbers: `CONVENTIONS.md` (wins over any older value in a topic file).

## 1. Evidence ledger

- **Effect horizons [A]:** short-term reversal ~1 week-1 month (Jegadeesh 1990; Lehmann 1990); momentum 3-12 months (Jegadeesh and Titman 1993); time-series momentum to ~12 months, then partial reversal (Moskowitz, Ooi and Pedersen 2012); long-term reversal 3-5 years (De Bondt and Thaler 1985); post-earnings drift ~ the next quarter (Bernard and Thomas 1989, 1990). -> Max hold <= the horizon of the effect claimed (04 1.5). At 1 week-1 month the effect is REVERSAL: short continuation (flags) rests on [P]/[C]; short pullbacks inside a longer uptrend fit both effects.
- **Disposition effect [A]** (Shefrin and Statman 1985; Odean 1998): winners sold early, losers held. -> Exits and clocks written BEFORE entry; never extend a clock on a loser.
- **Stops help only with persistent returns [A]** (Kaminski and Lo 2014). -> Stops and time stops test the claimed drift.
- **Random-walk math [A math]**, approximate for fat-tailed, gapping prices: P(touch d within n bars) = 2(1 - Phi(d / (sigma_1 sqrt n))) (reflection); with drift mu first passage is inverse Gaussian, mean d / mu; daily sigma ~ ATR / 1.6 (expected one-period Brownian range = sqrt(8/pi) sigma: Feller 1951; Parkinson 1980); no drift: P(target before stop) = 1 / (1 + R:R), 33% at 2.0 = break-even. -> Without drift, time to target grows with distance SQUARED (5.1); a high R:R is no edge: name the drift.
- **Triple barrier [C]** (Lopez de Prado 2018): profit take, stop, time barrier. -> Every fill gets a gradeable outcome.
- **"Time stops improve results" [S]** (no rigorous general study found); fixed-hold exits to test an entry's edge are standard system-testing practice [C] (Kaufman). -> Time stops test for drift and free capital.
- **Big winners [P]:** trend-following payoffs come from a minority of large winners held long (Wilcox and Crittenden 2005); O'Neil's 8-week hold for a stock up 20%+ within 3 weeks of a breakout [C]. -> A trending winner at a limit is graduated or re-underwritten (8, 9), never silently extended.
- **Time symmetry [S]** ("a measured move takes as long as the pattern took") is untested; Bulkowski's statistics run to the "ultimate high" (peak before a 20%+ decline) [P]. -> Pattern duration is only a range top (M4); his rise figures are not T1 timing.
- **Events** [A]/[S] per row of 7.1; **MAE/MFE** tracking (Sweeney 1996) [C] -> record on every exit (15).

## 2. Principles

1. **No open-ended trade.** A plan ends at exactly one of: stop, final target, trail, invalidation, time stop, T1 deadline, max hold, event exit, thesis break, entry expiry; each has a price or a date.
2. **Three barriers or no plan.** Missing stop, target or time barrier = incomplete: reject it yourself.
3. **Clocks are set before entry and never silently extended**; a clock ends only in the actions of section 8.
4. **Time is part of the thesis.** "Right but late" is treated as wrong.
5. **Losers are never renewed or graduated.**
6. **Risk never increases after entry.** Stops move only toward the trade (07); renewals and graduations use a stop at or above the one in force.
7. **Decision support only.** The plan tells the human what to do and when.

## 3. Lifecycle

### 3.1 Phases

| Phase | Starts when | Monitored | Ends when (-> next) | Who checks today |
|---|---|---|---|---|
| `watch` | setup forming, not actionable | trigger conditions completing | completes -> plan (`pending`); fails or watch expiry -> drop | technical agent (verdict `reject` + watch note) |
| `pending` | plan published with trigger and `valid_until` | trigger, cancel_if, stale cap, events entering the no-entry zone | fill -> `open`; `valid_until` -> `expired`; cancel_if -> `cancelled`; price past stale cap unfilled -> `missed` | follow-up (missed entry only) |
| `open` | first tranche filled (bar 0) | stop, progress stop, CP1, events | stop -> `closed`; CP1 passed or T1 hit -> `managing`; progress fail -> exit/reduce (6.3) | follow-up (stop only) |
| `managing` | CP1 passed or T1 partial taken | stop raises, adds, scale-outs, trail, CP2, T1 deadline, max hold, events | final target, trail, invalidation, time limit, event exit, thesis break -> `closed`; renewal/graduation -> new plan | follow-up (stop/target/news) |
| `closed` | fully exited | - | post-trade record (15) | user via `/trade`; evaluator |

Terminal codes: `expired`, `cancelled`, `missed` (never entered); `stop`, `invalidation`, `target_final`, `trail`, `time_progress`, `time_t1`, `max_hold`, `event_exit`, `thesis_break`, `renewed`, `graduated`. After `stop` or `invalidation`, re-entry is a NEW plan under 06 3.3 (once per setup, fresh trigger, never the same day).

### 3.2 Bar counting

- Bar 0 = fill bar (the trigger close under `level_trigger: close`; the fill session for stop/limit orders); bar n = n-th completed session after it. Weekly plans: week 0 = fill week, valued at its last close.
- Count NYSE sessions. With no holiday data, count weekdays and say so (a holiday then makes a date one session early: the conservative side). 252 sessions ~ 365 calendar days.
- Daily checkpoints are judged on that bar's close (16:00 New York); weekly ones on the week's last close.
- The fill date is unknown at plan time: state each post-fill clock as "bar N after fill" AND the latest date = `valid_until` + N sessions. Check events through the latest max-hold date.

### 3.3 What resets a clock [C]

| Action | Clock effect |
|---|---|
| Later tranche or pyramid add | none: clocks run from tranche 1's fill; no adds after CP2 |
| Scale-out, stop raise, trail switch | none |
| Unfilled conditional tranche | expires at its own date, else at CP2; never fills after the T1 partial |
| Renewal (8.1) or graduation (9) | new plan, new id, clocks restart from its date |
| Anything else ("give it another week") | forbidden |

## 4. Clocks per trade_type (canonical)

All values [C] house defaults; 01-07 and 09 cite this table and `CONVENTIONS.md` summarises it.

| Clock | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Watch expiry (from as_of) | 10 sessions | 20 sessions | 8 weeks | 13 weeks |
| Entry validity `valid_until` | 5 sessions | 10 sessions | 20 sessions | 40 sessions |
| Progress stop = default CP1 (latest): MFE >= +0.5R | bar 5 | bar 10 | week 6 | week 13 |
| Progress fail action (07 11) | exit | halve, stop to last higher low | halve, tighten | reduce |
| Default CP2 (latest): close >= +1R or new swing high above the entry-time high | bar 10 | bar 20 | week 13 | week 26 |
| T1 deadline | min(max hold, 2 x E) | same | same | same |
| Max hold | 15 bars | 40 bars | 26 weeks | 52 weeks per plan (multi-year = chain of annual plans) |
| Same-type renewals | 1 | 1 | 1 | unlimited, each a full re-underwrite |
| Stop checked on | daily close | daily close | daily close (hard stop); weekly close (invalidation) | same |
| Full review (05 9) | every 2-3 sessions | weekly | weekly; deep every 4 weeks | monthly + after each report |
| Pipeline horizon | `swing` | `swing` | `swing` if max hold <= ~13 weeks, else `long_term` | `long_term` |
| Earnings (09 4, 06 11) | no report between entry and latest max hold + 2 sessions (shorten max hold to end >= 1 session before it, else reject) | cushion rule at the last close before (09 4.2); no new entry in the last 10 sessions | pilot <= 1/3 before, add after | tranche around reports |

E = expected bars/weeks to T1 (5). Plan checkpoints = the EARLIER of the 6.1 formula and these defaults. Holds follow the ledger's horizons [A], mapping [C]: short_swing = reversal window (buy pullbacks, do not chase); swing = ~60-session drift window; long_swing = 3-12 month momentum; investment re-underwrites yearly (~12 months = longest documented continuation).

### 4.1 Setup-specific clocks (use when earlier) [C]

| Setup family (04) | Earlier clock | If it fails |
|---|---|---|
| Daily breakout (S3, S5, S7) | close below pivot - 0.5 ATR in bars 1-5 (03 2.6, 4.15); close >= pivot + 1R within 10 bars (swing) | exit (structure) / halve (progress) |
| Weekly breakout (S3 weekly, S6) | new weekly high within 6 weeks | halve, stop to last weekly higher low |
| Pullback / retest (S1, S2) | close above the prior bar's high within 3-5 bars of the fill | exit |
| Squeeze / NR7 (S9) | range expansion in the trade direction within 3-5 bars | exit |
| Mean reversion (S10, S11, S14, S15) | S10 max hold 5-8 bars; S14 5 bars; S11 the median prior support-to-resistance traverse; S15 CP bar 5, max 10-15 bars; all exit fully at target, no runner (04 1.6) | exit |
| Post-report drift (S13) | max hold inside ~60 sessions after the report [A window; weak in large caps today, Martineau 2022]; the next report is an event exit | exit or graduate |

## 5. Expected time to target

Estimate E (sessions for daily plans, weeks for weekly) to T1, and to T2 if planned. Show inputs.

### 5.1 Methods

| Method | Formula (from the bars) | Gives | Label |
|---|---|---|---|
| M1 ATR floor | n_min = ceil(d / ATR14), d = T1 - entry | rough lower bound (gaps and flag poles beat it briefly; sustained trends rarely). n_min > max hold -> reject | arithmetic; "rarely" [C] |
| M2 Noise-only median | n_50 = (d / (0.674 x sigma_1))^2, sigma_1 = 0.63 x ATR14 (daily) or weekly ATR14 / 1.6; shortcut 5.5 x (d / ATR14)^2 | median first-touch time with NO edge | [A math] |
| M3 Leg analog | last 2-4 completed legs in the trade direction (hook pivots): v_i = (leg high - leg low) / (ATR then x bars in leg); v = median; E = (d / ATR14) / v | time at this stock's own trend speed; primary when >= 2 comparable legs | [C] |
| M4 Formation symmetry | E_hi = bars the pattern took to form; flags: the pole is the analog leg | range top for measured moves | [S]; pole analog [C] |
| M5 Drift model (optional) | drift mu per bar (e.g. v x ATR): mean time d / mu; P(touch by t) = Phi((mu t - d)/(sigma_1 sqrt t)) + exp(2 mu d / sigma_1^2) x Phi((-d - mu t)/(sigma_1 sqrt t)) | chance of T1 by the deadline IGNORING the stop (overstates a win) | [A math]; mu [S] |

Square-root-of-time: typical excursion after n bars ~ sigma_1 x sqrt(n), so reachability k = d / (sigma_1 x sqrt(max hold)) (05 5.3; keep k <= 1.5). M2 medians (daily bars): d = 2 ATR -> ~22; 3 -> ~50; 4 -> ~88; 6 -> ~198. Noise-only chance of touching T1 within the max hold (reflection, sigma_1 = 0.63 ATR, no stop):

| d (daily ATR) | within 15 bars (short_swing) | within 40 bars (swing) |
|---|---|---|
| 2 | ~41% | ~62% |
| 3 | ~22% | ~45% |
| 4 | ~10% | ~32% |

These are upper bounds: close-confirmed levels are reached less often than touched ones, and with a stop and no drift P(T1 first) = 1 / (1 + R:R). Beyond ~3 ATR a short_swing needs demonstrated drift (M3) or a longer type.

### 5.2 Combining (house rule [C])

1. Central E = M3 if >= 2 comparable legs (same trend stage, similar ATR%); else M4; else M2 halved, marked "low confidence". Range = [min, max] of methods computed; floor = M1. M3 and M4 differ > 2x: say so, M4 = range top.
2. Completed legs are the ones that worked, so M3 is optimistic: hence T1 deadline = 2 x E.
3. In risk_off (01 12.2) legs from a risk_on period overstate speed: use the slowest leg, not the median.
4. Reject or change type if E > 2/3 x max hold, M1 > max hold, or k > 1.5. Never lengthen max hold to fit.
5. Report `expected_days_to_t1: {estimate, range, floor, method}`, same for T2.

### 5.3 Worked example (hypothetical, swing)

XYZ daily flat base, 30 sessions, 42.50-50.00 (height 7.50); last higher low 47.40; ATR14 1.20. Entry 50.12, stop 47.10 (47.40 - 0.25 ATR; R 3.02), T1 57.20 (d 7.08 = 5.90 ATR), T2 61.10 (9.15 ATR).
- M1: 6 bars (T2: 10). M2: 5.5 x 5.90^2 = ~191: without drift the trade fails.
- M3: leg A 40.10 -> 49.30 in 24 bars at ATR 1.10 = 0.348 ATR/bar; leg B 43.00 -> 50.00 in 20 bars at ATR 1.15 = 0.304; v = 0.326; E(T1) = 18, E(T2) = 28.
- M4: base 30 bars = range top (measured move 57.50; T1 sits under it).
- E(T1) = 18 (range 18-30, floor 6) <= 26.7: fits swing. k = 7.08 / (0.63 x 1.20 x sqrt 40) = 1.48: needs a named tailwind in `## Setup`.
- Clocks: CP1 = min(6, 10) = bar 6; CP2 = min(12, 20) = bar 12; T1 deadline = min(40, 36) = bar 36; max hold bar 40.

## 6. Time stops and checkpoints

### 6.1 Definitions and formulas

- R = E_blend - s_initial (filled tranches). Open R = (close - E_blend) / R. MFE_R = (highest close since fill - E_blend) / R under `level_trigger: close` (highest high under `intraday`); MAE_R likewise with lows.
- **Progress time stop:** MFE_R < +0.5 by the progress bar (4, 4.1, or CP1 if earlier) -> the type's fail action. A valid breakout or pullback shows follow-through early (06 5); its absence says the drift is missing [C].
- **CP1** = min(round(E / 3), default CP1), at least bar 2 (week 2). **CP2** = min(round(2E / 3), default CP2), at least CP1 + 1. **T1 deadline** = min(max hold, 2 x E).

### 6.2 What to check

| Check | CP1 (~1/3 of E) | CP2 (~2/3 of E) |
|---|---|---|
| Progress | MFE_R >= +0.5 | close >= +1R, or a new swing high above the entry-time high |
| Structure (hook pivots) | no close below pivot - 0.5 ATR (03 2.6); pullbacks: higher low intact | higher low above the entry-time low; no lower high |
| Trend line (02) | short_swing above EMA10; swing above EMA21; weekly types: weekly close above the pivot | swing above SMA50; long_swing weekly above 10-week SMA; investment above a rising 30-week SMA |
| RS (01 11) | RS vs SPY and sector ETF not at a new low since entry | RS flat or rising since entry |
| Volume (02 7.11) [C] | up/down volume ratio since entry >= 1 | no cluster of >= 3 down closes on RVOL > 1.3 within 10 bars |
| Regime (01 12) | SPY class not lower than at entry | same |
| Clock | E' = bars elapsed + remaining distance / current velocity; E' > T1 deadline = progress fail | same |
| Events | an event before the next checkpoint: apply its rule (7) | same |

### 6.3 Decision at a checkpoint (first matching row wins)

| Result | Action |
|---|---|
| Structure fails (close back in base, lower low, invalidation line) | exit at the close, whatever the progress |
| Event before the next checkpoint | apply the event rule; it overrides "continue" |
| Progress fails, structure intact | CP1: the type's fail action (4). CP2: stop to breakeven (E_blend) or exit |
| Progress passes, RS or regime fails | continue; stop to last higher low; no adds |
| All pass | continue; trail per rule; adds only before CP2 |

### 6.4 Gaps and fills while open [C]

| Situation (daily bars) | Action for the human |
|---|---|
| Open gaps below the stop | exit at the open; record realised R (worse than -1R) |
| Open gaps above T1 | take the T1 partial at the open; rest per scale-out plan |
| Stop and target both inside one bar (`intraday` trigger) | assume the stop came first (the only safe reading of a daily bar) |
| Weekly plan, stop hit midweek | the daily-close hard stop acts; weekly invalidation is checked only on the week's close |

## 7. Event calendar in the timeline

### 7.1 Event table

| Event | Source | Evidence | Timeline rule |
|---|---|---|---|
| Earnings | `GetUpcomingInvestorEvents`; else same quarter last year +/- 7 days [C] from 8-K item 2.02 dates (`ListFilings`), marked estimated | later-than-usual reports tend to carry worse news (Johnson and So 2018) [A] | per section 4; mark the report session and the one before; gaps skip stops (06 11) |
| Ex-dividend | not a technical-agent tool; dividend data elsewhere if available, else NOT CHECKED | drop ~ dividend, on average somewhat less (Elton and Gruber 1970) [A]; FINRA 5330 lowers resting buy-limits and sell-stops by the dividend unless "do not reduce" | 7.3 |
| Index events: S&P quarterly rebalance (after the close on the third Friday of Mar/Jun/Sep/Dec, with quarterly expiration); Russell reconstitution (historically June; a move to semi-annual from 2026 was announced, not re-checked here) | calendar [C]; index-change data if available | addition effects (Shleifer 1986; Harris and Gurel 1986, largely reversed within weeks) much smaller or gone lately (Patel and Welch 2017; Greenwood and Sammon 2022) [A], current size [S] | ignore RVOL on those sessions; no volume-confirmed trigger on them alone |
| Macro: FOMC, CPI, payrolls | upstream economic calendar (market scanner) if present, else NOT CHECKED | higher returns on announcement days (Savor and Wilson 2013) [A]; pre-FOMC drift (Lucca and Moench 2015) reported gone after 2011 (Kurov, Wolfe and Gilbert 2021) [S] | list dates in the hold; stop < 1.5 ATR away: say a macro day can hit it; never move stops for it |
| Monthly options expiration | calendar | "pinning" [S] | information only |
| Company events (investor day, FDA, vote, lockup) | `GetUpcomingInvestorEvents`; others if available | lockup expiries: negative abnormal returns, volume jump (Field and Hanka 2001) [A] | binary events = earnings rules (09) |

### 7.2 Building the timeline

1. List every dated item from `as_of` to the latest max-hold date: `valid_until`, progress bar, CP1, CP2, T1 deadline, max hold, each event and the session before each report. Sort by date.
2. A checkpoint on or within 1 session after a report is evaluated on the session BEFORE it (decide while the stop still bounds risk).
3. Every report inside the window gets: "on the close of <date - 1>: if open R < X exit/halve, else hold with stop at Y" (default X = 1R for swing; cushion rule 09 4.2).
4. A report that makes a type unworkable removes that type (05 11 step 6); never shrink max hold below E to dodge it.
5. Write in `## Plan`: `Timeline: valid until 10-09 | CP1 bar 6 | CP2 bar 12 | decide 11-04 before report 11-05 | T1 by bar 36 | max hold bar 40 (latest 12-07)`.

### 7.3 Ex-dividend

- Put an ex-date inside the hold in the event plan if the dividend >= 0.1 x ATR14.
- Equibles bars are split-adjusted (docs/operations.md); dividend adjustment is undocumented: an unexplained gap ~ the dividend on the ex-date bar means unadjusted.
- A close-based stop within one dividend of price can trip on the distribution alone: write "on ex-date <date>, compare the close with stop - dividend" and tell the human a resting sell-stop is lowered by the dividend unless marked do-not-reduce (sell-limit targets are not).

## 8. At the time limit

A time limit (progress stop, setup clock, T1 deadline, max hold) forces a decision on that bar's close; "nothing" is not an option. First matching row wins:

| State at the limit | Action | Code |
|---|---|---|
| Open R < 0 | exit at the close (next open if the close has passed) | `time_*` |
| 0 <= open R < 1, no fresh setup | exit | `time_*` |
| Open R >= 1 and a LONGER type qualifies now (05 13.1) | graduate (9) | `graduated` |
| Open R >= 0, a fresh SAME-type setup (own pivot and stop), renewal count allows | re-underwrite (8.1) | `renewed` |
| T1 deadline, open R >= 1, T1 not hit, nothing qualifies | reduce: sell half, stop to max(E_blend, last higher low) | - |
| Max hold, runner on a trail after T1 | exit the runner, or re-underwrite it | `max_hold` / `renewed` |
| Investment at 52 weeks | re-underwrite with a fresh upstream thesis and chart; none -> exit | `renewed` / `max_hold` |

"Reduce" is allowed once per plan: half size, stop to the last higher low (never lower), new limit = half the remaining bars of the window.

### 8.1 Re-underwrite procedure

1. Pretend you are flat: current close = new entry e'. Old entry and open profit are irrelevant (standard remedy for the disposition effect: bias [A], remedy [C]).
2. New structural stop s' >= the stop in force; new T1' from the current chart; recompute E', checkpoints and max hold from today.
3. Run every role.md rule on (e', s', T1'). Any reject -> exit.
4. Record `parent_plan`, `renewal_count`, reason, date: a new plan, never an edited old one.

## 9. Rolling into a longer trade_type (graduation)

Conditions in 05 13.1 (open profit >= 1R or T1 reached; the longer type's charts qualify NOW; its structural stop at or above the original entry; no report within ~2 weeks unless the cushion rule passes). Take the planned T1 partial first. Record:

```yaml
graduation:                      # [proposed]
  parent_plan: <analysis path or id>
  from_type: swing
  to_type: long_swing
  date: 2026-11-20
  partial_taken: "1/3 at T1 57.20"
  new_stop: 51.40                # >= original entry 50.12: the rest cannot become a loss
  new_primary_chart: 1w
  new_targets: {t1: 66.00, method: "weekly measured move", k: <re-checked>}
  clocks_restart: true           # CP1/CP2/T1 deadline/max hold from `date`
  horizon_change: "swing -> long_term (new max hold 26 weeks > ~13)"
```

Forbidden (05 13.3): graduating a loser, widening a stop, averaging down. Degradation (longer -> shorter, 05 13.2) is allowed and tightens stop and clocks.

## 10. Scale-out, trailing and blended R

Owned by `07-exits.md`; the plan must state:

| Item [C] | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Scale-out | all at T1, or 1/2 at T1 + tight trail to max hold (mean reversion: all at target) | 1/2 at T1, 1/2 at T2 or trail | 1/3 T1, 1/3 T2, 1/3 trail | trim 1/4-1/3 at T1; rest on weekly trail |
| Trail after T1 | 2-bar pivot low - 0.25 ATR or close below EMA10 (tight mode: prior bar's low) | close below EMA21, or chandelier (highest high since entry - 3 x ATR; LeBeau's original: 22-bar highs, ATR22) | weekly close below 10-week SMA | weekly close below 30-week SMA (Weinstein) |
| Stop after T1 partial | max(breakeven, last higher low) | same | same | last weekly higher low |

Mean-reversion setups exit fully at target; trend setups keep a runner (04 1.6; 07 7). Formulas (Tharp R-multiples [C]):
- R_i = (T_i - E_blend) / R. Blended R = sum(f_i x R_i) (value the trail portion at its planned target or at breakeven; say which). Floor after T1 = f_1 x R_1.
- **`reward_to_risk` is checked on T1 = `target`** (04 1.4, 07 6.4 agree): role.md checks the single `target` field and the follow-up agent uses it as its target tripwire. Blended R is information only.
- Expectancy = p_win x avg win R - (1 - p_win) x avg loss R. State p_win only from a named study or the pipeline's own records (15); the no-edge baseline is 1 / (1 + R:R).

### 10.1 Position size (information for the human)

The profile has no account size and role.md no size field: give a formula, never an invented share count.
- shares = floor(B / (E_blend - s)), B = the human's risk budget per trade (fixed-fractional, Tharp [C]). `max_loss_per_trade_pct` limits stop distance as % of price, NOT account risk.
- Tranches: worst fill state keeps sum(shares_i x (e_i - s_current)) <= B [arithmetic]. Half risk (0.5 x B) when a sibling says so or for a pilot before a report (06 10) [C].
- Gap allowance: a stop is not a guaranteed price; with a report or binary event in the hold, state the loss at the stock's own past report gap beside R (05 7.5 worst-case line) [C].
- Volatility scaling improved momentum and factor portfolios (Barroso and Santa-Clara 2015; Moreira and Muir 2017) [A, portfolio level]; 0.5 x B for one trade when SPY is risk_off or HV20 stressed is [C].
- Stop-distance sizing already scales by volatility; never shrink a stop to "afford" more shares.

## 11. Review cadence and the follow-up agent

### 11.1 How the pipeline watches a position today

- `/follow-up` ticks at 10:00, 12:00, 14:00 and 16:15 New York on weekdays (docs/operations.md). Tripwires: stop, target, missed entry (price > 3% past entry, or through the stop, before a fill), material news. Alerts within 12 hours of the last alert are held. A full re-review runs on a delivered alert or every 14 days and recommends `hold`, `adjust_plan` (a complete new plan passing role.md rules: where renewals and graduations land) or `exit`.
- Under `level_trigger: close`, only the 16:15 tick confirms a stop, target or checkpoint; midday ticks are warnings.

### 11.2 Mapping and gaps

| | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| 14-day re-review vs needed cadence (4) | too slow: a 15-bar trade may get one | too slow | adequate for the deep review | adequate |
| Checkpoints, time stops | not tripwires: put them in `invalidation` (any re-review applies them) and the Timeline line for the human | same | same | same |
| 12h cooldown | a 10:00 news alert holds a 16:15 stop alert to next morning | same | lower impact | lower impact |
| Earnings | material news triggers a re-review only AFTER the report: the pre-report decision must be in the plan text | same | same | same |

### 11.3 Proposed extensions (not implemented; do not assume)

1. Alert kind `time` for `valid_until`, progress bar, CP1, CP2, T1 deadline, max hold and the pre-report decision date.
2. Stop, target and max-hold alerts bypass the 12h cooldown.
3. Full re-review interval per trade_type: 3 / 5 / 10 / 20 sessions.
4. Evaluator closes a filled plan with no stop or target hit at its `max_hold_date` close (`time_exit`, realised R); today it stays `open` / `worked: null`.
5. Position file carries `trade_type`, `valid_until`, `max_hold_date`, checkpoints, tranches and scale-out.

## 12. Trade plan template

### 12.1 YAML (every field)

```yaml
plan:
  # --- identity ---
  trade_type: swing                  # [proposed] short_swing | swing | long_swing | investment
  horizon: swing                     # [current] swing | long_term (section 4)
  chart_timeframe: 1d                # [current] primary chart: 1d | 1w
  setup: "S3 flat base breakout"     # [proposed] card from 04
  direction: long                    # [current, top-level field in role.md]
  phase: pending                     # [proposed] watch | pending | open | managing | closed
  regime_at_entry: risk_on           # [proposed] 01 12; a lower class later fails a checkpoint
  # --- entry ---
  entry: 50.12                       # [current] first trigger; used by rule checks
  entry_condition: "daily close above 50.12 (pivot 50.00 + 0.1 x ATR 1.20), RVOL >= 1.4; valid until 2026-10-09; void if filled above 50.46"  # [current]
  entry_plan:                        # [proposed] detail: 06 14
    trigger_type: close_breakout
    valid_until: 2026-10-09          # as_of + entry validity (4)
    cancel_if: ["close below 47.10", "new high above 50.00 without trigger (re-plan)", "report enters no-entry zone", "regime drops a class"]
    stale_cap: 50.46                 # 06 8: min((57.20 + 2 x 47.10) / 3, 47.10 / 0.92), rounded down
    fill_ceiling: 50.46              # 05 7.5: (57.20 + 2.0 x 47.10) / 3.0 = 50.4667 -> 50.46 (rounded down); above it R:R < 2.0
    tranches: [{fraction: 1.0, trigger: "the entry above"}]
  # --- risk ---
  stop: 47.10                        # [current]
  stop_method: "last higher low 47.40 - 0.25 x ATR 1.20"      # [proposed]
  worst_case: "exit 0.5 ATR below stop (46.50): -1.2R, 7.2% of entry"   # [proposed] 05 7.5
  invalidation: "close below 49.40 (pivot - 0.5 ATR) in bars 1-5; MFE < +0.5R (51.63) by bar 6; T1 by bar 36; max hold 40 bars"  # [current] time rules live here today
  # --- targets ---
  target: 57.20                      # [current] = T1; reward_to_risk is checked on it
  targets:                           # [proposed]
    - {id: T1, price: 57.20, method: "resistance 57.50 - 0.25 ATR; = base measured move", r: 2.34}
    - {id: T2, price: 61.10, method: "52-week high 61.40 - 0.25 ATR", r: 3.64}
  scale_out: "1/2 at T1, stop to 50.12; 1/2 at T2 or trail"   # [proposed]
  trailing_rule: "after T1: close below EMA21"                # [proposed]
  # --- time ---
  expected_days_to_t1: {estimate: 18, range: [18, 30], floor: 6, method: "M3 legs 0.348/0.304 ATR/bar"}  # [proposed]
  expected_days_to_t2: {estimate: 28, range: [28, 40], floor: 10, method: "M3; range top = max hold"}   # [proposed]
  time_stop: {progress: "MFE >= 51.63 by bar 6, else halve, stop to last higher low", setup_clock: "close < 49.40 in bars 1-5 = exit", t1_deadline_bar: 36}  # [proposed]
  checkpoints:                       # [proposed] bars after fill
    - {id: CP1, bar: 6, check: "MFE >= 51.63; no close < 49.40; above EMA21; RS not at new low"}
    - {id: CP2, bar: 12, check: "close >= 53.14 (+1R) or new swing high; else stop to 50.12 or exit"}
  max_hold: {bars: 40, latest_date: 2026-12-07}               # [proposed] valid_until + 40 sessions
  at_time_limit: "section 8; renewals used 0 of 1"            # [proposed]
  # --- events ---
  event_plan:                        # [proposed]
    - {date: 2026-11-05, event: "earnings (confirmed)", rule: "cushion rule (09 4.2) at the 11-04 close: OP >= 1R, stop raisable to >= 50.12 and HEM < stop distance -> hold with stop 50.12; OP >= 0.5R -> halve; else exit"}
    - {date: null, event: ex-dividend, rule: "NOT CHECKED (no dividend tool)"}
  # --- expectation ---
  rr_single: 2.34                    # [proposed] T1 vs initial stop (the rule value)
  rr_blended: {all_targets: 2.99, floor_after_t1: 1.17}       # [proposed] information only
  renewal: {parent_plan: null, renewal_count: 0}              # [proposed]
```

### 12.2 What the current output supports

| Current field (role.md) | Carries today |
|---|---|
| `entry`, `entry_condition` | first trigger + "valid until <date>" + "void if filled above <ceiling>" + tranche text |
| `stop` | initial stop |
| `target` | T1 only; T2/T3 and scale-out in `## Plan` |
| `horizon`, `chart_timeframe` | mapped from trade_type (4) |
| `invalidation` | structural line + progress stop + "T1 by bar N" + "max hold N bars (latest <date>)" |
| rules | unchanged: `reward_to_risk` on T1; `upcoming_earnings` uses the horizon window, but check events through the latest max-hold date and flag in `## Risks considered` |

Everything else is proposed: one line per item in `## Plan` ("Type:", "Timeline:", "Events:", "Scale-out:", "Worst case:").

## 13. Filled examples (hypothetical)

All: `as_of` 2026-09-25 (Friday close); `profile.example.json` (max loss 8%, min R:R 2.0, `level_trigger: close`). "CP1 bar 2 (10-05)" = the date if filled on the stated day; NYSE holidays counted (Thanksgiving 2026-11-26, Christmas 2026-12-25).

### 13.1 short_swing: ABC bull flag

Pole 70.00 -> 80.60 in 7 bars (ATR then 1.50); 6-bar flag 78.90-80.60; ATR14 1.60; resistance 85.80; report 2026-11-12 (confirmed, after the latest max hold).

```yaml
plan:
  trade_type: short_swing
  horizon: swing
  chart_timeframe: 1d
  setup: "S3 variant: bull flag breakout (03 3.3)"
  entry: 80.76
  entry_condition: "daily close above 80.76 (flag high 80.60 + 0.1 x ATR); valid until 2026-10-02; void if filled above 80.80"
  stop: 78.50                        # flag low 78.90 - 0.25 ATR; R 2.26 = 2.8%
  invalidation: "close back in the flag (< 80.60) on bars 1-2; MFE < +0.5R by bar 2; T1 by bar 8; max hold 15 bars"
  target: 85.40                      # resistance 85.80 - 0.25 ATR; 2.05R; single target
  scale_out: "1/2 at T1; rest trails (2-bar pivot low - 0.25 ATR) to max hold"
  expected_days_to_t1: {estimate: 4, range: [4, 6], floor: 3, method: "M3: pole 1.01, prior leg 0.48 ATR/bar, median 0.74; d 2.90 ATR"}
  time_stop: {progress: "MFE >= 81.89 by bar 2, else exit", t1_deadline_bar: 8}
  checkpoints: ["CP1 bar 2 (10-05 if filled 10-01): no close in flag; MFE >= 81.89", "CP2 bar 3 (10-06): close >= 83.02 (+1R) or new swing high, else stop to 80.76 (breakeven) or exit"]
  max_hold: {bars: 15, date_if_filled_2026-10-01: 2026-10-22, latest_date: 2026-10-23}
  event_plan: [{date: 2026-11-12, event: earnings, rule: "after latest max hold: none"}]
  rr_single: 2.05                   # blended floor after T1: 1.03
```
k = 4.64 / (0.63 x 1.60 x sqrt 15) = 1.19. R:R 2.05 is within 0.1 of the minimum (a warning sign per evaluation.md): say so. Fill ceiling (85.40 + 2 x 78.50) / 3 = 80.80 is only 0.04 above entry, so a next-open fill above 80.80 fails R:R; close-trigger overshoot (~0.5 ATR = a third of R here, 05 7.5) goes in the worst-case line.

### 13.2 swing: XYZ flat base breakout

The full plan is the 12.1 template (numbers from 5.3); report 2026-11-05 (confirmed, 41 days: role flag inside 45). Dated view if filled 2026-10-02: CP1 bar 6 = 10-12; CP2 bar 12 = 10-20; pre-report decision 11-04 = bar 23; max hold bar 40 = 11-30 (latest 12-07). The entry window ends 19 sessions before the report, outside the 10-session no-entry zone (06 11). The pre-report decision lands between bar 18 (fill 10-09) and bar 23 (fill 10-02), at or just after E(T1) = 18: if the trade is slower than its analog legs the pre-report rule, not T1, decides it; say so in `## Risks considered`.

### 13.3 long_swing: LMN weekly base breakout

20-week base 100.00-120.00; weekly ATR14 5.40; last weekly higher low 113.60; resistance 140-142 (= measured move 140); prior advance 88 -> 128 in 30 weeks at weekly ATR 5.0. Reports 2026-11-10 (confirmed, 46 days: outside 30) and ~2027-02-09 (estimated from last year's 8-K 2.02).

```yaml
plan:
  trade_type: long_swing
  horizon: long_term                 # max hold 26 weeks > ~13
  chart_timeframe: 1w
  setup: "S6 weekly stage-2 base breakout"
  entry: 120.54
  entry_condition: "weekly close above 120.54 (120.00 + 0.1 x weekly ATR 5.40); valid until 2026-10-23"
  entry_plan:
    tranches:
      - {fraction: 0.5, trigger: "the entry above (pilot: report inside the hold)"}
      - {fraction: 0.5, trigger: "first weekly close after the 11-10 report holding above 120.00, near 124.00", stop_after: 116.50, expires: CP2}
  stop: 112.25                       # higher low 113.60 - 0.25 weekly ATR; daily-close hard stop; R 8.29 = 6.9%
  invalidation: "weekly close below 116.00 (120.00 - 0.75 weekly ATR); MFE < +0.5R (124.69) by week 4; no new weekly high by week 6; T1 by week 26"
  target: 138.65                     # 140.00 - 0.25 weekly ATR; 2.18R
  targets: [{id: T1, price: 138.65, r: 2.18}, {id: T2, price: 158.65, method: "leg equality: prior 40-point advance from 120.00 = 160.00, - 0.25 weekly ATR [S]", r: 4.60}]
  scale_out: "1/3 T1, 1/3 T2, 1/3 on weekly close below the 10-week SMA"
  expected_days_to_t1: {estimate: 13 weeks, range: [13, 20], floor: 4 weeks, method: "M3 0.267 weekly ATR/week; d 3.35 weekly ATR; M4 base 20 weeks"}
  checkpoints: ["CP1 week 4 (11-06 if filled 10-09): MFE >= 124.69; weekly close > 120.00; pre-report decision", "CP2 week 9 (12-11): weekly close >= 128.83 (+1R) or new 52-week high; else stop to last weekly higher low or reduce"]
  max_hold: {weeks: 26, date_if_filled_2026-10-09: 2027-04-09, latest_date: 2027-04-23}
  event_plan:
    - {date: 2026-11-10, event: "earnings (confirmed)", rule: "pilot only before; tranche 2 after a post-report weekly close > 120, stop raised to 116.50"}
    - {date: ~2027-02-09, event: "earnings (estimated)", rule: "if open R < 1 on the prior close, halve"}
  rr_single: 2.18
  rr_blended: {trail_at_t2: 3.79, trail_at_breakeven: 2.26, floor_after_t1: 0.73}   # tranche 1's entry
```
Tranche check (06 10.3): both filled, E_blend 122.27; with the stop at 112.25 the loss is 8.2% and R:R 1.63 (both fail), so the add requires the stop at 116.50: 4.7% and 2.84. k = 18.11 / ((5.40 / 1.6) x sqrt 26 = 17.2) = 1.05. Weekly-close entry: the human buys Monday's open, so check the stale cap on the actual fill (weekend gap, 05 7.5).

### 13.4 investment: QRS stage 1 -> 2 breakout from a 2.5-year base

Base 44.00-58.00 (130 weeks); 30-week SMA 55.20 rising; weekly ATR 2.60; last weekly higher low 55.40; resistance 72-73.50; prior-cycle high 86.00 (monthly). Report 2026-11-03 (confirmed, 39 days: outside 30).

```yaml
plan:
  trade_type: investment
  horizon: long_term
  chart_timeframe: 1w
  setup: "S6 Weinstein stage-2 breakout (investor buy), zone tranches"
  entry: 58.26
  entry_condition: "weekly close above 58.26 (58.00 + 0.1 x weekly ATR 2.60); valid until 2026-11-20"
  entry_plan:
    tranches:
      - {fraction: 0.4, trigger: "the entry above"}
      - {fraction: 0.3, trigger: "limit 57.20 on a throwback holding 56.50-58.00 on weekly closes", expires: CP2}
      - {fraction: 0.3, trigger: "after the 11-03 report: weekly close above 61.00", stop_after: 56.40, expires: CP2}
  stop: 54.10                        # higher low 55.40 - 0.5 weekly ATR; R 4.16 = 7.1% on tranche 1
  invalidation: "weekly close below the 30-week SMA and below 56.50; MFE < +0.5R by week 7; T1 by week 42; re-underwrite at week 52"
  target: 71.35                      # 72.00 - 0.25 weekly ATR (= measured move 58 + 14); 3.15R
  targets: [{id: T1, price: 71.35, r: 3.15}, {id: T2, price: 85.35, method: "prior-cycle high 86.00 - 0.25 weekly ATR", r: 6.51}]
  scale_out: "trim 1/4 at T1; 1/4 at T2; rest on weekly close below the 30-week SMA"
  expected_days_to_t1: {estimate: 21 weeks, range: [21, 130], floor: 5 weeks, method: "M3 prior-cycle 0.231 weekly ATR/week; M4 130 (> 2x apart, range top)"}
  checkpoints: ["CP1 week 7 (12-04 if filled 10-16): MFE >= +0.5R; weekly close > 58.00; RS vs SPY rising", "CP2 week 14 (2027-01-22): weekly close >= +1R or new 52-week high; 30-week SMA rising; else reduce"]
  max_hold: {weeks: 52, date_if_filled_2026-10-16: 2027-10-15, latest_date: 2027-11-19}
  at_time_limit: "re-underwrite with a fresh upstream thesis and chart (8.1); no thesis -> exit"
  event_plan: [{date: 2026-11-03, event: "earnings (confirmed)", rule: "tranche 3 only after the report; thesis review after every report"}]
  rr_single: 3.15
```
Fill states: tranche 1 only 7.1% / 3.15; 1+2 (E 57.81) 6.4% / 3.65; all three (tranche 3 near 61.00, E 58.76) with the stop at 54.10: 7.9% / 2.70, inside the cap by a hair but with total open risk above the initial plan (06 10.2 rule 4), so tranche 3 requires the stop at 56.40 (4.0%, R:R 5.33). T1 deadline = min(52, 2 x 21) = week 42. Tranche 1 can fill in the 10 sessions before the report (valid until 11-20); 06 11 allows a first investment tranche there, but say so.

## 14. Pre-publish checklist

1. trade_type chosen (05 11), mapped to `horizon` and `chart_timeframe`; setup clock (4.1) applied if earlier.
2. Three barriers: stop, T1 (T2 if scaling), time (progress stop, T1 deadline, max hold).
3. `valid_until`, cancel_if, stale cap, fill ceiling; "void if filled above" when the ceiling is within 3% of entry.
4. E(T1) from >= 2 methods with inputs; E <= 2/3 max hold; M1 <= max hold; k <= 1.5.
5. CP1/CP2 bars and criteria; illustrative dates; latest max-hold date; Timeline line (7.2).
6. Events checked through the latest max-hold date, each with a rule; ex-dividend checked or NOT CHECKED.
7. Every tranche fill state passes `max_loss` and `reward_to_risk`; worst state and worst-case gap loss reported.
8. `target` = T1; blended R information only; time rules copied into `invalidation`.
9. Nothing renews or graduates a loser, widens a stop or resets a clock (3.3).

## 15. Post-trade record (evaluation and calibration)

On close record: exit code (3.1), date, price, realised R (and gap slippage vs stop), bars held, E(T1) vs actual bars to T1, MFE_R, MAE_R, the deciding checkpoint, events passed. Over many trades actual/expected bars calibrates M3 (typically > 1.5 = too optimistic: widen E), and winners' MAE shows whether stops sit outside normal noise (Sweeney) [C]. Evaluator and feedback agents may use these; they never see accept/reject decisions.

## 16. Shorts (mirror notes, only if `allow_short: true`)

Mirror every price rule. Shorter clocks [C]: volatility rises in declines (leverage effect [A]; Black 1976, Christie 1982) and squeezes produce sharp rallies [C]; short_swing/swing clocks only, a report inside the hold is a reject, and borrow cost/availability (not in the data) is a gap to list.

## Sources

- Jegadeesh (1990), Journal of Finance; Lehmann (1990), Quarterly Journal of Economics (short-term reversal).
- Jegadeesh and Titman (1993), "Returns to buying winners and selling losers", Journal of Finance. Moskowitz, Ooi and Pedersen (2012), "Time series momentum", Journal of Financial Economics. De Bondt and Thaler (1985), "Does the stock market overreact?", Journal of Finance.
- Bernard and Thomas (1989), Journal of Accounting Research; (1990) Journal of Accounting and Economics. Martineau (2022), "Rest in peace post-earnings announcement drift", Critical Finance Review.
- Shefrin and Statman (1985), Journal of Finance; Odean (1998), "Are investors reluctant to realize their losses?", Journal of Finance.
- Kaminski and Lo (2014), "When do stop-loss rules stop losses?", Journal of Financial Markets.
- Feller (1951), Annals of Mathematical Statistics (expected range sqrt(8/pi) sigma); Parkinson (1980), Journal of Business; Chhikara and Folks (1989), The Inverse Gaussian Distribution; reflection principle in any stochastic-processes text.
- Lopez de Prado (2018), Advances in Financial Machine Learning (triple barrier).
- Wilcox and Crittenden (2005), "Does trend following work on stocks?" (Blackstar Funds white paper).
- O'Neil, How to Make Money in Stocks (8-week hold). Weinstein (1988), Secrets for Profiting in Bull and Bear Markets (30-week SMA stages). Kaufman, Trading Systems and Methods (time exits). Tharp, Trade Your Way to Financial Freedom (R-multiples, expectancy). Sweeney (1996), Maximum Adverse Excursion. LeBeau and Lucas (1992), Technical Traders Guide to Computer Analysis of the Futures Market (chandelier exit).
- Bulkowski, glossary, "ultimate high": https://www.thepatternsite.com/glossary.html
- Johnson and So (2018), "Time will tell: information in the timing of scheduled earnings news", Journal of Financial and Quantitative Analysis.
- Savor and Wilson (2013), Journal of Financial and Quantitative Analysis. Lucca and Moench (2015), "The pre-FOMC announcement drift", Journal of Finance. Kurov, Wolfe and Gilbert (2021), "The disappearing pre-FOMC announcement drift", Finance Research Letters.
- Elton and Gruber (1970), Review of Economics and Statistics. FINRA Rule 5330: https://www.finra.org/rules-guidance/rulebooks/finra-rules/5330
- Shleifer (1986), Journal of Finance; Harris and Gurel (1986), Journal of Finance; Patel and Welch (2017), Review of Asset Pricing Studies; Greenwood and Sammon (2022), "The disappearing index effect", NBER working paper.
- Field and Hanka (2001), "The expiration of IPO share lockups", Journal of Finance.
- Barroso and Santa-Clara (2015), "Momentum has its moments", Journal of Financial Economics; Moreira and Muir (2017), "Volatility-managed portfolios", Journal of Finance.
- Black (1976), Proceedings of the American Statistical Association; Christie (1982), Journal of Financial Economics (leverage effect).
- Pipeline: prompts/technical-analysis/role.md, prompts/follow-up/role.md, prompts/technical-analysis/evaluation.md, docs/operations.md, profile.example.json.
- Web note: web access was unavailable during the research and both reviews except FINRA 5330 and Bulkowski's glossary (checked in the original research). Not re-checked online: the Russell semi-annual reconstitution schedule and the bibliographic details of Kurov-Wolfe-Gilbert (2021), Greenwood-Sammon (2022), Patel-Welch (2017) and Martineau (2022). Section 5.1 percentages and M2 medians are computed from the formulas shown, not taken from any study.
