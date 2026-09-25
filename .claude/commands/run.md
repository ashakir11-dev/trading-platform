---
description: Run the trading pipeline end to end and report (live, as of now)
argument-hint: "[--max-sectors N] [--shortlist N]"
---
You are the middleware agent. Read `prompts/middleware/role.md`,
`prompts/middleware/report.md` and `prompts/formats.md`, and follow them.

Run the pipeline end to end, live, as of now. Options: $ARGUMENTS

1. Set up the run (run_id, as_of, prompt_commit, profile, run.md).
2. Launch `market-scanner` (mode `default`, subject `market`, no upstream).
3. Apply the forwarding rules to its sector calls.
4. Launch one `sector-deep-dive` per pursued sector, in parallel (mode `default`,
   subject = the sector as a slug, upstream = the market scanner's folder, task = the
   sector and its direction).
5. Apply the forwarding rules to the shortlists.
6. Launch one `company-deep-dive` per forwarded candidate, in parallel.
7. Launch one `technical-analysis` per candidate that passed, in parallel.
8. Run the recommendation check.
9. Write the report and show it.
