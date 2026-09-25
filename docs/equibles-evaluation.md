# Equibles evaluation

*Checked 2026-09-25 against the source at commit `67072d4`
([github.com/daniel3303/Equibles](https://github.com/daniel3303/Equibles)), plus a
screenshot of the Cloud pricing page the user shared. equibles.com and sec.gov are blocked
from the research environment, so nothing here was run against live data.*

## What it is

- An open-source (AGPL-3.0) server that runs in Docker with PostgreSQL. It collects public
  data into your own database and serves it over MCP.
- Sources: SEC EDGAR (XBRL financials, filings, 13F, Forms 3/4/5/144), FRED, FDA.gov,
  FINRA/SEC short data, CFTC, CBOE, congressional trades and USAspending.
- **Self-hosted daily prices come from Yahoo Finance.**
- Scrapers start from 2020 by default, configurable back to 2000.
- No order or trading tools.

## Point-in-time check on SEC financials (code review)

| Question | Finding | Evidence |
|---|---|---|
| Are restatements kept or overwritten? | **Kept.** Each value is its own row, keyed by accession number and carrying `FiledDate`. | `FinancialFact.cs` docstring: "Restatements are retained as separate rows discriminated by AccessionNumber". The unique index includes `AccessionNumber`. |
| Does it delete anything? | Yes. A quality filter removes rows from lower-ranked forms (proxies, registration statements, some 8-Ks) when a 10-K/10-Q states the same period. It also removes obvious ×1,000 or ×1,000,000 scale errors. | `FinancialFactImportQualityFilter.cs` |
| Does the filter create look-ahead? | **No.** At worst, a value becomes visible later (at the 10-Q/10-K filing date) than it could have from an earlier 8-K. That delay is conservative, not leaky. | Same file |
| Can the query tools answer "as of date D"? | **Not directly.** The MCP tools offer "latest restated" (leaks look-ahead) or `asOriginallyReported` (first periodic filing). Neither means "latest filed on or before D": a restatement filed before D should be visible at D but isn't under `asOriginallyReported`. `toDate` filters by period end, not by filing date. | `FinancialFactsTools.cs` lines ~64–85, ~756–767 |

**Conclusion:** the stored data **is point-in-time capable**, but the MCP query layer is
not. A `FundamentalsProvider` adapter must read the self-hosted Postgres tables directly
with `filed_date < as_of` (make a value visible from the next trading day after its filing
date, since `FiledDate` has no time), and pick the latest filed row per concept and period.
For backtests, avoid the "latest restated" tools entirely.

## Cloud plans (from the user's screenshot)

| Plan | Price | Prices | API |
|---|---|---|---|
| Free | $0 | End-of-day. Intraday, live and option-chain calls return an upgrade link | 100 req/day (MCP + REST shared) |
| Plus | $9.99/mo | Stocks and options **15-min delayed** | 10,000 req/day |
| Pro | $49.99/mo ($19.99 first month) | **Real-time** stocks and options | "Everything in Plus" and more; up to 5 web feeds |
| Custom | Quote | Broader coverage, redistribution rights | Custom |

Cloud has a REST API, which the self-hosted README doesn't mention. Unknown for Cloud:
whether prices are consolidated or single-venue, which vendor licenses them, whether
delisted tickers are covered, whether there is a batch/snapshot endpoint, whether REST
supports as-of-filing-date queries, and the personal-use license terms.

## Fit for this pipeline

| Role | Verdict |
|---|---|
| SEC fundamentals, filings, 8-K, ownership, insider, macro (FRED), FDA outcomes | **Good candidate (self-hosted).** Replaces several free-source adapters. Read Postgres directly for `as_of` queries. Only ALFRED vintages would still need a separate adapter (FRED ≠ ALFRED). |
| Historical prices for backtests | **No.** Yahoo-sourced, delisted coverage unknown. Keep Sharadar or Norgate. |
| Live prices | **Possible cheap option (Cloud Plus, $9.99).** Cheaper than Massive Starter ($29) with 15-min delay, but consolidated-vs-IEX, batch support and license terms must be confirmed first. |
| News / scheduled catalyst dates | Not covered. PDUFA dates are announced by companies, not FDA.gov (inference, unverified), so BPIQ is still needed. |

## Still to verify (needs unblocked network or the user's machine)

1. Run self-hosted Equibles, load a known restater, and confirm both the original and the
   restated rows are present with the correct `FiledDate`s.
2. Ask Equibles support or read the docs: are Cloud Plus prices consolidated (SIP)? Is
   there a multi-ticker snapshot? What are the license terms?
3. Measure disk and sync time for a 2000+ backfill.
