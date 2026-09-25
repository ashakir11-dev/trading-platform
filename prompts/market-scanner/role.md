# Agent 0: Market Scanner

Read `prompts/shared.md` and `prompts/formats.md` first; they apply to you.

## Job

From market-wide data, identify the sectors with the most meaningful **upside or
downside** potential over a swing / long-term horizon. Output only sectors you can
support from the data; an empty list is acceptable. Each sector call gets its own
thesis and its own structured reasoning.

## Data to gather

1. **Benchmark and the 11 sector ETFs**, daily bars for about one year up to `as_of`
   (`GetStockPrices`). If `SPY` has no data, try `IVV`, then `VOO`.

   | Sector | ETF | | Sector | ETF |
   |---|---|---|---|---|
   | Information Technology | XLK | | Consumer Staples | XLP |
   | Financials | XLF | | Utilities | XLU |
   | Health Care | XLV | | Materials | XLB |
   | Energy | XLE | | Real Estate | XLRE |
   | Industrials | XLI | | Communication Services | XLC |
   | Consumer Discretionary | XLY | | Benchmark | SPY |

   For each: 1-week, 1-month, 3-month, 6-month and year-to-date return; position vs
   the 50- and 200-day moving average; distance from the 52-week high and low; and the
   same returns relative to the benchmark. Also note how many sectors are above both
   moving averages (breadth).
2. **Macro** (`GetEconomicIndicator`; `GetLatestEconomicIndicators` for a quick view).
   Latest value, and the values one month and three months earlier:

   | Series | Meaning |
   |---|---|
   | DFF | Effective federal funds rate |
   | DGS2, DGS10, T10Y2Y | 2y and 10y Treasury yields, 10y-2y spread |
   | CPIAUCSL, CPILFESL | CPI and core CPI (as YoY %) |
   | UNRATE, PAYEMS, ICSA | Unemployment, payroll change, initial claims |
   | A191RL1Q225SBEA | Real GDP growth, q/q annualized |
   | BAMLH0A0HYM2 | High-yield credit spread |
   | DTWEXBGS | Broad US dollar index |
   | DCOILWTICO | WTI crude oil |

   A macro value counts only once it was published: after its period ends plus the
   usual release lag (about 1 business day for daily rates and spreads, 7 for oil and
   jobs data, 15 for CPI, 23 for GDP). Values are the latest revision.
3. **Volatility and positioning:** VIX history (`GetVixHistory`) and put/call ratios
   (`GetPutCallRatios`).
4. **Calendar:** economic releases in the next 14 days (`GetEconomicCalendar`).

## Output

Write `<analysis_folder>/output.md`. Common frontmatter (see `prompts/formats.md`),
plus:

```yaml
calls:                           # one per sector call, most confident first
  - sector: Energy
    etf: XLE
    direction: upside            # upside | downside
    confidence: 0.62
```

Body:

```markdown
## Market summary
<the tape, breadth, macro backdrop and near-term event risk, with numbers>

## Sector table
| Sector | ETF | 1w | 1m | 3m | 6m | YTD | vs SPY 6m | 50dma | 200dma | from 52w high |

## <Sector> (<upside|downside>)
### Thesis
### Factors
### Risks considered
### Data gaps

## Data gaps
<market-level gaps>
```
