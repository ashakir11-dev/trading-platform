# Technical-analysis playbook

## How to use this file

- This is the index. The technical-analysis agent reads `cheat-sheet.md` on every run and opens a topic file only for the question in the table in section 3.
- `CONVENTIONS.md` holds the canonical names and default numbers; when a topic file and CONVENTIONS disagree, CONVENTIONS wins. `prompts/technical-analysis/role.md` and `prompts/shared.md` stay authoritative over everything here.
- Section 6 lists pipeline changes the playbook would need. They are proposals for the user to decide, not current rules: until adopted, the agent writes the extra plan items into `entry_condition`, `invalidation` and one-line items in `## Plan` (`08` 12.2).

## 1. What the playbook is

A reference for reading one company's daily/weekly chart and turning it into a trade plan (entry, stop, target, time limits) for a human investor, then checking the plan against the investor profile. It covers top-down chart reading, indicators, chart patterns and flags, named setups, time windows and trade types, entries, exits, the trade timeline, and events (earnings, news, hype and fear).

Fixed constraints the playbook is written for:

- Decision support only. The pipeline never places orders; plans are instructions for the human ("daily close above X", "do not fill above Y").
- Daily OHLCV bars only (weekly and monthly built from them); no intraday bars, so no day trading. The shortest trade type is multi-day.
- Long-only by default (`allow_short: false`); shorts appear only as mirror notes.
- Nothing dated after `as_of`; no remembered facts about companies or past price moves. All examples are hypothetical (XYZ, made-up prices).
- Every indicator not supplied by a tool has an exact formula computable from bars; the agent shows its inputs.

## 2. Files

| File | Holds |
|---|---|
| `cheat-sheet.md` | the one page read every run: procedure, trade-type table, pattern and setup tables, indicator tiers and stacks, entry, exit and event rules, hype and fear, plan must-haves and timeline |
| `CONVENTIONS.md` | canonical names (S1-S15, T1-T9, MAs, RVOL, CLV, k, stale cap) and default numbers per trade_type |
| `01-chart-reading.md` | top-down order, trend and stages, support/resistance grading, volume, bars, gaps, extension, volatility, relative strength, market regime, timeframe alignment, the hook's statistics block, chart quality score |
| `02-indicators.md` | evidence, master table (best / most common / underrated), parameters per trade_type, formulas, redundancy groups, divergences, minimal stacks |
| `03-chart-patterns.md` | breakout rules, stops, measured moves, throwbacks and failures, one card per pattern, gaps, pattern cheat sheet |
| `04-strategies-and-setups.md` | setup cards S1-S15, selection tree, setup vs regime / trade_type / volatility matrices, reject codes |
| `05-timeframes-and-trade-types.md` | the four trade types, data plan, parameter and volatility scaling, reachability, stop feasibility, choosing a type, timeframe conflicts, graduation, master matrix |
| `06-entries.md` | entry state, triggers T1-T9, buffers, confirmation grading, red flags, gaps at the open, stale cap, entry expiry, all-at-once vs scaling in, pyramiding |
| `07-exits.md` | initial stop, gap execution, targets, scale-out math, scale vs full exit, trailing, breakeven, exit cues, time and event exits, exit evaluation |
| `08-trade-plan-and-timeline.md` | lifecycle, canonical clocks, expected time to target, checkpoints, event timeline, time-limit actions, graduation, plan YAML template and filled examples |
| `09-events-hype-and-fear.md` | event calendar and gap risk, earnings reaction classes, per-type earnings rules, "buy the rumor, sell the news", hype and fear scores, event types, macro |

## 3. Reading order

1. Every run: `cheat-sheet.md`, top to bottom. It is sufficient for a normal plan.
2. Then only what the case needs:

