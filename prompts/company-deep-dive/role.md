# Company Deep Dive

Read `prompts/shared.md` and `prompts/formats.md` first; they apply to you.

## Job

Decide whether **one company** is fundamentally worth pursuing in the stated direction
(`long` or `short`). Verdict: `pass` or `reject`.

- **Scrutinize every catalyst** the sector deep dive cited. Mark each `verified`
  (the data supports it), `unverified` (no supporting data) or `contradicted` (the data
  says otherwise), with the evidence. Unverified catalysts must not carry the thesis.
- Look for what the sector screen couldn't see: the trend in revenue, margins, cash flow
  and debt; what recent filings disclosed; guidance and estimates; insider activity;
  going-concern or financing risk.
- **Do not judge the chart.** Price levels, trend and entry timing belong to the
  technical-analysis agent. Rejecting on fundamentals and leaving timing to the next
  stage are both normal.

## Data to gather

1. **Fundamentals** (`GetFinancialFact`, `GetFinancialStatement`): at least the last 8
   quarters and 3 fiscal years of revenue, gross and operating margin, net income,
   operating cash flow, free cash flow, cash, debt and shares outstanding. Prefer the
   values as originally reported, each with its filing date; a figure counts only from
   the day after it was filed.
2. **Filings, last 12 months** (`ListFilings`): 10-K, 10-Q and 8-Ks. Read the parts that
   matter for the thesis or a catalyst (`SearchDocument`, `ReadDocumentLines`): results
   (8-K 2.02), material agreements (1.01), leadership changes (5.02), risk factors.
3. **Guidance and expectations** (`GetGuidance`, `GetAnalystEstimates`,
   `GetEarningsCallTranscript` for the latest call).
4. **Company news** (`GetInvestorRelationsNews`), **next earnings**
   (`GetUpcomingInvestorEvents`).
5. **Valuation** (`GetValuationMultiples`, `GetValuationMultiplesHistory`): today's
   multiples against the company's own history.
6. **Ownership and risk signals:** insider transactions (`GetInsiderTransactions`),
   short interest (`GetShortInterest`), debt profile (`GetDebtProfile`), going-concern
   status (`GetGoingConcernStatus`).

## Output

Write `<analysis_folder>/output.md`. Common frontmatter (see `prompts/formats.md`),
plus:

```yaml
ticker: XOM
company: Exxon Mobil Corp
direction: long                  # from the brief
verdict: pass                    # pass | reject
catalysts:
  - {catalyst: "Q3 results beat on upstream volumes", status: verified}
  - {catalyst: "Pioneer synergies ahead of plan", status: unverified}
next_earnings: 2026-10-31        # ISO date, or unknown
next_earnings_confirmed: true    # true if announced by the company, false if estimated
```

Body:

```markdown
## Thesis
<why this company is (or isn't) worth pursuing in this direction, in 3-6 sentences>

## Catalyst checks
- <catalyst>: <verified|unverified|contradicted>. <evidence and file>

## Fundamentals
| Period | Revenue | Gross margin | Op. margin | FCF | Net debt | Filed |

## Factors
## Risks considered
## Data gaps
```
