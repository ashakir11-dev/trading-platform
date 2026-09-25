# trading-platform

Multi-agent trading research pipeline. **Read `docs/ARCHITECTURE.md` before changing
any agent, schema, or the middleware** — it holds the design principles (raw-data
pass-through, structured reasoning, one-way middleware, split outcomes/process review)
and the open decisions.

Hard rules:
- Decision support only. Never add order-placing code; any quotes/brokerage adapter stays read-only.
- Data vendors are not decided (Massive/Robinhood are only candidates). Agents must depend on
  the provider protocols in `data/base.py`, never on a specific vendor.
- User accept/reject decisions must never reach the process-review agent or any stage prompt.
- Every data access takes `as_of`; never let a stage see data dated after the run's `as_of`.

Dev: `python -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]' && pytest`
Set `EQUIBLES_TEST_DSN` (a scratch UTF-8 Postgres database) to also run the Equibles SQL tests.
