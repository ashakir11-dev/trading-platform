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

| # | Ticker | Company | Score | Passed | Forwarded | One-line case |
|---|---|---|---|---|---|---|

## Candidates
| Candidate | Company deep dive | Catalysts (verified / unverified / contradicted) | Technical | Why, in one line |
|---|---|---|---|---|

## Recommendations
<candidate_id, ticker, direction, entry / stop / target, horizon, rule flags>
<"None: ..." with the reason when empty>

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
each recommendation as a card with its price ladder, max loss, potential gain,
reward:risk, catalysts, flags and the agents' confidence. The script lays out and
computes the plan distances; every word comes from your JSON, so the same rules apply
as for `report.md`: copy the agents' values and words, never soften or add to them.

```json
{
  "run_id": "20260925T213314Z",
  "as_of": "2026-09-25T21:33:14Z",
  "prompt_commit": "174a3ea",
  "profile": {"name": "<profile name>", "max_loss_per_trade_pct": 8, "min_reward_to_risk": 2},
  "backtest": null,
  "funnel": {"sectors_called": 4, "sectors_pursued": 1, "companies_screened": 25,
             "candidates": 3, "passed_company": 2, "recommended": 1},
  "recommendations": [{
    "candidate_id": "20260925T213314Z-XOM", "ticker": "XOM", "company": "Exxon Mobil Corp",
    "sector": "Energy", "direction": "long", "horizon": "swing",
    "entry": 118.40, "stop": 111.00, "target": 134.00,
    "entry_condition": "daily close above 118.40 (breakout over the August high)",
    "invalidation": "daily close back below 113.50",
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
  `flags` are the technical rules with `outcome: flag`.
- With no recommendations, `recommendations` is `[]` and `no_recommendation_reason` is
  the "None: ..." line of `report.md`.
- Backtests: `backtest` is `{"point_in_time": "<audited | leaks-found>", "limits":
  ["<each limit the first line of report.md names>"]}`.
- Unknown values are `null`; the page leaves them out.
- If the script fails, record it under "Errors" in `run.md` and carry on: `report.md`
  is the report of record.
