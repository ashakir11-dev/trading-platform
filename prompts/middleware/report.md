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
