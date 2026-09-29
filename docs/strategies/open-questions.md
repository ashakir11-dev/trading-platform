# Strategies: open questions before wiring them in

*2026-09-29. Decisions for the user before the drafts in this folder
([`investment.md`](investment.md), [`swing.md`](swing.md), [`short-swing.md`](short-swing.md))
become the technical agent's playbook. Research: [`research.md`](research.md). Nothing here
is decided; where there is a recommendation, it is marked as one.*

## Top questions

1. **Bucket limits vs strategy limits (§B).** The buckets were designed per *reward shape*;
   the strategies need limits per *strategy*. Core's 5% max loss rejects most weekly
   (investment) stops, although core prefers `long_term`; every bucket's minimum reward:risk
   rejects every short-swing trade (R:R ≈ 0.3-0.7 by design). Per-strategy limits, or keep the
   buckets and accept that some strategies can't run?
2. **Trailing exits in the plan format (Q6).** Investment and swing earn their edge in the
   right tail; the format forces fixed targets summing to 1. Add a trailing leg?
3. **Short swing and the exit path (Q12-Q14).** The entry survives hours of delay; the exit
   doesn't, because triggers are close-based, alerts can sit in the 12-hour cooldown, and every
   exit is a user `/trade` command. Automate short-swing exits at the paper broker, accept and
   measure the latency, or drop the short swing?
4. **New horizon (Q1).** Add `short_swing` (1d primary, 10-day max hold) to the profile, the
   horizons table and the rules?
5. **How the agent chooses a strategy (Q2-Q3).** Mechanical setups, computed by code, with the
   agent judging context; or the agent reading the playbook and applying it itself?
6. **New statistics and the sector ETF (Q15-Q16).** Approve adding the statistics listed below
   to `price_stats.py`, and a sector ETF call to the technical agent's data step?
7. **Mechanical backtester (Q20-Q22).** Build one outside the agent pipeline, and how does it
   get 20 years of Equibles bars for ~900 stocks?

## A. Fit with the pipeline

**Q1. Horizon mapping.** Proposed: investment ↔ `long_term`, swing ↔ `swing`, short swing ↔ a
new `short_swing` (primary 1d, context 1w, earnings window ~15 calendar days, `max_hold` 10
trading days). Principle 7 excludes day trading, not 2-10 day holds, so a literal reading
allows it; its rationale (plans going stale while the pipeline runs) applies to the short
swing's exits, not its entries (see [`short-swing.md`](short-swing.md) §1, §10). Does the
short swing need a principle-7 decision, or only a horizon?

**Q2. Choosing between strategies.** Options: (a) the bucket's `horizons` decide which
strategies are eligible; each eligible strategy's filter is tested; if several match, take
the bucket's `preferred_horizon`, then the variant matching `entry_style`; if none match,
`reject` with "no playbook setup". (b) As (a), but an off-playbook plan is allowed with a
`flag`. Recommendation: (a) for the forward test, so every trade is one the backtest covers;
(b) muddies the evaluation.

**Q3. Who computes the setup.** Rules today "never make judgment calls" and the middleware
recomputes plan arithmetic. If filters, setups and levels are computed by code (in the price
hook), the agent's job becomes context (news, chart anomalies, data gaps) and the plan is
reproducible from `raw/`; if the agent computes them, fidelity has to be measured. The
fidelity metric is in each strategy's §12 either way.

**Q4. Principle 1 (no cross-comparison).** The academic momentum evidence is cross-sectional
(top decile vs bottom decile); the drafts use absolute thresholds vs SPY and the sector ETF
instead, so each candidate is still judged alone. Confirm that's the intended trade-off (the
backtest must then test the absolute-threshold version, not assume the papers' results).

**Q5. Expected rejection rate.** Most fundamentally chosen candidates will match no setup on
a given day. Is a high rejection rate acceptable, or should a "setup forming" state (watch
until the setup triggers) be added? That would be a new position state and new follow-up work.

## B. Bucket vs strategy limits

| | investment | swing | short swing |
|---|---|---|---|
| typical stop | 8-15% | 4-10% | 3-10% (3×ATR) |
| reward:risk | open-ended (trail); 3R reference | 2.5-3.3R fallback targets | 0.3-0.7 |
| targets | ⅓ partial + trail | ½ at 2R + trail | 1 |
| entry valid | 10 days | 5 days | 2 days |
| clashes | core `max_loss` 5%; `max_targets`/fractions | minor (`entry_valid` 10 vs 5) | every `min_reward_to_risk`; core `max_loss`; `target_return_pct`; no horizon |

**Q6. Trailing leg in plans.** Proposal to discuss: plans may carry `trail: {rule, fraction}`
next to `targets`, with fractions summing to 1 across both; reward:risk measured to a
reference target; follow-up computes the trailing stop each tick. Without it, the fallback
targets truncate the payoff the strategies are built on (H4 in the investment and H3 in the
swing backtest plans test exactly this).

**Q7. Max loss.** Options: per-strategy `max_loss_per_trade_pct`; a cap in ATR multiples
instead of percent; or cap **account risk** (stop distance × position size ≤ X% of equity)
and let stop width vary. Recommendation to discuss: account risk, since that's what the loss
cap is protecting.

