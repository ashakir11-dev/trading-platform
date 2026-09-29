---
name: trading-platform
description: Entry point for the trading-platform pipeline in this repo. Use when the user wants to run, backtest, evaluate, or trade against the multi-agent trading research pipeline, or asks what this repo does. Points to the real commands rather than reimplementing them.
---

# trading-platform

This repo's trading pipeline is driven by slash commands, not by this skill's
own instructions — this file only routes you to them. **Read `CLAUDE.md`
first**; it holds the hard rules (paper-trading-only, the decisions firewall,
raw-data capture) that every command below depends on and that this skill
does not re-enforce on its own.

Before changing any agent, prompt, or command, also read
`docs/ARCHITECTURE.md` and `docs/prompt-subagents-design.md`.

## Commands

- `/run` — run the pipeline end to end, live, as of now
- `/run-agent` — run one pipeline agent on its own (isolation mode)
- `/backtest` — run the pipeline as of a past date, with audited point-in-time data
- `/decide` — record accept/reject on a recommended candidate; on accept, places the sized paper entry order
- `/trade` — record entry/exit on an accepted position, or place/check a paper order for it
- `/follow-up` — one follow-up tick over an open position
- `/evaluate` — grade past runs against what happened since
- `/feedback` — propose lessons for one agent from its evaluations
- `/approve` — approve or reject a proposed lesson for an agent

Operational setup (paper trading credentials, running the pipeline) is in
`docs/operations.md`.

This skill is only discoverable inside this repository: the pipeline's
safety guarantees live in `.claude/hooks/workspace_guard.py`,
`.claude/agents/*.md` tool allowlists, `.claude/settings.json`, and
`.mcp.json`, none of which travel with this file if copied elsewhere.
