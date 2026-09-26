---
description: Record that you entered or exited an accepted position (in full or in part)
argument-hint: "<position_id> entered|exited <price> [YYYY-MM-DD] [fraction] [size]"
model: claude-sonnet-5
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Record a trade the user made. Arguments: $ARGUMENTS
(position_id, `entered` or `exited`, the price, optional date (default today, New York
time), optional fraction of the full planned position (e.g. `0.5`) and optional size).

1. `workspace/positions/<position_id>/position.md` must exist and have `status: open`;
   if not, stop and say so.
2. `entered`: append `{date, price, fraction}` to `fills`. Fraction default: the next
   unfilled tranche's fraction, or 1 without tranches. The first fill sets `opened` =
   the date. Set `entry` = the blended price of all fills. Refuse if the fills would
   exceed 1.
   `exited`: only after `opened` is set. Append `{date, price, fraction}` to `exits`.
   Fraction default: everything still held (sum of fills minus sum of exits); refuse
   more than that. When nothing is left: set `status: closed`, `closed` = the date and
   `exit_price` = the blended price of all exits.
3. Append a row to the trade log in `workspace/decisions/<position_id>.md`
   (date, action, price, size, with the fraction in the size column if no size given).
4. Confirm in one or two lines, with what is still held. After the final exit, suggest
   `/evaluate --run <run_id>`.

Trade facts go into the position file; nothing else from the decision file does.
