---
description: Record that you entered or exited an accepted position
argument-hint: "<position_id> entered|exited <price> [YYYY-MM-DD] [size]"
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Record a trade the user made. Arguments: $ARGUMENTS
(position_id, `entered` or `exited`, the price, optional date (default today, New York
time) and optional size).

1. `workspace/positions/<position_id>/position.md` must exist; if not, stop and say so.
2. `entered`: set `opened` = the date and `entry` = the price (keep the planned entry as
   `planned_entry`). Only allowed while `opened` is empty.
   `exited`: set `status: closed`, `closed` = the date, `exit_price` = the price. Only
   allowed while `status: open` and after `opened` is set.
3. Append a row to the trade log in `workspace/decisions/<position_id>.md`
   (date, action, price, size).
4. Confirm in one or two lines. After an exit, suggest `/evaluate --run <run_id>`.

Trade facts go into the position file; nothing else from the decision file does.
