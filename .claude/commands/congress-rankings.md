---
description: Rebuild the Congress member scorecard (for cron)
argument-hint: ""
model: claude-sonnet-5
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Rebuild the member scorecard that every congress-analyst candidate-signal run reads.

1. Set up a run as usual with `mode: rankings` in `run.md`, subject `roster`.
2. Launch `congress-analyst-rankings` (mode `rankings`, subject `roster`, upstream
   `none`), with the output path `workspace/congress/member_rankings.md` in the brief.
3. Record the result in `run.md` and set `status: complete`. No forwarding, no report
   file — the next `/run` picks up the new scorecard automatically by copying it into
   its own run folder.
