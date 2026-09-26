---
description: Grade past runs against what happened since (per agent), and review your own decisions
argument-hint: "[--run RUN_ID] [--agent AGENT] [--min-days N]"
---
You are the middleware agent. Read `prompts/middleware/role.md` and
`prompts/formats.md`, and follow them.

Evaluate past runs. Arguments: $ARGUMENTS

1. Set up a run as usual with `mode: evaluation` in `run.md` (its `as_of` is the
   evaluation date, `eval_as_of`).
2. **Pick what to evaluate.** With `--run`, that run. Otherwise every run in
   `workspace/runs/` with mode `live` or `backtest`, `status: complete`, and an
   `as_of` at least `--min-days` (default 7) days old, whose last evaluation for that
   agent (the newest `workspace/agents/<agent>/evaluations/<run_id>--*`) is older than 7
   days or missing. With `--agent`, only that agent. Agents: `market-scanner`,
   `sector-deep-dive`, `company-deep-dive`, `technical-analysis`, `follow-up`; skip an
   agent with no analyses in that run.
3. Launch one `stage-evaluator` per (run, agent), in parallel, with this brief:
   `evaluated_agent`, the run's `run_id`, `run_mode` and `point_in_time` (from its
   `run.md`), the run's `as_of`, `eval_as_of`, the agent's analysis folders for that run
   as `upstream`, the run's profile, the run's positions (position files whose `plan:`
   points into that run: trade facts only), and `analysis_folder` =
   `workspace/agents/<agent>/evaluations/<run_id>--<YYYYMMDD of eval_as_of>`.
4. **Your decisions (D0).** For each candidate in the evaluated runs that has a file in
   `workspace/decisions/`, write `workspace/decisions/reviews/<candidate_id>--<YYYYMMDD>.md`:
   the decision and the note, the trade log, the technical-analysis evaluation's outcome
   for that candidate, and where the user and the agents differed (e.g. rejected a plan
   whose target was hit; accepted one whose stop was hit; exited earlier or later than
   the plan). Plain facts, no advice. **This is for the user only:** never copy it, or
   anything from a decision, into an agent brief, an evaluation, an analysis or a run
   folder.
5. Write `workspace/runs/<run_id>/report.md` with the agents' results: per agent and
   run, the summary metrics, the subjects that worked and didn't, the attributions and
   the patterns. Then show it, and after it, **in chat only**, a short "Your decisions"
   section from step 4. Suggest `/feedback <agent>` for agents whose evaluations show a
   repeated pattern.
