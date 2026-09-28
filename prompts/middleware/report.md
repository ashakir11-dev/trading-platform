# The report to the user

Plain, factual, scannable. It is the user's basis for decisions, so it must never
overstate: say what each agent concluded and how confident it was, and put
disagreements and data gaps where they can't be missed.

```markdown
# Pipeline run <run_id>
As of <as_of> · prompt <prompt_commit> · profile <name> · options <...>

## Market
<the market scanner's market summary, shortened to one paragraph>

| Sector | Direction | Confidence | Pursued? |
|---|---|---|---|

## <Sector> (<direction>)
<the sector deep dive's sector view in 2-3 sentences; say if it disagreed with the call>

| # | Ticker | Company | Score | Bucket | Passed | Forwarded | One-line case |
|---|---|---|---|---|---|---|---|

## Candidates
| Candidate | Bucket | Company deep dive | Catalysts (verified / unverified / contradicted) | Technical | Why, in one line |
|---|---|---|---|---|---|---|

## Recommendations
<at most one per risk_bucket, in the order core, growth, speculative; say "picked by
pick score = company confidence × technical confidence">
<candidate_id, ticker, direction, bucket, position size %, entry / stop / targets (with
fractions), horizon, entry valid until, pick score, rule flags>
<"None: ..." with the reason when empty>

## Also passed (tracked, not recommended)
<every other eligible candidate, same fields, grouped by bucket; one line each. These
are graded by the evaluator exactly like the recommendations.>

## Not pursued / rejected
- <subject>: <stage>: <reason>

## Conflicts
## Data gaps that mattered
<the gaps agents said lowered their confidence>
## Errors

Decide with: /decide <candidate_id> accept|reject [note]
Files: workspace/runs/<run_id>/ and each agent's analysis folder.
```

Never include anything from `workspace/decisions/`.

## The showcase page (report.html)

After `report.md`, write `workspace/runs/<run_id>/report.json` and render it:

```
python3 scripts/render_report.py workspace/runs/<run_id>/report.json
```

This writes `report.html` next to it: one self-contained page (no network) that shows
each recommendation as a card — collapsed to a one-line trade summary (ticker, bucket,
entry / stop / targets, max loss, reward:risk, flags), expanding to the price ladder,
the chart of the primary timeframe with the plan's levels drawn from the agent's own
`raw/` bars, catalysts, risks and the agents' confidence. Recommendations open
expanded; "also passed" candidates are listed collapsed below them. The script lays out and
computes the plan distances; every word comes from your JSON, so the same rules apply
as for `report.md`: copy the agents' values and words, never soften or add to them.

```json
{
  "run_id": "20260925T213314Z",
  "as_of": "2026-09-25T21:33:14Z",
  "prompt_commit": "174a3ea",
  "profile": {"name": "<profile name>", "buckets": {
    "core": {"max_loss_per_trade_pct": 5, "min_reward_to_risk": 1.5, "position_size_pct": 3, "entry_style": "pullback"},
    "growth": {"max_loss_per_trade_pct": 8, "min_reward_to_risk": 2, "position_size_pct": 2, "entry_style": "either"},
    "speculative": {"max_loss_per_trade_pct": 15, "min_reward_to_risk": 3, "position_size_pct": 1, "entry_style": "breakout"}
  }},
  "backtest": null,
  "funnel": {"sectors_called": 4, "sectors_pursued": 1, "companies_screened": 25,
             "candidates": 3, "passed_company": 2, "eligible": 2, "recommended": 1},
  "recommendations": [{
    "candidate_id": "20260925T213314Z-XOM", "ticker": "XOM", "company": "Exxon Mobil Corp",
    "sector": "Energy", "direction": "long", "risk_bucket": "growth", "horizon": "swing",
    "pick_score": 0.42, "position_size_pct": 2,
    "entry": 118.40, "stop": 111.00, "target": 134.00,
    "targets": [{"price": 128.00, "fraction": 0.5}, {"price": 140.00, "fraction": 0.5}],
    "entry_valid_until": "2026-10-09",
    "entry_condition": "daily close above 118.40 (breakout over the August high)",
    "invalidation": "daily close back below 113.50",
    "chart": {"bars": "workspace/agents/technical-analysis/analyses/<run_id>/XOM/raw/006-GetStockPrices.json",
              "timeframe": "1d"},
    "current_price": {"price": 117.10, "source": "live_quote", "at": "2026-09-25T19:45:00Z"},
    "thesis": "<the company deep dive's Thesis, shortened to 1-2 sentences>",
    "setup": "<the technical analysis's Setup, shortened to 1-2 sentences>",
    "catalysts": [{"catalyst": "Q3 results beat on upstream volumes", "status": "verified"}],
    "next_earnings": "2026-10-31", "next_earnings_confirmed": true,
    "flags": [{"rule": "upcoming_earnings", "detail": "2026-10-31 (confirmed) in 36 days, inside 45"}],
    "key_risks": ["<at most 3 risks from the two analyses' Risks considered, one line each>"],
    "confidence": {"company_deep_dive": 0.7, "technical_analysis": 0.6},
    "files": {"company_deep_dive": "workspace/agents/company-deep-dive/analyses/<run_id>/XOM",
              "technical_analysis": "workspace/agents/technical-analysis/analyses/<run_id>/XOM"}
  }],
  "also_passed": [],
  "no_recommendation_reason": null,
  "market": {"summary": "<the one-paragraph market summary from report.md>",
             "sectors": [{"sector": "Energy", "direction": "upside", "confidence": 0.65,
                          "pursued": true, "note": ""}]},
  "not_pursued": [{"subject": "CVX", "stage": "technical-analysis", "reason": "reward_to_risk 1.4 < 2.0"}],
  "conflicts": [], "data_gaps": [], "errors": []
}
```

- Plan numbers, flags, catalysts, `next_earnings` and confidences are copied from the
  frontmatter of the candidate's technical-analysis and company-deep-dive `output.md`;
  `flags` are the technical rules with `outcome: flag`. `risk_bucket` is copied from
  the sector deep dive's shortlist entry for this ticker (unchanged since).
- `profile.buckets` lists every bucket's `max_loss_per_trade_pct`, `min_reward_to_risk`,
  `position_size_pct` and `entry_style` so the page can show which profile applied to
  each recommendation without re-deriving them.
- `targets`, `target`, `entry_valid_until` and `pick_score` come from the plan and the
  recommendation check; `position_size_pct` from the bucket's profile.
- `chart.bars` is the technical agent's `raw/` file holding the primary chart's daily
  bars (the `GetStockPrices` response for the plan's `chart_timeframe`; for `1w` the
  page builds weekly bars from the daily ones). The script draws the chart from that
  file with the plan's levels; if the file is missing the card has no chart.
- `also_passed` holds the eligible candidates that were not the bucket's pick, in the
  same shape as `recommendations`; the page lists them collapsed under the picks.
- With no recommendations, `recommendations` is `[]` and `no_recommendation_reason` is
  the "None: ..." line of `report.md`.
- Backtests: `backtest` is `{"point_in_time": "<audited | leaks-found>", "limits":
  ["<each limit the first line of report.md names>"]}`.
- Unknown values are `null`; the page leaves them out.
- If the script fails, record it under "Errors" in `run.md` and carry on: `report.md`
  is the report of record.
