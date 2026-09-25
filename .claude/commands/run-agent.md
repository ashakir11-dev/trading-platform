---
description: Run one pipeline agent on its own (isolation mode)
argument-hint: "<agent> <subject> [instructions]"
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Run a single agent in isolation mode. Arguments: $ARGUMENTS
(first word: the agent; then its subject; anything after is passed as the task).

Agents available: `market-scanner` (subject: `market`), `sector-deep-dive`
(subject: a sector name, e.g. "Energy"; optionally "upside"/"downside"),
`company-deep-dive` and `technical-analysis` (subject: a ticker; optionally
"long"/"short"). For `technical-analysis`, copy the profile into the run folder as
usual and pass it in the brief.

1. Set up the run as usual, with `mode: isolation` in `run.md`.
2. Launch the agent with `mode: isolation`, `upstream: none`, and the subject and
   instructions as the task.
3. When it returns, show the user a short summary of its analysis (the frontmatter
   fields and the main conclusion, in a few lines) and the folder path. Record it in
   `run.md` and set `status: complete`. No forwarding, no report file.
