---
description: Record your accept/reject for a recommended candidate; on accept, place the sized paper entry order
argument-hint: "<candidate_id> accept|reject [note]"
model: claude-sonnet-5
allowed-tools: Bash(python3 scripts/broker_alpaca.py:*)
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Record the user's decision. Arguments: $ARGUMENTS
(candidate_id, then `accept` or `reject`, then an optional free-text note).

1. The run is the part of the candidate_id before the last `-`. Read its
   `workspace/runs/<run_id>/run.md`. The candidate must be listed under
   "Recommendations" or "Also passed"; if not, stop and tell the user (only candidates
   that passed every filter can be decided). An "Also passed" accept is allowed: it is
   the user overriding the pick rule, and the report says which it was.
2. If `workspace/decisions/<candidate_id>.md` already exists, stop: a candidate is
   decided once.
3. Write `workspace/decisions/<candidate_id>.md` in the format of `prompts/formats.md`,
   with `decided_at` = now, the note verbatim under "Why", and an empty trade log.
4. On `accept`: create `workspace/positions/<candidate_id>/position.md` from the
   technical analysis plan the candidate points to (entry, `entry_valid_until`, stop,
   `targets`, `target`, horizon, direction, `risk_bucket`) plus, from the run's
   `profile.json`: `level_trigger`, `max_hold_trading_days` for the horizon and the
   bucket's `position_size_pct`. `status: open`, `opened` empty, `remaining_fraction:
   1.0`, `qty: null`. Trade facts only: never the note.
   On `reject`: nothing else is created; stop after confirming.
5. **Paper entry order (accept only).** This is forward testing against Alpaca's paper
   account and the only place besides `/trade` that places an order; it runs only
   because the user typed `/decide ... accept`.
   a. Run `python3 scripts/broker_alpaca.py account`. If it reports missing credentials,
      skip the order, leave `broker: null`, and tell the user the position is watched
      but unsized (set `ALPACA_API_KEY_ID`/`ALPACA_API_SECRET_KEY` to enable paper
      orders). Otherwise `equity` = the account's `equity`.
   b. `qty` = floor(`position_size_pct` / 100 × equity / entry). If `qty` is 0, place
      nothing and say the account is too small for one share at this size.
   c. Order type from the plan vs the technical analysis's `current_price`:
      long with entry **above** the current price (a breakout) → `stop_limit` buy,
      `--stop-price <entry> --limit-price <entry × 1.005>`; long with entry **at or
      below** it (a pullback) → `limit` buy at `<entry>`. Short: mirrored (`sell`;
      entry below current → `stop_limit` with `--limit-price <entry × 0.995>`; else
      `limit`). Never a market order: the plan's entry condition is the price.
   d. Run `python3 scripts/broker_alpaca.py submit --symbol <ticker> --side <buy|sell>
      --qty <qty> --type <stop_limit|limit> [--stop-price ...] --limit-price ... --tif gtc`.
      Show the user the raw JSON result. On success set `broker: alpaca_paper`,
      `broker_entry_order_id` = the order `id` and `qty` on the position. If the order
      fills immediately (`status: filled`), also set `opened` = today (New York) and
      `entry` = `filled_avg_price`, and append the trade-log row in the decision file.
   e. The order stays working until it fills or `entry_valid_until` passes; `/follow-up`
      cancels it then. Never place the stop or the target orders here: the follow-up
      agent watches those levels and the user (or `/trade broker-sell`) exits.
6. Confirm in two or three lines what was recorded, the order placed (type, qty, price)
   or why none was, and that the position is now watched.

The decision and note never go into any other file.
