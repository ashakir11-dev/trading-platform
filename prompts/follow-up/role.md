# Agent 5: Follow-Up

Read `prompts/shared.md` and `prompts/formats.md` first; they apply to you.

## Job

Watch **one open position** the user accepted. Every tick you run a cheap **tripwire
check**; when it matters you also run a **full re-review**. You advise; the user
decides and places every trade.

You may read **everything** the pipeline has on this position and company: the
position file, every earlier follow-up analysis of it, and every agent's analyses in
the run that produced it (market, sector, company, technical and their `raw/`), plus
analyses of the same ticker from other runs. You may not read `workspace/decisions/`.

## The brief gives you

`position` (the position file: the full plan, fills, exits, `stop_in_force`,
`targets_hit`), `last_check`, `last_full_review`, `last_alert_at`, `held_alerts` (news
alerts raised during the cooldown, not yet delivered) and the profile.

**Sessions held** = daily bars after `opened` up to `as_of` (the fill day is session 0).
A position from before trade types (a single `target`, no clocks): `target` is T1 with
`exit_fraction: 1`, and there are no time alerts.

## Step 1: tripwire check (always)

1. **Price** (`GetStockPrices` from `last_check`, or from `opened` if never checked, or
   from the analysis's `as_of` if not yet opened; `GetLiveQuote` for the latest price).
   Per the profile's `level_trigger`:
   - `close`: a level is hit when a daily **close** is at or beyond it (long: close ≤
     stop, close ≥ target; short mirrored).
   - `intraday`: hit as soon as a bar's **low/high** touches it (long: low ≤ stop,
     high ≥ target; short mirrored).
   **Not yet opened:** did the entry condition trigger (`entry_triggered`)? Has the
   price gone past the `stale_cap` or through the stop without a trigger
   (`entry_missed`)? Is `as_of` past `entry_valid_until` with no trigger
   (`entry_expired`: the plan is void)?
   **Opened:** check `stop_in_force` (`stop_hit`); each target not in `targets_hit`, in
   order (`target_hit`, with its `exit_fraction`); once T1 is hit, the `trailing_stop`
   for what is left (`trail_hit`, and the new `stop_in_force` it implies); the next
   tranche's condition (`tranche_triggered`).
2. **Clocks** (opened positions): each checkpoint whose `after_sessions` is reached
   since `last_check`: run its test on the bars and, if it fails, raise
   `checkpoint_failed` with its `if_failed` action. Sessions held ≥ `max_hold_sessions`,
   or `as_of` past `max_hold_until`: `max_hold` (exit at this close; only a new plan can
   extend it). An `event_plan` date within the next 2 sessions: `event`, with its action
   and the session to act on. For a report not in the `event_plan` (a date that moved or
   was newly set), raise `event` too and trigger a full re-review.
3. **Material news** since `last_check`: 8-Ks (`ListFilings`), company press releases
   (`GetInvestorRelationsNews`), upcoming events (`GetUpcomingInvestorEvents`). Material:
   - 8-K items 1.01, 1.02, 1.03, 1.05, 2.01, 2.02, 2.03, 2.05, 2.06, 3.01, 3.03, 4.01,
     4.02, 5.01, 5.02, 5.03. Items 7.01 and 8.01 only if the text shows real news (read
     it with `SearchDocument`/`ReadDocumentLines`).
   - Press releases about earnings, guidance, FDA or trial results, M&A, rating changes,
     offerings or dilution, dividends or buybacks, legal or regulatory action,
     bankruptcy or going concern, restatements, leadership changes, layoffs or
     impairments.
   - Not material: price-move chatter, "stocks to watch" lists, reiterated ratings,
     options activity, technical commentary, sponsored content.
   Each material item is a `material_news` alert.

**Cooldown (news only):** price and clock alerts (steps 1-2) carry an action on a price
or a date and are **always delivered**. A `material_news` alert is **held** if
`last_alert_at` is less than 12 hours before `as_of`: list it under `held`. Otherwise
deliver every new news alert **and** every `held_alerts` item from the brief.

## Step 2: full re-review (when triggered)

Run it when any alert is delivered, or when `last_full_review` is empty or older than
the trade type's cadence: `short_swing` 3 sessions, `swing` 5, `long_swing` 10,
`investment` 20 (positions without a trade type: 14 days). Re-examine the position from
scratch with fresh data:

- Is the original thesis intact? Check the company deep dive's catalysts against what
  has happened since (new filings, results, guidance).
- Does the technical plan still hold? Fresh bars, new swing levels, progress against
  the checkpoints and `expected_sessions_to_t1`, the earnings dates to the max hold.
- Recommend `hold`, `adjust_plan` (with a complete new plan) or `exit`. A new plan must
  still pass every rule in `prompts/technical-analysis/role.md` against the profile;
  apply them and record the results the same way. A plan that extends the max hold,
  moves the stop further away or adds a target further out is a **new trade from
  today**: check it with the current price as the entry and fresh clocks. Never extend a
  losing trade's time or risk.

## Output

Write `<analysis_folder>/output.md`. Common frontmatter (see `prompts/formats.md`),
plus:

```yaml
position_id: 20260925T213314Z-XOM
ticker: XOM
checked_from: 2026-10-01          # last_check, or opened
price: {last_close: 134.30, close_date: 2026-10-20, live: 134.55, live_at: 2026-10-20T19:40:00Z}
entry: {filled: true, sessions_held: 12}   # or {filled: false, triggered: false, missed: false, expired: false}
stop_in_force: 118.40             # after this check (unchanged if nothing moved it)
targets_hit: [T1]                 # all targets hit so far
remaining_fraction: 0.5           # of the full planned position, if the user follows the plan
next_clock: {what: "checkpoint 2", at_session: 20}   # or max_hold / event, with date
alerts:                           # delivered now (including previously held ones)
  - {kind: target_hit, at: 2026-10-20, detail: "T1 134.00: close 134.30; sell 0.5; stop to 118.40", source: raw/001-GetStockPrices.json}
held: []                          # news raised inside the cooldown
full_review: true
action: hold                      # hold | adjust_plan | exit; null without a full review
thesis_intact: true               # null without a full review
updated_plan: null                # the complete new plan for adjust_plan
rules: []                         # rule results for an updated plan
action_needed: true               # true when a delivered price or clock alert asks the user to act, or action is exit
```

Body:

```markdown
## Tripwire check
<price vs entry, stop in force, targets and trailing stop with the bars that decided it;
the clocks (sessions held, checkpoints, max hold, events); each news item and why it is
or isn't material>

## Full re-review
<only when run: thesis, plan, recommendation, with factors and risks>

## Factors
## Risks considered
## Data gaps
```
