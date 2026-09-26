---
description: Propose lessons for one agent from its evaluations
argument-hint: "<agent>"
model: claude-sonnet-5
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Run feedback for one agent. Arguments: $ARGUMENTS (the agent).

1. List `workspace/agents/<agent>/evaluations/`. Fewer than 2 evaluations: say so and
   stop (a lesson needs a pattern across evaluations).
2. Launch `stage-feedback` with a brief naming the agent, the evaluation folders (all of
   them), `upstream` = those folders, and the proposals folder
   `workspace/agents/<agent>/feedback/`.
3. Show each new proposal: its id, the lesson, the evidence in one line, and the command
   `/approve <agent> <proposal_id>` or `/approve <agent> <proposal_id> reject`.

The user's decisions never go into the brief.
