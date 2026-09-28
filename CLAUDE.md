# trading-platform

Multi-agent trading research pipeline built as Claude Code subagents. **Read
`docs/ARCHITECTURE.md` before changing any agent, prompt or command** — it holds the
design principles (raw-data pass-through, structured reasoning, one-way middleware,
split outcomes/reasoning review) and the open decisions — and
`docs/prompt-subagents-design.md` for how the subagents, hooks and workspace implement them.

Hard rules:
- Decision support, with paper-trading execution for forward testing (decided 2026-09-28; was
  "decision support only, no order-placing code" before). The only order-placing code is
  `scripts/broker_alpaca.py`, hard-coded to Alpaca's **paper** endpoint (never configurable to a live
  account); it is a plain script, not an MCP tool or subagent capability, so no stage/follow-up/evaluator
  agent can call it. Only the middleware agent may run it, and only from `/trade`, and only when the user
  types that command — never on the pipeline's own initiative. Every quotes/data adapter besides it stays
  read-only.
- Equibles is the data vendor; anything it doesn't provide is deferred, not sourced elsewhere.
- Agents reach MCP servers only through the tools listed in their subagent definition (`.claude/agents/*.md`),
  read-only tools only; every Equibles write tool (portfolios, lots, watches, reports) stays on the deny list
  in `.claude/settings.json`.
- User accept/reject decisions must never reach any agent (stage, follow-up, evaluator or feedback) or prompt;
  only the middleware agent reads `workspace/decisions/`.
- Every run has an `as_of`; agent prompts must forbid using data dated after it, and every tool result an agent
  used is kept in its `raw/` folder so this can be checked. In backtests, stage agents get no data tools: only
  the gatekeeper agent calls Equibles, and every data pack passes the pit-auditor before a stage agent reads it.

Subagent pipeline: prompts in `prompts/`, subagents and commands in `.claude/`, run data in git-ignored
`workspace/`. `.claude/hooks/workspace_guard.py` enforces the decisions firewall, the read-only tool rule and
raw-data capture, and turns price responses into statistics (`price_stats.py`, arithmetic only); keep
`tests/test_workspace_guard.py` and `tests/test_price_stats.py` passing when changing them.
`scripts/render_report.py` lays out the middleware's `report.json` as `report.html` (layout and plan distances
only, no network); keep `tests/test_render_report.py` passing.

Dev: `pip install pytest && pytest` (tests cover the hooks). Running the pipeline: `docs/operations.md`.
Paper trading setup and the `/trade` broker workflow: `docs/operations.md` §1 and §4; keep
`tests/test_broker_alpaca.py` passing when changing `scripts/broker_alpaca.py`.