**Q8. Reward:risk vs expectancy.** A mean-reversion trade wins often and small. Options:
exempt `short_swing` from `reward_to_risk` and gate it on a backtested expectancy instead;
keep the rule and don't run the short swing; or give the short swing its own bucket-independent
limits.

**Q9. Sizing.** Today: notional `position_size_pct` (core 3%, growth 2%, speculative 1%), which
within each bucket's own loss cap risks at most ~0.15% of equity per trade (e.g. core 3% × 5%). The drafts ask for risk-based sizing (0.25-0.5%
of equity), capped by `position_size_pct`, plus per-strategy caps on open positions and per
sector. Keep notional sizing for the forward test, or switch?

**Q10. `entry_valid_trading_days`, `target_return_pct`, `entry_style`.** Per strategy rather
than per bucket? Speculative's `breakout` style flags the swing pullback and short-swing
entries; is that a flag or a reason not to offer them to speculative?

**Q11. Plan margins** (already open in ARCHITECTURE §5). Levels are defined by the strategy,
so they can't be nudged to fit a limit. Confirm "reject, never move" also applies here.

## C. Execution and follow-up

**Q12. Intraday trigger vs close confirmation.** A resting stop-limit fills intraday; the
current `entry_condition` examples say "daily close above". The drafts accept intraday fills
(capped by the limit). Agree, or require close confirmation (which needs a next-day order and
another latency)?

**Q13. Exits.** Every exit is a user `/trade` command today, and stops/targets are not parked at
the broker. For the short swing, options: (a) a resting GTC **limit sell** at the target at the
paper broker (fixed price, no slippage beyond it); (b) exit orders for the time stop placed by
`/follow-up` at the next session (a marketable limit; CLAUDE.md forbids market orders only for
entries); (c) keep manual exits and measure exit latency in the forward test. Any of (a)-(b)
changes the "exits remain the user's command" decision.

**Q14. Follow-up cadence and state.** Needed for the drafts: (a) exempt short-swing stop,
target and time-stop alerts from the 12-hour cooldown; (b) dynamic exits the follow-up doesn't
support today: weekly `W30` close exit and weekly trailing stop (investment), breakeven move
and 10-day-low trail (swing), close above the current `SMA5` and a 5-session time stop (short
swing); (c) whether the 14-day full re-review should differ per horizon. Is `level_trigger:
close` right for all three, or should the short swing's catastrophe stop be intraday?

**Q15. Earnings as a hard rule.** `upcoming_earnings` is a `flag` today; the drafts make it a
hard condition (short swing: no report within 10 trading days; swing: exit before the report
unless target 1 is hit; investment: no entry across one). Strategy-specific rejects?

## D. Data

**Q16. New statistics in `price_stats.py`** (arithmetic on fetched bars, keeping
`tests/test_price_stats.py` passing): completed-weeks flag on weekly bars; `W10`, `W30` and
slopes; `SMA5`, `SMA150`; `SMA20`/`SMA200` slopes; `RSI2`; `R12-1`; weekly base (length, depth,
pivot, pivot age, 3-week range, volume dry-up); 10-bar box (high, low, depth); 20-bar highest
close; 3- and 5-bar lows; 10- and 50-bar volume means; largest 3-bar |change| in ATR.

**Q17. Sector ETF.** The technical agent can already call `GetStockPrices` on an ETF, but the
brief has no sector→ETF mapping and `role.md` doesn't ask for it. Add both? (One more call per
candidate.)

**Q18. VIX.** Only needed if a VIX regime variant is adopted (e.g. the Nagel-motivated short
swing variant: allow entries below SPY's 200-day at half size when VIX is high). The technical
agent lacks `GetVixHistory`; it could read the scanner's `raw/` instead.

**Q19. Short side.** All three drafts recommend long-only at first, while `profile.example.json`
ships `allow_short: true`. Per-strategy `allow_short`, or keep shorts on and accept untested
mirrors?

## E. Testing

**Q20. A plain mechanical backtester.** The drafts' §12 assume a deterministic script (new,
outside the agent pipeline, no orders) that runs the rules over daily bars. Build it? Where
should it live, and what does it report?

**Q21. Getting the history.** ~900 stocks × 20 years at ≤ 500 rows per `GetStockPrices` call is
~9,000 calls. Through MCP sessions, or a direct Equibles API route for a script? Point-in-time
index membership: Equibles serves only the latest ETF holdings; `GetIndexChanges` /
`GetIndexComposition` may allow reconstructing past members (unverified). If not, the vendor
rule says defer, and backtests are labelled survivorship-biased.

**Q22. Acceptance criteria.** What result earns a strategy its place in the playbook? A
suggestion to react to: expectancy > 0 after costs on the untouched 2019-2025 hold-out, max
drawdown no worse than SPY buy-and-hold's over the same period, and no single sector or year
supplying most of the profit.

**Q23. Look-ahead in the design itself.** These drafts were written with knowledge of market
history through 2026 (2008, 2020 and 2022 are known outcomes), so even the hold-out is not
fully clean for the *design*. The only clean evidence is forward paper trading from the date
the rules are frozen. Freeze them (version and date) before the forward test starts?

**Q24. Regime filters.** Investment and short swing use SPY > 200-day; swing also requires SPY
> 50-day (untested, first ablation). Keep them different per strategy, or one shared regime?
