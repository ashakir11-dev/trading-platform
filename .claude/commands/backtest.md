---
description: Run the pipeline as of a past date, with audited point-in-time data packs
argument-hint: "--as-of YYYY-MM-DD[THH:MM:SSZ] [--max-sectors N] [--shortlist N] [--allow-current-constituents]"
---
You are the middleware agent. Read `prompts/middleware/role.md`,
`prompts/middleware/backtest.md`, `prompts/middleware/report.md` and
`prompts/formats.md`, and follow them.

Run the pipeline end to end as a backtest. Options: $ARGUMENTS

Same stages and forwarding rules as `/run` (market-scanner → sector-deep-dive per
pursued sector → company-deep-dive per candidate → technical-analysis per passing
candidate → recommendation check), but every stage agent is its `-backtest` variant and
gets an audited data pack built first, as `prompts/middleware/backtest.md` describes.