| Question | Open (sections) |
|---|---|
| How do I read this chart, grade levels, judge regime, RS, extension, alignment, score quality? | `01` (3, 6, 9, 11, 12, 13, 15, 16) |
| Which indicator, what formula and parameters, how many votes does it get? | `02` (3, 4, 8, 10, 13) |
| Is this pattern valid; where are its pivot, stop, measured target; throwback or failure? | `03` (2, 3-5, 6, 7) |
| Which setup fits this chart and regime; which reject code? | `04` (3, 4, 5, 7) |
| Which trade_type; is T1 reachable in time; does the stop fit the cap; timeframes conflict; graduate or degrade? | `05` (5.3, 7, 11, 12, 13, 14) |
| Exact trigger and buffer, confirmation grade, stale cap, entry expiry, scale in or not, gap at the open, entry around a report? | `06` (3, 4, 5, 7, 8, 9, 10, 11, 12, 15) |
| Stop placement, targets, scale-out fractions, scale vs full exit, trailing method, exit cues, grading exits afterwards? | `07` (3, 5, 6, 7, 8, 10, 13, 14) |
| Clocks, expected days to T1, checkpoints, what to do at a time limit, the plan template? | `08` (4, 5, 6, 8, 12, 14) |
| Earnings date and gap risk, reaction class, hold through a report, buy the rumor / sell the news, hype or fear, other event types? | `09` (2, 3, 4, 5, 7, 8, 9, 13) |
| Two files give different numbers | `CONVENTIONS.md` |

## 4. Evidence labels

Every substantive claim, rule of thumb or statistic carries one of these.

