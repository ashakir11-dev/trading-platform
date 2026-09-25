# trading-platform

Multi-agent trading research pipeline. **Read `docs/ARCHITECTURE.md` before changing
any agent, schema, or the middleware** — it holds the design principles (raw-data
pass-through, structured reasoning, one-way middleware, split outcomes/process review)
and the open decisions. The system is moving to prompt-based subagents: read
`docs/prompt-subagents-design.md` before adding or changing a subagent, prompt or command.

Hard rules:
- Decision support only. Never add order-placing code; any quotes/brokerage adapter stays read-only.
- Equibles is the data vendor; anything it doesn't provide is deferred, not sourced elsewhere.
  (The existing Python pipeline's agents depend only on the provider protocols in `data/base.py`.)
- Agents reach MCP servers only through the tools listed in their subagent definition (`.claude/agents/*.md`),
  read-only tools only; every Equibles write tool (portfolios, lots, watches, reports) stays on the deny list
  in `.claude/settings.json`.
- User accept/reject decisions must never reach the process-review agent or any stage prompt.
- Every run has an `as_of`; agent prompts must forbid using data dated after it, and every tool result an agent
  used is kept in its `raw/` folder so this can be checked. In backtests, stage agents get no data tools: only
  the gatekeeper agent calls Equibles, and every data pack passes the pit-auditor before a stage agent reads it.

Dev: `python -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]' && pytest`
Set `EQUIBLES_TEST_DSN` (a scratch UTF-8 Postgres database) to also run the Equibles SQL tests.
