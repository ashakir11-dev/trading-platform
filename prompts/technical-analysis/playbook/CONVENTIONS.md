# Playbook conventions

## How to use this file

- Canonical names, notations and default numbers for files 01-09. If a topic file shows an older value, this file wins; owners hold the detail (01 chart reading, 02 indicators, 03 patterns, 04 setups, 05 time windows, 06 entries, 07 exits, 08 plan/timeline, 09 events).
- All numbers are [C] house defaults unless a topic file labels them otherwise. role.md rules stay authoritative.

## Trade types

| trade_type | hold | primary (levels) | context | trigger | `horizon` / `chart_timeframe` |
|---|---|---|---|---|---|
| short_swing | 3-15 sessions | daily ~6 mo | weekly ~1 yr | daily | `swing` / `1d` |
| swing | 2-8 weeks | daily ~1 yr | weekly ~2 yr | daily | `swing` / `1d` |
| long_swing | 2-6 months | weekly ~2 yr (+ daily) | weekly/monthly ~5 yr | daily | `swing` if max hold <= ~3 months (13 weeks), else `long_term` / `1w` |
| investment | 6 months+ | weekly ~5 yr | monthly ~10 yr | weekly; daily fine entry | `long_term` / `1w` |

## Names and notation

- Setups (04): S1 pullback to a rising MA, S2 breakout retest, S3 base breakout (flat base, cup with handle, VCP; variants 3WT, ascending base, bull flag/pennant, high tight flag), S4 momentum/RS leadership, S5 52-week-high breakout, S6 Weinstein stage-2 breakout, S7 Donchian/trend following, S8 MA crossover (filter only), S9 squeeze, S10 RSI(2) dip, S11 range, S12 spring/failed breakdown, S13 post-earnings drift/gap continuation, S14 gap fill, S15 capitulation reversal. Entry triggers T1-T9 (06 3.1).
- MAs: EMA10, EMA21, SMA20/50/150/200; 10-week, 30-week, 40-week SMA; 10-month SMA. ATR14 = Wilder, daily; "weekly ATR14" on weekly bars.
- RVOL = V / mean(V of prior 50 sessions); RVOL(20) for short_swing; weekly: / prior 10 weeks. CLV = ((C - L) - (H - C)) / (H - L).
- d = (close - MA) / ATR14 (01 9). Mansfield RS n = 52 weekly or 252 daily (say which). Chandelier = HH(n) - m x ATR(n).
- P pivot, b buffer, e entry, s stop, R = e - s, T1 = role `target`, CP1/CP2 checkpoints, E expected bars to T1, HEM/HEMmax (09 2.2).
- Reachability k = (T1 - e) / (0.63 x ATR14 x sqrt(max-hold bars)); weekly: weekly ATR14 and weeks. k <= 1.5 (05 5.3).
- Stale cap = min((T1 + m x s) / (1 + m), s / (1 - L/100)), m = `min_reward_to_risk`, L = `max_loss_per_trade_pct`, rounded down to the cent (06 8.3); its first term is the fill ceiling e_max (05 7.5).

## Defaults per trade_type

| Item | short_swing | swing | long_swing | investment |
|---|---|---|---|---|
| Trigger (close mode) | daily close > P + 0.1 ATR | same | weekly close > P + 0.1 weekly ATR | same |
| Breakout RVOL | >= 1.5 (RVOL(20)) | >= 1.4 | week >= 1.2 | week >= 1.2 or OBV 26-week high |
| Max extension at entry (01 9.2) | d <= 3 vs EMA21 | d <= 5 vs SMA50 | d <= 3 weekly ATR vs 10-week | <= 40% above 40-week |
| Stop buffer beyond level | 0.25-0.5 ATR | 0.5-1 ATR | 0.25-0.5 weekly ATR | 0.5 weekly ATR |
| Stop distance / minimum | 1.5-2.5 ATR / >= 0.75 ATR | 2-3.5 ATR / >= 1 ATR | 1-2 weekly ATR + daily-close hard stop | 1.5-3 weekly ATR + hard stop |
| Entry validity (T4 limit) | 5 sessions (3) | 10 (5) | 20 (10) | 40 (20) |
| Watch expiry | 10 sessions | 20 sessions | 8 weeks | 13 weeks |
| CP1: MFE >= +0.5R | bar 5 | bar 10 | week 6 | week 13 |
| CP1 fail | exit | halve, stop to last higher low | halve, tighten | reduce |
| CP2: close >= +1R or new swing high, else breakeven or exit | bar 10 | bar 20 | week 13 | week 26 |
| Max hold / renewals | 15 bars / 1 | 40 bars / 1 | 26 weeks / 1 | 52 weeks per plan / unlimited re-underwrites |
| Tranches / max adds | 1 / 0 | 1-2 / 1 | 2-3 / 2 | 2-4 / 3 |
| Scale-out (trend) | all at T1, or 1/2 + tight trail | 1/2 at T1, rest T2 or trail | 1/3 T1, 1/3 T2, 1/3 trail | 1/4-1/3 at T1, rest weekly trail |
| Trail | 2-bar pivot - 0.25 ATR or EMA10 close | EMA21 close, 5-bar pivot - 0.5 ATR, or HH22 - 3 x ATR22 | weekly close < 10-week SMA; HH10W - 2.5-3 weekly ATR | weekly close < 30/40-week SMA; HH26W - 3 weekly ATR |
| Earnings (09 4) | no report from entry to max hold + 2 sessions: end max hold >= 1 session before it, else reject | no entry in the last 10 sessions; cushion rule (09 4.2) at the last close before | pilot <= 1/3 before, add after; name each report | first tranche allowed; next after the report; no add in last ~10 sessions |
| Role earnings window | 45 d | 45 d | 45 or 30 d | 30 d |
| Trend MA / oscillator | EMA10/21, SMA50; RSI(2) or Stoch(14,3,3) | SMA50/200, EMA21; RSI(14) or MACD | 10/30/40-week; weekly MACD or RSI(14) | 40-week, 10-month; weekly RSI(14) context |

## Rules shared by every file

- `reward_to_risk` is checked on T1 alone; blended R is information; R multiples are runner checkpoints, never the target. Mean-reversion setups (S10, S11, S14, S15) exit fully at target.
- Failed breakout = close < P - 0.5 ATR within 1-5 bars (03 2.6). Throwback rates: qualitative only (not re-verified).
- Re-entry once per setup, on a fresh trigger (T9 reclaim or new pivot), never the same day (06 3.3).
- Adds only to winners (close >= e + 0.5R or a new trigger), each <= the prior tranche, stop raised so total risk <= initial; no averaging down outside planned zone tranches.
- Liquidity: 20-day dollar volume < $5M rejects short_swing/swing. >= 3 non-earnings gaps in 252 bars that would skip the stop = stop in gap noise (07 4.2).
- Estimated earnings date = same quarter last year +/- 7 calendar days. Release after the close on T: act at T's close; before the open: at T-1's close.
- Labels: [A] academic, [P] practitioner study, [C] convention/house default, [S] speculative. Bulkowski figures are "[P, as summarised]".
