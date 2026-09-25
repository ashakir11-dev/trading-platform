# Agent 1: Sector Deep Dive

Read `prompts/shared.md` and `prompts/formats.md` first; they apply to you.

## Job

Examine **one sector** and screen its companies into a **ranked shortlist** for the
company deep dive. Work from cheap bulk data: full company financials are pulled
later, only for your shortlist, so screen broadly and let the deep dive verify.

- For **every** company you evaluate, give a `potential_score` (0-100, relative within
  this sector, in the sector call's direction: for a downside call it scores downside
  potential) and a `passed` flag.
- List each company's catalysts with the data they came from.
- Include notable companies you reject (`passed: false`) so the record shows what was
  filtered out and why.
- Aim for roughly 10-30 companies evaluated. Pass only those with a real case.

## Data to gather

1. **Constituents:** the sector ETF's holdings (`GetEtfHoldings`): the top 25 by weight,
   with tickers. The report counts only once public (report period + 60 days); note its
   date. ETF by sector: see `prompts/market-scanner/role.md`.
2. **Screen:** ratios and size per company (`ScreenStocks`, `GetValuationMultiples`):
   market cap, valuation multiples, growth and margins where available.
3. **Prices and breadth:** daily bars for about six months per constituent
   (`GetStockPrices`): 1m / 3m / 6m return, vs the 50- and 200-day moving average, vs
   the sector ETF. Breadth: share of constituents above each moving average.
4. **Events, last 90 days and upcoming:** 8-K filings (`ListFilings`; the item numbers
   say what happened, e.g. 2.02 results, 1.01 material agreement, 5.02 leadership),
   company press releases (`GetInvestorRelationsNews`), upcoming earnings
   (`GetUpcomingInvestorEvents`), and for Health Care the FDA advisory meetings
   (`GetFdaAdvisoryCommitteeMeetings`).

## Output

Write one file per company **as soon as you have judged it**, then the sector file.

`<analysis_folder>/companies/<TICKER>.md`:

```markdown
---
ticker: XOM
company: Exxon Mobil Corp
potential_score: 78
passed: true
confidence: 0.6
---
## Case
<2-4 sentences>

## Catalysts
- [earnings|fda|analyst_action|product|regulatory|macro|m_and_a|other] <description>. Expected: <ISO date or unknown>. Source: <file>

## Factors
## Risks considered
## Data gaps
```

`<analysis_folder>/analysis.md`: common frontmatter (see `prompts/formats.md`), plus:

```yaml
sector: Energy
direction: upside                # from the sector call
etf: XLE
shortlist:                       # every company evaluated, highest potential_score first
  - {ticker: XOM, potential_score: 78, passed: true}
  - {ticker: CVX, potential_score: 64, passed: true}
  - {ticker: OXY, potential_score: 31, passed: false}
```

Body:

```markdown
## Sector view
<do you agree with the sector call? breadth, dispersion, what drives the ranking>

## Ranking
| # | Ticker | Company | Score | Passed | One-line case |

## Data gaps
```

`confidence` in `analysis.md` is your confidence in the sector view; each company file
has its own.
