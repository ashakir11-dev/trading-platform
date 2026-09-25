# trading-platform

A multi-agent pipeline for trade research. It supports decisions only and never places orders.

Agent 0 (market scanner) → Agent 1 (sector deep dive) → company deep dive → technical
analysis → middleware report → **you decide** → Agent 5 (follow-up loop) → outcomes and
process review.

The design, its principles and its open decisions are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Layout

```
src/trading_pipeline/
  config.py            PipelineConfig / LLMConfig (open decisions are config switches)
  schemas.py           stage outputs (structured reasoning), records, positions
  llm.py               LLMClient protocol + AnthropicLLM (structured outputs)
  middleware.py        runs the stages, carries raw data forward, logs reasoning, user boundary
  store.py             SQLite: reasoning logs, snapshots, positions, reviews, isolated user decisions
  data/base.py         provider protocols, point-in-time RawDataBundle
  data/mcp.py          skeleton adapters for candidate vendors (Massive, read-only Robinhood)
  data/gaps.py         explicit placeholders for the open data gaps
  agents/              one module per agent
tests/                 scripted-LLM + fixture-data tests
```

## Dev

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest
```
