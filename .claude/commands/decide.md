---
description: Record your accept/reject for a recommended candidate
argument-hint: "<candidate_id> accept|reject [note]"
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Record the user's decision. Arguments: $ARGUMENTS
(candidate_id, then `accept` or `reject`, then an optional free-text note).

1. The run is the part of the candidate_id before the last `-`. Read its
   `workspace/runs/<run_id>/run.md`. The candidate must be listed under
   "Recommendations"; if not, stop and tell the user (only recommended candidates can be
   decided).
2. If `workspace/decisions/<candidate_id>.md` already exists, stop: a candidate is
   decided once.
3. Write `workspace/decisions/<candidate_id>.md` in the format of `prompts/formats.md`,
   with `decided_at` = now, the note verbatim under "Why", and an empty trade log.
4. On `accept`: create `workspace/positions/<candidate_id>/position.md` from the
   technical analysis plan the recommendation points to (entry, stop, target, horizon,
   direction) and the profile's `level_trigger`, with `status: open` and `opened` empty
   until the user reports the trade. Trade facts only: never the note.
   On `reject`: nothing else is created.
5. Confirm in two lines what was recorded and, on accept, that the position is now
   watched and that the user places the trade themselves.

The decision and note never go into any other file.