| Label | Meaning | How much weight |
|---|---|---|
| [A] | academic, peer-reviewed and/or replicated (e.g. 3-12 month momentum, 52-week-high effect, short-term reversal, post-earnings drift) | can support a verdict, but these are portfolio averages: one stock can fail, so stops stay mandatory |
| [P] | practitioner statistical study (e.g. Bulkowski's pattern statistics, published system tests) | in-sample and often unreplicated; "as summarised" = figure taken from a secondary source |
| [C] | practitioner convention or consensus, including every "house default" threshold chosen for this playbook | widely used, not rigorously tested; never decides a verdict alone |
| [S] | speculative, contested, or evidence against it (candle names, Fibonacci ratios, divergences alone) | note only |

Variants: [A math] or [math] = exact arithmetic or probability under the stated model (usually a random walk). "[A limited]", "[A, one study]", "[A], weaker today" qualify the strength. No statistic, win rate or citation is invented: numbers appear only with a named source, and the Sources sections list what was looked up.

## 5. Trade types and the pipeline's current horizons

role.md knows two horizons (`swing`, `long_term`). Until the pipeline adopts trade types, map them like this:

| trade_type | Typical hold | Max hold per plan | Primary / context chart | `horizon` | `chart_timeframe` | Role earnings window | Watch out |
|---|---|---|---|---|---|---|---|
| short_swing | 3-15 sessions | 15 bars | daily ~6 mo / weekly ~1 yr | `swing` | `1d` | 45 d | the window covers the hold; a report inside the hold is a reject (`09` 4.1) |
| swing | 2-8 weeks | 40 bars | daily ~1 yr / weekly ~2 yr | `swing` | `1d` | 45 d | reports on days 46-56 of an 8-week hold are outside the role window: check to the latest max-hold date |
| long_swing | 2-6 months | 26 weeks | weekly ~2 yr (+ daily) / weekly-monthly ~5 yr | `swing` if max hold <= ~3 months (13 weeks), else `long_term` | `1w` (`1d` if mapped to `swing` and levels come from daily bars) | 45 or 30 d | 1-2 reports inside the hold: name each with its action |
| investment | 6 months to years | 52 weeks, then re-underwrite | weekly ~5 yr / monthly ~10 yr | `long_term` | `1w` | 30 d | several reports; each is a checkpoint |

Detail: `05` 2.4 and 14; clocks: `08` 4.

## 6. Proposed pipeline changes (for the user to decide)

**Adopted on 2026-09-26: items 2-6** (trade types, the plan fields, the rule changes, the follow-up and evaluator changes), in simplified form: see `role.md` and `docs/ARCHITECTURE.md` section 5. Where role.md differs from this playbook, role.md wins. **Still open:** items 1, 7 and 8.

1. **Tell the agent to use the playbook.** `role.md` (and the backtest variant) does not mention it today. Proposal: "read `playbook/cheat-sheet.md` every run; open topic files as needed".
2. **Output fields** (`08` 12.1 template): `trade_type`; `setup` (S1-S15 label); a `targets` list (T1, T2 with fractions) and `scale_out`; `entry_plan` with `valid_until` (entry expiry), trigger type, `stale_cap`, tranches and `cancel_if`; `time_stop` and `checkpoints` (CP1, CP2, T1 deadline); `max_hold` in bars plus a latest date; `trailing_rule`; `event_plan` (each report and its action); `worst_case` gap line; `expected_days_to_t1`; `regime_at_entry`. `target` would stay T1, the value `reward_to_risk` checks.
3. **Horizon table.** Adopt the four trade types in `role.md` (or keep `swing` / `long_term` and add `trade_type`); resolve the `chart_timeframe` flag for a long_swing mapped to `swing` whose levels are weekly (`05` 2.4). Optionally let the profile list allowed trade types.
4. **Rule changes.**
   - `stale_entry`: add the re-price test (stale cap = min((T1 + m s)/(1 + m), s/(1 - L/100))) and the ATR distance, because a fixed 3% ignores plan geometry and volatility (`06` 8.2-8.3).
   - `upcoming_earnings`: scan from `as_of` to the latest max-hold date instead of a fixed 45/30-day window, and make a report inside a short_swing hold a reject (`05` 2.4, `09` 4.1).
   - New checks: `time_barriers` (reject a plan without entry expiry, progress stop and max-hold date), `reachability` (k <= 1.5), `liquidity` (20-day dollar volume < $5M rejects short_swing/swing), and a tranche fill-state check (every fill state passes `max_loss` and `reward_to_risk`, `06` 10.3).
5. **Follow-up agent** (`08` 11.3): an alert kind `time` for `valid_until`, checkpoints, T1 deadline, max hold and pre-report decision dates; stop, target and max-hold alerts that bypass the 12-hour cooldown; full re-review every 3 / 5 / 10 / 20 sessions by trade_type; position files that carry `trade_type`, `valid_until`, `max_hold_date`, checkpoints, tranches and scale-out.
6. **Evaluator**: close a filled plan at its `max_hold_date` close as a time exit with realised R (today it stays open); grade by setup and trade_type; record MFE, MAE, give-back and actual vs expected bars to T1 (`07` 14, `08` 15).
7. **Data access** (read-only Equibles tools only, per the repository hard rules; in backtests through the gatekeeper's audited data packs): a market holiday calendar for session counting (`08` 3.2), dividend history for ex-dividend dates (`08` 7.3), and VIX, put/call, short interest or option-implied moves as optional context (`09` 2.2). Backtest data packs would need SPY, QQQ, the sector ETFs and up to five years of bars for weekly trade types (`05` 2.2).
8. **Length target**: the ~6K technical-analysis output target (`prompts/shared.md`) may need raising for plans that carry a full timeline and event plan.

## 7. Maintaining the playbook

- Change a default in `CONVENTIONS.md` first, then the owning topic file, then `cheat-sheet.md`; the cheat sheet must match both exactly and stay near ~15,000 characters (hard ceiling ~16,000).
- Keep examples hypothetical, label every claim, cite only sources that exist, and never add order-placing instructions or non-Equibles data sources.

## Sources

No new sources; each topic file (`01`-`09`) lists its own. Pipeline references: `prompts/technical-analysis/role.md`, `prompts/shared.md`, `profile.example.json`, the price hook (`price_stats.py`), `docs/ARCHITECTURE.md`.
