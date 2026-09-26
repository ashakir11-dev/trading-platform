---
name: approve
description: Approve (or reject) a proposed lesson for an agent
argument-hint: "<agent> <proposal_id> [reject]"
model: claude-sonnet-5
disable-model-invocation: true
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Arguments: $ARGUMENTS (agent, proposal_id, optionally `reject`).

1. Read `workspace/agents/<agent>/feedback/<proposal_id>.md`. It must exist and have
   `status: pending`.
2. **Reject:** set `status: rejected` and stop.
3. **Approve:** append one entry to `prompts/<agent>/lessons.md` (replace
   "(none yet)" on the first one):
   `- <the lesson, verbatim>. (Approved <YYYY-MM-DD>, proposal <proposal_id>.)`
   Set the proposal's `status: approved`.
4. Commit only that file: `git add prompts/<agent>/lessons.md` and
   `git commit -m "Approve lesson <proposal_id> for <agent>"`. Every later analysis
   records the prompt commit it ran with, so the effect of each lesson can be traced.
   If git is missing or the folder is not a git checkout, skip the commit and say so:
   the lesson is in effect, but runs record `prompt_commit: unversioned`.
5. Confirm in one line with the commit id (or that no commit was made).
