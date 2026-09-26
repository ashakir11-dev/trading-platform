# trading-platform

Multi-agent trading research pipeline built as Claude Code subagents. **Read
`docs/ARCHITECTURE.md` before changing any agent, prompt or command** — it holds the
design principles (raw-data pass-through, structured reasoning, one-way middleware,
split outcomes/reasoning review) and the open decisions — and
`docs/prompt-subagents-design.md` for how the subagents, hooks and workspace implement them.

Hard rules:
- Decision support only. Never add order-placing code; any quotes/brokerage adapter stays read-only.
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
