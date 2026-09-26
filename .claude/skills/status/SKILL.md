---
name: status
description: Show where things stand - recent runs, recommendations awaiting your decision, open positions and their last alerts, pending lessons. Use when the user asks what is going on, what is open or what to do next.
argument-hint: "[--runs N]"
model: claude-sonnet-5
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Show the user where things stand. Arguments: $ARGUMENTS (`--runs N`: how many recent
runs to list, default 5). Read files only; start no agent and write nothing.

If `workspace/` does not exist, say that nothing has run yet and suggest `/setup`.
Otherwise report, in short sections (skip an empty one):

1. **Recent runs.** The newest N folders in `workspace/runs/`: from each `run.md`
   frontmatter the `run_id`, `mode`, `as_of`, `status`, and the number of
   recommendations; for a live or backtest run, the path of its `report.html`.
2. **Awaiting your decision.** Candidates listed under "Recommendations" in a complete
   live run's `run.md` that have no `workspace/decisions/<candidate_id>.md` yet, with
   entry / stop / target and the command `/decide <candidate_id> accept|reject [note]`.
3. **Open positions.** `workspace/positions/*/position.md` with `status: open`: ticker,
   direction, entry / stop / target, `opened` (or "not entered yet" and the command
   `/trade <position_id> entered <price>`), `last_check`, and the last line of
   `alerts.md`. Suggest `/follow-up` if no check ran today.
4. **Pending lessons.** `workspace/agents/*/feedback/*.md` with `status: pending`: the
   agent, the proposal id and the lesson in one line, with `/approve <agent> <proposal_id>`.
5. **Evaluations due.** Complete live or backtest runs at least 7 days old with no
   evaluation yet: suggest `/evaluate`.

This summary is for the user only: nothing from `workspace/decisions/` goes anywhere
else.
