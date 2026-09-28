---
description: Record that you entered or exited an accepted position, or place/check a paper order for it
argument-hint: "<position_id> entered|exited <price> [YYYY-MM-DD] [size] | <position_id> broker-buy|broker-sell <qty> [limit_price] | <position_id> broker-status"
model: claude-sonnet-5
allowed-tools: Bash(python3 scripts/broker_alpaca.py:*)
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Arguments: $ARGUMENTS. First word is always `position_id`; second word picks the mode.

## Manual: `entered` / `exited`

Use this when the trade happened somewhere else (your own broker, by hand) and you're
just recording it. Arguments: position_id, `entered` or `exited`, the price, optional
date (default today, New York time) and optional size.

1. `workspace/positions/<position_id>/position.md` must exist; if not, stop and say so.
2. `entered`: set `opened` = the date and `entry` = the price (keep the planned entry as
   `planned_entry`). Only allowed while `opened` is empty.
   `exited`: set `status: closed`, `closed` = the date, `exit_price` = the price. Only
   allowed while `status: open` and after `opened` is set.
3. Append a row to the trade log in `workspace/decisions/<position_id>.md`
   (date, action, price, size).
4. Confirm in one or two lines. After an exit, suggest `/evaluate --run <run_id>`.

Trade facts go into the position file; nothing else from the decision file does.

## Paper trading: `broker-buy` / `broker-sell` / `broker-status`

**Forward testing only, and only on this command.** No stage, follow-up or evaluator
agent has a broker tool; `scripts/broker_alpaca.py` talks only to Alpaca's paper-trading
endpoint (hard-coded in the script, never configurable to a live account), and a hook
blocks every subagent from running it. You are the only caller, and only when the user
types this command — never place or size an order on your own initiative.

Requires `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY` (a paper account's keys) in the
environment; if the script reports they're missing, stop and tell the user to set them
(see `docs/operations.md`).

**`broker-buy <qty> [limit_price]` / `broker-sell <qty> [limit_price]`:**

1. `workspace/positions/<position_id>/position.md` must exist and be `status: open`.
   `broker-buy` only while `opened` is empty and no `broker_entry_order_id` is working
   (`/decide accept` normally places the entry; use this for a manual re-entry or when
   that order was skipped); `broker-sell` only after `opened` is set. For a **short**
   position the entry side is `sell` and the exit side is `buy`; "buy"/"sell" in the
   mode names mean entry/exit.
   `<qty>` may be `all` (the position's remaining `qty × remaining_fraction`) or
   `target:<k>` (the k-th target's `fraction × qty`, for a scale-out exit).
2. side = the entry side for `broker-buy`, the exit side for `broker-sell`. Run:
   `python3 scripts/broker_alpaca.py submit --symbol <ticker> --side <side> --qty <qty>
   --wait 30` (add `--type limit --limit-price <limit_price>` if a limit price was
   given). Show the user the raw JSON result.
3. If the order's `status` is `filled`: treat it exactly like the manual case above
   (`entered`/`exited`, using `filled_avg_price` as the price and today, New York time,
   as the date unless the fill has its own date), and additionally set `broker:
   alpaca_paper` and `broker_entry_order_id` (entry) or append to `broker_exit_order_ids`
   (exit) on the position file. A partial (scale-out) exit: mark that target's `hit`
   date, subtract its `fraction` from `remaining_fraction`, keep `status: open`; the
   position closes (`status: closed`, `exit_price` = the size-weighted average of all
   exits) when `remaining_fraction` reaches 0 or a stop exit is recorded.
4. If it is not yet filled (e.g. a limit order still `new`/`accepted`), do **not** touch
   `opened`/`entry`/`status`/`exit_price` — only record the order id and `broker:
   alpaca_paper` on the position, and tell the user to check back with `broker-status`.
5. Append the same trade-log row as the manual case once (and only once) a fill is
   recorded, noting the broker order id and, for a scale-out, the target index.

**`broker-status`:** read the working order ids off the position file
(`broker_entry_order_id`, then any `broker_exit_order_ids` not yet recorded as filled)
and run `python3 scripts/broker_alpaca.py status <order_id>` for each. If one has since
filled, apply step 3 above; otherwise just show the current status.

Never run `broker_alpaca.py cancel`, `positions` or `account` from here unless the user
explicitly asks for that check.
