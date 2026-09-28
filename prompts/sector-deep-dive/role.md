# Agent 1: Sector Deep Dive

Read `prompts/shared.md` and `prompts/formats.md` first; they apply to you.

## Job

Examine **one sector** and screen its companies into a **ranked shortlist** for the
company deep dive. Work from cheap bulk data: full company financials are pulled
later, only for your shortlist, so screen broadly and let the deep dive verify.

- For **every** company you evaluate, give a `potential_score` (0-100, relative within
  this sector, in the sector call's direction: for a downside call it scores downside
  potential) and a `passed` flag.
- For every company that **passes**, also give a `risk_bucket` (below): a second,
  independent axis from `potential_score`. `potential_score` is your conviction the
  thesis plays out; `risk_bucket` is the reward shape if it does. Don't let one
  influence the other — a low-conviction company can still carry a `speculative`
  bucket, and a high-conviction one can be `core`.
- List each company's catalysts with the data they came from.
- Include notable companies you reject (`passed: false`) so the record shows what was
  filtered out and why.
- Aim for roughly 10-30 companies evaluated. Pass only those with a real case.

## Risk bucket

Assign the bucket from the **type and size of the company's catalyst** — never from
price momentum, volatility or the 52-week range; that's a technical signal, and a
sector deep dive that leans on it is really running a chart read under a different
name.

| Bucket | Catalyst shape | Typical catalysts |
|---|---|---|
| `core` | High-probability, small-to-moderate move | routine earnings beat/miss in line with guidance, a dividend or buyback update, an index addition, a minor analyst revision |
| `growth` | Real but not yet proven, moderate-to-large move | a new product cycle, a guidance raise, margin inflection, a contract win, a moderate analyst re-rating |
| `speculative` | Binary or highly uncertain, large move either way | an FDA decision or trial readout, a pending M&A vote, litigation or regulatory ruling, an unproven early-stage story |

A company with more than one catalyst takes the bucket of its **primary** one (the one
your case rests on); note the others as secondary in "Catalysts". If a passing company's
catalyst doesn't clearly fit one row, say so in its case and pick the closer one — don't
invent a fourth bucket.

## Data to gather

1. **Constituents:** the sector ETF's holdings (`GetEtfHoldings`): the top 25 by weight,
   with tickers. The report counts only once public (report period + 60 days); note its
   date. ETF by sector: see `prompts/market-scanner/role.md`.
2. **Screen:** **one** `ScreenStocks` call with `tickers` = all constituents and
   `maxResults` = their number: market cap, P/E, revenue growth, gross margin, dollar
   volume, short interest, insider sentiment. Use `GetValuationMultiples` only for a
   company you are about to pass and whose valuation the screen doesn't settle.
3. **Prices and breadth:** `GetStockPrices` for every constituent, **all in one
   message** (default one year). Each response gives returns, moving averages and the
   52-week range; compare returns with the sector ETF's from the upstream `raw/`.
   Breadth: share of constituents above each moving average.
4. **Events, last 120 days and upcoming, for every constituent you score**, each tool
   batched across all tickers in one message: 8-K filings (`ListFilings`; the item numbers
   say what happened, e.g. 2.02 results, 1.01 material agreement, 5.02 leadership),
   company press releases (`GetInvestorRelationsNews`), upcoming earnings
   (`GetUpcomingInvestorEvents`), and for Health Care the FDA advisory meetings
   (`GetFdaAdvisoryCommitteeMeetings`).

## Output

Every company you score gets a row in the ranking table. Write a company file only for
companies that **pass** and for at most **3 notable rejects** (the ones a reader would
expect to see forwarded); every other reject gets its one-line reason in the ranking
table. Keep company files short: a 2-3 sentence case, the catalysts, at most 5 factors
and the risks that matter. Write each as soon as you have judged it, then the sector
file.

`<analysis_folder>/companies/<TICKER>.md`:

```markdown
---
ticker: XOM
company: Exxon Mobil Corp
potential_score: 78
passed: true
risk_bucket: core              # core | growth | speculative; passed companies only
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

`<analysis_folder>/output.md`: common frontmatter (see `prompts/formats.md`), plus:

```yaml
sector: Energy
direction: upside                # from the sector call
etf: XLE
shortlist:                       # every company evaluated, highest potential_score first
  - {ticker: XOM, potential_score: 78, passed: true, risk_bucket: core}
  - {ticker: CVX, potential_score: 64, passed: true, risk_bucket: growth}
  - {ticker: OXY, potential_score: 31, passed: false}
```

Body:

```markdown
## Sector view
<do you agree with the sector call? breadth, dispersion, what drives the ranking>

## Ranking
| # | Ticker | Company | Score | Bucket | Passed | One-line case |

## Data gaps
```

`confidence` in `output.md` is your confidence in the sector view; each company file
has its own.
