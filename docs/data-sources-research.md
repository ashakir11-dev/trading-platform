# Data Sources Research: Provider Comparison and Recommended Stack

*Researched 2026-09-25. Decision support only. Nothing here implies order placement.*

**How to read this.** Every vendor claim has a source tag like `[S12]`, and the tags
resolve in §5. The research environment could not open most vendor websites directly
(an egress proxy blocked massive.com, tiingo.com, sec.gov, eodhd.com, benzinga.com,
financialmodelingprep.com, sharadar.com and others). So most claims come from web-search
extracts of those vendors' own pages, plus GitHub, which was reachable. Where only a
third-party page (a review site, blog or aggregator) confirmed a claim, the claim is
tagged **(3rd-party)**. Where nothing confirmed a claim, it says **unverified**.
**Re-check prices on the vendor page before you buy.** Several of them changed during
2025 and 2026.

This follows `docs/ARCHITECTURE.md` §5: every category needs a **live** feed and a
**deep, point-in-time (PIT), survivorship-free historical** feed, behind the protocols in
`src/trading_pipeline/data/base.py` (`PriceDataProvider`, `QuoteProvider`,
`SectorDataProvider`, `NewsCatalystProvider`, `FundamentalsProvider`).

---

## 1. Executive summary

### Headline findings

1. **Massive.com is Polygon.io, renamed.** The rebrand took effect 2025-10-30. APIs,
   accounts and SDKs continue to work, and `api.massive.com` runs alongside the old domain
   [S1][S2]. It is a good **price** vendor: survivorship-free, delisted tickers kept, flat
   files on every paid plan, and an official MCP server [S3][S5][S7][S9]. It is a **poor
   PIT fundamentals** source. Its `filing_date` is the date of the *most recent* filing that
   contained a period's numbers, so restated values replace what was originally
   reported [S6]. Its indicators cover only SMA/EMA/MACD/RSI [S10]. No pivot endpoint was
   found.
2. **Robinhood is not needed.** Its official MCP (launched 2026-05-27) exists to let
   agents **place trades** [S40][S41]. That conflicts with this repo's hard rule against
   order-placing code. Community read-only servers use an unofficial API [S42]. The price
   vendor already covers quotes.
3. **Sector breadth should be derived, not bought.** Survivorship-free daily prices plus a
   SIC-based sector map give everything the scanner needs. Avoid GICS, which is licensed
   by MSCI and S&P and restricted to internal use [S50]. Sector SPDR ETFs cover live
   sector performance at no cost [S52].
4. **Indicators and pivots should be computed locally** from OHLCV with TA-Lib, which now
   ships prebuilt wheels [S54]. Do **not** adopt `pandas-ta`: it is flagged as inactive
   and facing archival [S55].
5. **The catalyst archive can be assembled from parts.** No single affordable vendor sells
   a PIT catalyst archive. The best affordable build combines: EDGAR 8-K with acceptance
   timestamps (free); Benzinga news from 2015 (free via Alpaca, or via Massive); Benzinga
   analyst actions from 2012; biotech catalysts from BPIQ (history from 2017); and openFDA
   for actual approval outcomes. Institutional PIT event data (Wall Street Horizon,
   RavenPack) exists but is priced on request.
6. **Sharadar is the best value for PIT fundamentals.** The personal-use Core US Equities
   Bundle is $69/mo or $499/yr for full history. It has as-reported rows keyed on filing
   date, delisted issuers, prices from 1998, insider trades (Form 4), 13F holdings, 8-K
   events and SIC-based sectors [S20][S21][S22][S23][S24].

### Recommended stacks

| Category / gap | **Tier A: free / near-free (~$0–30/mo)** | **Tier B: ~$100–300/mo** | **Tier C: "serious" (~$600–1,500+/mo, much by quote)** |
|---|---|---|---|
| Daily OHLCV, history, delisted | Massive Basic (free, EOD, 2 yrs, 5 calls/min) for dev [S3]; **Massive Starter $29** (5 yrs, flat files) if any budget [S3][S7] | **Sharadar SEP** (1998+, active + delisted) [S22] as the backtest source of truth; **Massive Starter $29** or Developer $79 for live data and intraday [S3] | Massive Advanced $199 (20+ yrs, real-time) [S3] + Sharadar (professional license if needed, price unverified) or Norgate Diamond (from 1950) [S30] |
| Corporate actions | Massive splits/dividends endpoints [S8] | Sharadar ACTIONS (splits, spinoffs, delist reasons, ticker changes) [S22] | Same, plus cross-check against Norgate [S30] |
| Indicators / pivots | **Local TA-Lib** [S54] | Local TA-Lib | Local TA-Lib |
| Sector classification | SEC EDGAR SIC codes (free) [S51] | Sharadar TICKERS (SIC-derived, approximates GICS) [S22] | Same; license GICS only if it is really needed [S50] |
| Sector perf / breadth (gap 1) | **Derived** from prices + SIC; sector SPDR ETFs for live [S52] | **Derived** from Sharadar SEP + TICKERS; ETFs for live | Derived; Norgate historical index constituents [S30] |
| Fundamentals, PIT (gap 3) | **SEC EDGAR companyfacts + Financial Statement Data Sets** (free; each fact carries `filed`/`accn`) [S11][S12][S13] | **Sharadar SF1 ARQ/ART dimensions keyed on `datekey`** [S20][S23] | Sharadar pro, plus Intrinio ($150/mo individual; as-reported from 2006) [S34] as a second source |
| Ownership (13F, Form 4) | EDGAR via `edgartools` (MIT, has MCP) [S15] | Sharadar SF2 (insiders, 2005+) and SF3 (13F, 2013+) [S24] | Same, plus sec-api.io ($49–239/mo) [S16] |
| Live news (gap 4) | **Alpaca News API** (Benzinga content, free, 200 calls/min) [S44] | Alpaca News, or **Massive + Benzinga News expansion (from $99)** [S4][S26] | Benzinga direct enterprise (quote) [S27] or RavenPack (quote) [S37] |
| Historical news archive (gap 2) | Alpaca News history **from 2015** [S44][S45] | Same, plus Benzinga via Massive | RavenPack (20+ yrs PIT analytics) [S37] |
| SEC 8-K / filings | EDGAR submissions (`acceptanceDateTime`, 8-K `items`) [S14] | Same, plus Sharadar EVENTS (8-K, since 1993) [S22] | Same, plus sec-api.io streaming [S16] |
| Earnings dates / results | EDGAR 8-K Item 2.02 acceptance time (actuals only) [S14] | **Massive + Benzinga Earnings expansion** (history + upcoming, estimates, surprises) [S4] | **Wall Street Horizon** (PIT earnings-date revisions, 2006+) [S36] |
| Analyst actions | none usable free (FMP free has grades endpoints, depth unverified) [S33] | **Massive + Benzinga Analyst Ratings ($99)**, history back to 2012 [S4][S25][S26] | Same, or Benzinga direct |
| FDA / PDUFA | openFDA Drugs@FDA (outcomes) [S46]; pdufa.bio free API (not PIT) [S48] | **BPIQ APEX ~$60/mo billed annually** (API + MCP, historical events from 2017) [S47] | BPIQ commercial / RTTNews feed (quote) [S49] |
| M&A | EDGAR 8-K (Items 1.01/2.01), news | Sharadar EVENTS + Benzinga news | + RavenPack / WSH |
| Macro | **FRED + ALFRED** (free, vintages) [S56] | FRED + ALFRED | FRED + ALFRED |
| Quotes / account (optional) | Price vendor's delayed quotes; Alpaca free IEX real-time [S43] | Massive Starter (15-min delayed) [S3] | Massive Advanced real-time [S3]; Schwab API read-only if you hold an account [S57] |
| **Est. monthly cost** | **$0**; **$29** with Massive Starter | **~$250**: Sharadar $69 (or ~$42 billed annually) + Massive Starter $29 + Benzinga Ratings $99 + BPIQ ~$60. Earnings expansion extra (price unverified, "from $99") | **~$700–900 before quotes**: Massive Advanced $199 + 3–4 Benzinga expansions (~$300–400) + Sharadar $69+ + BPIQ, **plus quoted** WSH / RavenPack / professional licenses |

**Tier B is the recommendation.** It closes every known gap except PIT *scheduled* event
dates (see §3.4). It stays within personal-use licenses. It needs only two data MCPs
(Massive, and optionally BPIQ) plus plain Python adapters for Sharadar, EDGAR, FRED and
Alpaca News.

---

## 2. Per-category comparison tables

Column meanings: *PIT* = point-in-time; *Delisted* = survivorship-free.

### 2.1 Price / volume (OHLCV), corporate actions

| Vendor | History depth | Delisted | Adjustments / corp. actions | Live latency | Access / MCP | Limits | Price (individual) | License notes | Reputation |
|---|---|---|---|---|---|---|---|---|---|
| **Massive** (ex-Polygon) | Basic 2 yrs, Starter 5, Developer 10, Advanced 20+ [S3]; tick data back to 2003 [S5] | Yes: delisted kept with full history; `active=false` [S5] | Split-adjusted; **not dividend-adjusted**; new endpoints add `historical_adjustment_factor`; corporate actions back to 2008 [S8] | Free: EOD; Starter/Developer: 15-min delayed; Advanced: real-time [S3] | REST, WebSocket, flat files (S3) on all paid plans [S7]; **official MCP**, "experimental", MIT [S9][S9b] | Free 5 calls/min; paid unlimited [S3] | $0 / $29 / $79 / $199 [S3] | Individual plans = personal, non-professional [S5] | Documented problems: ticker reuse (META), some bogus splits, flat files unadjusted and contain late prints (3rd-party) [S58] |
| **Sharadar SEP** (Nasdaq Data Link / sharadar.com) | From 1998 [S22] | Yes, 21,000+ active + delisted [S22] | Splits, dividends, spinoffs, acquisitions, delist reasons, ticker changes [S22] | EOD, updated 17:30 and 23:30 ET [S22] | REST / bulk table download (Nasdaq Data Link) [S20]; no official MCP found | unverified | Bundle $29/mo (5 yrs) or **$69/mo / $499/yr full** [S21] | Personal use = natural person, not on behalf of an entity; termination/retention wording is ambiguous (3rd-party reading) [S25b] | Well regarded for backtesting (3rd-party) [S23] |
| **Norgate Data** | Platinum ≥30 yrs; Diamond from 1950 [S30] | Yes (Platinum/Diamond only) [S30] | Yes | EOD | Python package (`norgatedata`); **not a hosted REST API**, Windows desktop updater [S31] | n/a | Platinum **US$360/12 mo** (6/12-month terms only) (3rd-party) [S31b] | unverified | Strong in the systematic-trading community (3rd-party) [S31c] |
| **Tiingo** | 30+ yrs EOD [S28] | Only for tickers "not yet recycled" [S29] | Yes (adjusted EOD) | IEX real-time | REST; MCP community only (e.g. major7apps) [S29b] | Free: 50 req/h, 1,000/day, 500 symbols/mo [S28] | Power $30/mo (individual), $50 commercial [S28] | Individual = non-commercial [S28] | Good (3rd-party) |
| **EODHD** | US from ~2000 (26k+ US tickers) [S32] | Yes, via `delisted=1` [S32] | Splits/dividends endpoints [S32] | EOD + delayed/real-time add-ons | REST; **official MCP** (v1 API key, v2 OAuth; 72 tools) [S32b] | 100k calls/day on paid plans [S32c] | EOD All-World $19.99; All-in-One $99.99 [S32c] | Personal vs commercial pricing pages exist [S32c]; terms unverified | Mixed/unverified |
| **FMP** | Free/Starter 5 yrs; Premium 30 yrs [S33] | Delisted-companies endpoint [S33] | Yes | Starter+ real-time US [S33] | REST; **official hosted MCP** at `financialmodelingprep.com/mcp` [S33b] | Free 250/day; Starter 300/min, Premium 750/min, Ultimate 3,000/min [S33c] | ~$19 / $49 / $99 per month *billed annually* (Ultimate reported as $149 monthly) (3rd-party) [S33c] | Personal plan: no commercial use, no display to third parties [S33d] | Mixed; broad coverage |
| **Alpaca** | 7+ yrs [S43] | unverified | Adjusted bars available | Free: real-time IEX (~2.5% of volume); SIP older than 15 min free; full SIP with Algo Trader Plus $99/mo [S43][S43b] | REST/WS; **official MCP includes order tools** [S43c] | 200 calls/min free [S44] | $0 / $99 [S43b] | Algo Trader Plus free only in the Elite program, personal use [S43b] | Good |

**Verdict:** For history, use **Sharadar SEP** as the survivorship-free source of truth. For
live data, flat-file intraday and MCP convenience, use **Massive**. Before trusting Massive
history, check for ticker reuse (key on `sid` or a CIK/FIGI mapping, not the ticker) and
cross-check split events against Sharadar ACTIONS [S58].

### 2.2 Technical indicators / pivots

| Option | Coverage | Notes |
|---|---|---|
| Massive indicator endpoints | SMA, EMA, MACD, RSI only [S10] | No pivot or support/resistance endpoint was found (**unverified that none exists**). Adds API calls and couples indicator math to a vendor. |
| **TA-Lib (local)** | 150+ indicators | Since 0.6.5, `pip install ta-lib` ships wheels that bundle the C library [S54]. Deterministic and reproducible in backtests. |
| pandas-ta | Many indicators | Flagged "Inactive". Maintainer warned it would be archived without funding by 2026-07-01 [S55]. Avoid. |

**Verdict:** Implement `indicators()` and `pivots()` locally. Classic floor pivots, fractal
swing highs/lows and volume-profile levels are a few dozen lines on top of `bars()`, and
local code is PIT by construction.

### 2.3 Sector classification and breadth

| Source | What | PIT? | License | Cost |
|---|---|---|---|---|
| GICS (MSCI / S&P) | 11 sectors / 163 sub-industries | Historical GICS needs a vendor feed | **Licensed.** Internal use only, no external distribution, no building indexes or analytics without a license [S50] | Quote |
| SEC EDGAR SIC | 4-digit SIC per registrant in submissions JSON [S51] | Current value only; history **unverified** (each filing header carries the SIC at filing time, **unverified** as an API) | Public | Free |
| **Sharadar TICKERS** | SIC, plus Sharadar sector/industry that "approximates GICS" [S22] | Current mapping (**PIT history unverified**) | Within the Sharadar license | In bundle |
| Norgate | Historical index constituents (S&P 500/400/600, Russell 1000/2000/3000, NDX, DJIA) [S30] | Yes, for index membership | Norgate license | Platinum+ |
| Select Sector SPDR ETFs | Nine sectors since 1998-12-16; XLRE 2015; XLC 2018 [S52] | Prices are PIT by nature | Just prices | Free with any price feed |
| Kenneth French 49 industry portfolios | SIC-based daily value-weighted returns, rebuilt each June [S53] | Built on CRSP; good independent benchmark | Free academic use | Free |

**Verdict: derive breadth.** See §3.3.

### 2.4 Company fundamentals, filings, ownership

| Vendor | Statements | PIT / as-reported | History | Ownership | Access / MCP | Price |
|---|---|---|---|---|---|---|
| **SEC EDGAR** (companyfacts, frames, submissions) | All XBRL-tagged facts | **Yes, when handled correctly.** Each fact has `filed`, `accn`, `fy`, `fp`, `frame`, and a restatement appears as another row with a later `filed` [S12] | XBRL from ~2009 [S13] | Form 4, 13F raw filings | REST; 10 req/s; declared User-Agent required; nightly bulk `companyfacts.zip` / `submissions.zip` (~3 a.m. ET) [S11] | Free |
| SEC Financial Statement Data Sets | Face financials from every XBRL filing | As filed (quarterly drops) | 2009-04-15 onward [S13] | – | Bulk TSV | Free |
| **edgartools** (library) | Parses XBRL, 10-K/Q, 8-K, Form 4, 13F | Inherits EDGAR | – | Yes | Python; includes an MCP server (`edgartools-mcp`) [S15] | Free (MIT) |
| **Sharadar SF1/SF2/SF3** | ~150 indicators and ratios, 14,000+ issuers incl. delisted [S24] | **Yes.** ARQ/ARY/ART are as-reported and keyed on `datekey` (the SEC filing date); MRQ/MRY/MRT include restatements and would leak look-ahead [S20][S23] | 1998+; insiders 2005+; 13F 2013+ [S24] | SF2, SF3 | Nasdaq Data Link API / bulk | In the $69 bundle [S21] |
| Massive financials (v1 statements) | Income statement, balance sheet, cash flow, ratios | **Not PIT.** `filing_date` is the most recent filing that included the period [S6] | unverified | – | REST / MCP | In stock plans (tier unverified) |
| FMP | Statements, ratios, 13F (Ultimate), transcripts [S33c] | As-reported endpoints exist; PIT behavior **unverified** | Up to 30 yrs (Premium) [S33] | 13F, insider | REST + official MCP [S33b] | $19–99+/mo [S33c] |
| Tiingo fundamentals | Statements, daily metrics | Offers both "as reported" and "most recent" [S29] | 15+ yrs premium, 5 yrs free [S29] | – | Add-on, contact sales [S28] | unverified |
| Intrinio | Standardized + as-reported from 2006 [S34] | Described as point-in-time [S34] | 2006+ | unverified | REST | Individual developer $150/mo [S34] |
| EODHD | Fundamentals incl. delisted [S32] | **unverified** | unverified | Some | REST + official MCP | In All-in-One $99.99 [S32c] |
| QuantConnect (Morningstar) | 8,000 US equities from 1998, "As Original Reported" [S38] | Yes | 1998+ | – | **Runs inside QuantConnect cloud; local export rights unverified** | QC subscription |
| sec-api.io | Filings, XBRL-to-JSON, Form 3/4/5, 13F, full-text search [S16] | Filing-based | Full EDGAR | Yes | REST + Python SDK | $49–239/mo [S16] |

**Verdict:** Use **Sharadar SF1 (AR dimensions only)** as the fundamentals backbone, with
**EDGAR companyfacts** as the free fallback and audit trail. In the adapter, make a
fundamentals row visible only from the first trading day *after* `datekey`/`filed`
[S23].

### 2.5 News and catalysts

| Source | Content | History | Timestamp fidelity | Access | Price | License |
|---|---|---|---|---|---|---|
| **Alpaca News API** | Benzinga news for stocks and crypto [S44][S45] | **From 2015** [S44] | Benzinga `created` / `updated` (see Benzinga row) | REST/WS; official Alpaca MCP has news tools (and order tools) [S43c] | **Free**, 200 calls/min [S44] | Storage/redistribution terms **unverified** |
| **Benzinga via Massive** | News, analyst ratings, analyst details, consensus, earnings, guidance [S4][S26] | Ratings back to 2012 [S25]; news/earnings depth **unverified** | `published_utc`; the v2 news API has real-time delivery [S4b] | REST + Massive MCP | **Each expansion from $99/mo**, individual [S4] | Personal (Massive individual terms) |
| Benzinga direct | Newsfeed, calendars (earnings, ratings, **FDA**, M&A...), sentiment [S27][S27b] | Deep archives on enterprise contracts [S27] | Has both `created` and `updated`; `updatedSince` for deltas [S27c] | REST; Benzinga has announced an MCP server [S27d] | No public price [S27] | Enterprise |
| Massive's own ticker news | Aggregated headlines, publisher, sentiment [S4c] | **unverified** | `published_utc` [S4c] | REST/MCP | In stock plans | Personal |
| Tiingo News | 70M+ articles | **3 months queryable** on individual plans; up to 15 yrs commercial, 1990s institutional [S29c] | **Best documented:** `publishedDate` vs `crawlDate`; a large gap means backfill [S29c] | REST | Add-on / sales | Commercial for depth |
| Alpha Vantage NEWS_SENTIMENT | News + sentiment | **Only from 2022-03-01** (3rd-party) [S35b] | unverified | REST; official MCP [S35] | $49.99–249.99/mo; free 25/day [S35] | Personal |
| Finnhub | Company news, upgrades/downgrades, earnings calendar, **FDA advisory committee calendar** [S36b] | unverified | unverified | REST | Modular: market data $49.99, fundamentals $50, estimates $75/mo [S36c] | Free tier non-commercial |
| EODHD News | News + daily sentiment [S32d] | unverified | unverified | REST/MCP | In paid plans [S32d] | – |
| GDELT | Global news metadata (no article text), every 15 min [S39] | 2015+ (GDELT 2.0) | Crawl-time based | Bulk/BigQuery | Free | Open |
| **RavenPack** | Entity-event analytics, sentiment, novelty | 20+ yrs, **PIT** [S37] | Designed as PIT | Feed / WRDS | Quote only [S37] | Institutional |
| **SEC EDGAR 8-K** | Material events; `items` field | Full EDGAR | **Acceptance timestamp**. `acceptanceDateTime` is Eastern time despite a `Z` suffix (3rd-party) [S14] | REST, free | Free | Public |
| Sharadar EVENTS | 8-K event codes | Since 1993 [S22] | Filing date | Bulk | Bundle | Personal |

**Earnings calendars and results**

| Source | Notes |
|---|---|
| EDGAR 8-K Item 2.02 | Free; gives actual release timestamps, never *expected* dates [S14] |
| Massive + Benzinga Earnings | Historical and upcoming, EPS/revenue actual vs estimate, surprise [S4] |
| Finnhub earnings calendar | EPS/revenue estimate and actual [S36b]; history depth **unverified** |
| **Wall Street Horizon** | **PIT DateBreaks** (every earnings-date revision, estimated vs confirmed); 10,000 companies, mostly archived from 2006 [S36] | Quote |

**Analyst actions:** Benzinga (2012+) through Massive for $99 [S25][S26]; FMP
grades / historical-grades endpoints [S33]; Finnhub upgrades/downgrades [S36b]. Only
Benzinga's history depth is documented.

**FDA / biotech catalysts**

| Source | What | History | PIT? | Access | Price | License |
|---|---|---|---|---|---|---|
| **openFDA Drugs@FDA** | Approval / submission history with `submission_status_date` [S46] | Decades | Outcomes are dated. **Scheduled** PDUFA dates are not included | REST, ~240 req/min, key optional [S46] | Free | Public |
| **BPIQ (BiopharmIQ)** | PDUFAs, readouts, AdComs, IPOs, pipelines; "5K+ historical events for back-testing", comprehensive from 2017 [S47] | 2017+ | Historical events available; revision history **unverified** | API + **MCP** included with APEX [S47] | **APEX $60/mo billed annually**; commercial by quote [S47] | Personal research; commercial/redistribution priced separately |
| pdufa.bio | PDUFA calendar, decision archive, free read API + `llms.txt` [S48] | Archive | **No.** Rebuilt daily and `as_of` = build date, so past dates may be corrected after the fact [S48] | Free REST | Free | As-is, no warranty [S48] |
| BioPharmCatalyst | PDUFA/FDA calendars; API by inquiry [S49b] | unverified | unverified | Inquiry | unverified | **Terms of use page exists but was not readable. Do not scrape.** [S49b] |
| Benzinga FDA calendar | PDUFA, AdCom, top-line results; historical and upcoming [S27b] | unverified | unverified | Benzinga API | Enterprise | – |
| RTTNews Biotech Investor | FDA and clinical-trial calendars; API/XML/RSS feeds [S49] | "20+ years covering the sector" [S49] | unverified | Custom | Quote [S49] | Custom |
| Finnhub FDA AdCom calendar | FDA advisory committee meetings [S36b] | unverified | – | REST | Finnhub tier | – |

### 2.6 Macro

| Source | Coverage | PIT | Limits | Price |
|---|---|---|---|---|
| **FRED** | Rates, CPI, FX, commodities, spreads (800k+ series) | Latest values only | 120 req/min with a free key [S56] | Free |
| **ALFRED** | FRED vintages; every observation has `realtime_start` / `realtime_end` [S56] | **Yes** | Same API (`vintage_dates`, `realtime_*`) | Free |
| Caveat | Third-party copyrighted series (e.g. S&P/Case-Shiller) need the owner's permission for anything beyond personal use [S56b] | | | |

Use ALFRED for any macro series that gets revised (CPI, payrolls, GDP). Market-priced
series (Treasury yields, FX) are not revised, so plain FRED is fine for those.

### 2.7 Live quotes / account visibility (read-only)

| Option | Quotes | Positions | Order capability | Verdict |
|---|---|---|---|---|
| **Robinhood official MCP** (`agent.robinhood.com/mcp/trading`, OAuth, since 2026-05-27) | Live quotes | Positions, balances, history | **Yes.** Trades inside a separate "Agentic" account; other accounts read-only [S40][S41] | **Do not connect.** It exposes order tools, which conflicts with the hard rule. |
| Robinhood community read-only MCPs | Quotes, positions, etc. | Yes | No (unofficial API, can break at any time) [S42] | Fragile; avoid |
| Alpaca | Real-time IEX free; SIP $99 [S43] | Yes | Official MCP includes orders [S43c] | Use REST data endpoints through our own adapter, never their MCP |
| Schwab Trader API | Real-time + history | Yes | API supports trading | Free for account holders after app approval [S57]; only if the user already banks there |
| Tradier | Real-time for account holders; sandbox 15-min delayed [S57b] | Yes | Yes | Only with an account |
| IBKR | Paid subscriptions; 15-min delayed free [S57c] | Yes | Yes | Overkill |
| **Price vendor quotes** (Massive) | 15-min delayed on Starter/Developer, real-time on Advanced [S3] | – | None | **Recommended.** A swing horizon doesn't need real-time. |

### 2.8 Backtest-ready bulk data and local storage

| Source | Bulk form | Local storage allowed? |
|---|---|---|
| Massive | Flat files (S3) on all paid plans: day/minute aggregates, trades, quotes [S7] | Downloading is the intended use [S7]. Personal/non-professional only [S5] |
| Sharadar | Full table exports via Nasdaq Data Link [S20] | Personal license covers a private research database; **post-termination retention is ambiguous** (3rd-party reading of terms) [S25b] |
| SEC EDGAR | Nightly `companyfacts.zip`, `submissions.zip`; quarterly FSDS [S11][S13] | Yes (public data) |
| FRED/ALFRED | API | Yes, except copyrighted third-party series [S56b] |
| Norgate | Local database by design [S31] | Yes, while subscribed (details unverified) |
| Alpaca News, Benzinga-via-Massive, BPIQ | API only | **unverified.** Read each ToS before caching years of news locally |
| QuantConnect datasets | Cloud; some in LEAN format [S38] | On-premise export rights **unverified** |

### 2.9 MCP servers

| Vendor | Server | Official? | Maturity | Order tools? |
|---|---|---|---|---|
| Massive | `massive-com/mcp_massive`; rebuilt into 4 composable tools (`search_endpoints`, `call_api`, `query_data`, …) with an in-memory SQLite layer [S9][S9b] | Yes | **"Experimental… subject to breaking changes"**, MIT [S9] | No (data only) |
| FMP | Hosted `financialmodelingprep.com/mcp?apikey=…` [S33b] | Yes | Hosted; details unverified | No |
| EODHD | `EodHistoricalData/EODHD-MCP-Server` (v1 key, v2 OAuth), 72 tools [S32b] | Yes | Active | No |
| Alpha Vantage | Official MCP [S35] | Yes | unverified | No |
| BPIQ | API + MCP with APEX [S47] | Yes | unverified | No |
| Benzinga | "Our MCP Server is LIVE" [S27d] | Yes | unverified | No |
| edgartools | `edgartools-mcp` (uvx) [S15] | Yes (library author) | Library is mature | No |
| Alpaca | `alpacahq/alpaca-mcp-server` v2 [S43c] | Yes | Active | **Yes. Do not use.** |
| Robinhood | Trading MCP [S40][S41] | Yes | New (2026) | **Yes. Do not use.** |
| Tiingo | `major7apps/tiingo-mcp`, `tiingo-mcp` (PyPI) [S29b] | **Community** | – | No |
| Sharadar, FRED, openFDA | none official found | – | – | – |

**Architecture note:** MCP is convenient for ad-hoc agent exploration, but backtests need
deterministic, cacheable, `as_of`-filtered calls. Put the **REST/bulk adapters behind
`data/base.py` protocols** as the source of truth, and use MCP only for live runs, if at
all. Middleware fetches the data, not agents (§3 of ARCHITECTURE.md), so agents don't
need vendor MCPs.

---

## 3. Specific answers

### 3.1 Should we keep Massive?

**Yes, but narrow its role.** Keep it for: live and delayed prices and snapshots; minute
bars and flat files; the optional Benzinga expansions (analyst ratings, earnings, news);
and quick MCP exploration. The $29 Starter plan is enough for swing horizons (5 years,
15-min delayed, unlimited calls, flat files) [S3][S7].

**Do not use it for:**
- **PIT fundamentals.** `filing_date` reflects the latest filing, so restatements leak
  into history [S6].
- **Pivots.** No endpoint was found. Indicators should be computed locally anyway [S10].
- **Being the only source of historical truth.** Ticker reuse and questionable splits have
  been documented (3rd-party) [S58]. Key series by Massive's `sid`, or by CIK/FIGI, and
  cross-check splits against Sharadar ACTIONS.

Starter's 5 years is too short for a multi-regime backtest. Sharadar (from 1998) covers
the deep history more cheaply than Massive Advanced.

### 3.2 Do we need Robinhood at all?

**No.** The only thing Robinhood uniquely provides is the user's own positions. The
official MCP is built around trade placement [S40][S41], and the read-only alternatives use
an unofficial, unstable API [S42]. The price vendor already covers quotes. If position
visibility is wanted later, the safest route is a **manual CSV/JSON positions import** into
the `QuoteProvider.positions()` adapter. Next safest is the read endpoints of a broker's
REST API called by our own adapter, with no order methods, which the repo rules already
require.

### 3.3 Can sector breadth be derived instead of bought?

**Yes, and deriving is better than buying,** because we control PIT and survivorship.
Recipe:

1. **Universe on date *t*:** every common stock with a price bar on *t* in Sharadar SEP
   (or Massive flat files), delisted names included [S22][S5]. Optionally filter by
   liquidity (dollar volume) and price.
2. **Sector map:** SIC from Sharadar TICKERS or EDGAR, mapped to ~11 GICS-like buckets
   (Sharadar's own sector field already approximates GICS) [S22][S51]. This avoids GICS
   licensing [S50].
3. **Metrics per sector on *t*:** % of names above their 50/200-day moving average;
   advance/decline counts; new 52-week highs minus lows; equal- and cap-weighted returns
   over 1/5/20/60 days; up-volume ratio; dispersion; relative strength against SPY. All
   come from `bars()`.
4. **Live:** the same computation on the latest bars, plus sector SPDR ETFs (XLK, XLF, …;
   XLRE from 2015, XLC from 2018) as a quick cross-check [S52].
5. **Validation:** compare derived sector returns with the Kenneth French 49-industry
   daily portfolios (CRSP-based and survivorship-free) over overlapping dates [S53].

**Residual limits:**
- SIC codes are current, not historical (PIT SIC history is unverified), so a company that
  changed business carries its current sector backwards. The impact is small but real.
  Don't trust GICS-like buckets across the 2018 Communication Services reshuffle.
- Sharadar prices start in 1998, which is ample.

### 3.4 What is the best achievable historical catalyst archive, and what honest-backtest limits remain?

**Best affordable archive (Tier B):**

| Catalyst type | Source | "Known-at" timestamp |
|---|---|---|
| Company news | Benzinga via Alpaca (2015+) [S44], or via Massive [S4] | `created`. Treat `updated` as a revision and never use it as the knowledge time [S27c] |
| Material events, M&A, guidance, exec changes | EDGAR 8-K `items` + `acceptanceDateTime` [S14]; Sharadar EVENTS [S22] | EDGAR acceptance time (convert from ET correctly) |
| Earnings **results** | 8-K Item 2.02 acceptance [S14]; Benzinga Earnings (actuals, estimates, surprise) [S4] | Acceptance time / Benzinga timestamp |
| Earnings **scheduled dates** | Benzinga Earnings (upcoming) [S4] | **Not PIT.** Only WSH DateBreaks stores revision history [S36] |
| Analyst actions | Benzinga Analyst Ratings, 2012+ [S25][S26] | Action date/time |
| FDA outcomes | openFDA Drugs@FDA [S46] | `submission_status_date` (a date, not a time) |
| FDA scheduled PDUFA / AdCom / readouts | BPIQ historical events 2017+ [S47]; pdufa.bio archive [S48] | **Mostly not PIT.** Archives are corrected in place (pdufa.bio rebuilds daily) [S48] |
| Insider / institutional flows | Sharadar SF2/SF3 [S24]; EDGAR Form 4 / 13F | Filing date (13F reports 45 days after quarter end) |

**Honest-backtest limits that remain:**

1. **Scheduled-event look-ahead.** For past dates, we mostly know the *final* PDUFA or
   earnings date, not the date that was expected at the time. Mitigation: only WSH
   (earnings) sells revision history [S36]. For FDA events, record our own snapshots going
   forward, and in backtests treat scheduled dates as known only once a dated press release
   or 8-K announcing them exists.
2. **News backfill and revisions.** Vendors add sources later and backfill them. Tiingo
   documents this explicitly (`crawlDate` ≫ `publishedDate` means backfill) [S29c].
   Benzinga has `updated` [S27c]. Without an ingestion timestamp, a headline dated 09:30
   may have been unavailable until much later. Mitigation: lag every news item by a
   conservative delay (e.g. use the next session), and prefer EDGAR acceptance times
   for material events.
3. **Coverage drift.** News volume and analyst coverage in 2015 differ from 2026. The
   scanner's hit-rate will look different for reasons that have nothing to do with
   reasoning quality.
4. **LLM training-data leakage (the biggest limit).** The agents are LLMs whose training
   data runs to their knowledge cutoff (this model's is 2026-06). In a backtest dated
   2019, the model may already "know" that a drug was approved or a company was acquired.
   PIT data cannot fix this. Mitigations:
   - Treat only dates after the model's cutoff as a true out-of-sample test, and set
     `PipelineConfig.holdout_start` after the cutoff of every model used.
   - Anonymize tickers and company names in backtest prompts where feasible.
   - Record which model version produced each backtest.
5. **Price data depth vs catalyst depth.** Prices go back to 1998, but catalysts only
   reach 2012 (ratings), 2015 (news) or 2017 (biotech). Honest catalyst backtests are
   limited to roughly 2015 onward.

---

## 4. Risks and caveats

**Licensing**
- Almost every affordable plan here is **personal / non-professional**: Massive individual
  [S5], FMP [S33d], Tiingo Power [S28], Sharadar personal [S25b], Alpaca Algo Trader Plus
  [S43b], BPIQ APEX [S47]. Sharing outputs with other people, running this for a fund or
  employer, or turning it into a product requires business licenses, often at several
  times the price.
- **GICS** needs an MSCI/S&P license and is internal-use only [S50]. Use SIC-derived
  sectors instead.
- **Local caching of news and catalyst archives** (Alpaca/Benzinga, BPIQ) has unverified
  terms. Read the ToS before building a multi-year local archive.
- Sharadar's retention language after cancellation is ambiguous (3rd-party) [S25b].
  Assume stored data must be deleted when the subscription ends unless the vendor
  confirms otherwise in writing.
- Do not scrape BioPharmCatalyst or other calendar websites.

**Survivorship bias**
- Use only survivorship-free sources for universes (Sharadar SEP, Massive with
  `active=false`, Norgate Platinum+). Tiingo keeps delisted data only for tickers that
  haven't been recycled [S29]. Free tiers of most vendors are *not* reliable for this.
- **Ticker ≠ company.** Ticker reuse (META) breaks naive joins [S58]. Key everything on
  a permanent ID (Sharadar `permaticker`, Massive `sid`, SEC CIK).

**Look-ahead**
- **Restated fundamentals:**
  - Never use Sharadar MR* dimensions [S23].
  - Never use Massive's `filing_date` as a knowledge date [S6].
  - With EDGAR, choose the fact row with the earliest `filed` date on or before `as_of`
    [S12].
  - Make data visible from the next trading day after filing.
- **Late-ingested or revised news:** see §3.4 items 1 and 2. Store both the vendor
  timestamp and our own `fetched_at` (`DataSnapshot` already has `fetched_at`). For live
  runs, our `fetched_at` becomes the honest PIT record from here on. **Start archiving
  live data now:** our own snapshots are the only fully PIT catalyst archive we'll ever
  have.
- **Timezone traps:** EDGAR `acceptanceDateTime` is ET with a misleading `Z` suffix
  (3rd-party report) [S14]. openFDA and some calendars give dates without times, so
  assume end of day.
- **Macro revisions:** use ALFRED vintages, not FRED latest [S56].
- **Adjusted prices:** split/dividend adjustment factors are computed with future events.
  Keep indicators consistent, and compute returns from unadjusted prices plus corporate
  actions if exact PIT prices matter. Massive does not adjust for dividends [S8].

**Vendor and operational risk**
- Massive's MCP is explicitly "experimental" [S9]. The Massive (ex-Polygon) financials
  endpoint was replaced in 2025–26 (the experimental endpoint was sunset 2026-06-22) [S6].
  Expect API churn and pin adapter versions.
- Price and plan changes are frequent: Tiingo announced new Power plans [S28]; FMP's
  monthly vs annual prices differ by source [S33c]. Re-verify before purchase.
- Several items here rest on third-party pages or remain unverified (see tags).
  Specifically:
  - Massive news history depth
  - Benzinga Earnings expansion price and depth
  - BPIQ revision history
  - Alpaca news storage terms
  - Norgate's exact price
  - EODHD news depth
  - whether a Massive pivot endpoint exists

---

## 5. Sources

- [S1] Massive blog, "Polygon.io is Now Massive": https://massive.com/blog/polygon-is-now-massive
- [S2] Press release (EIN Presswire), rebrand 2025-10-30, api.massive.com parallel: https://www.einpresswire.com/article/863823068/polygon-io-is-now-massive ; FISD: https://fisd.net/polygon-io-is-now-massive/
- [S3] Massive pricing (Basic free / Starter $29 / Developer $79 / Advanced $199; history 2/5/10/20+ yrs; EOD / 15-min delayed / real-time; free 5 calls/min): https://massive.com/pricing ; https://massive.com/stocks
- [S4] Massive, "Benzinga Data Now Available on Massive.com" (expansions from $99/mo individual): https://massive.com/blog/benzingadata-partnership ; https://massive.com/partners/benzinga
- [S4b] Massive Benzinga News endpoint: https://massive.com/docs/rest/partners/benzinga/news
- [S4c] Massive ticker news endpoint (`published_utc`, publisher, sentiment): https://massive.com/docs/rest/stocks/news
- [S5] Massive KB, delisted tickers; individual plans personal/non-professional: https://massive.com/knowledge-base/article/what-does-massive-do-with-delisted-tickers ; https://massive.com/stocks
- [S6] Massive KB, filing date of financial reports (most recent filing): https://massive.com/knowledge-base/article/does-massive-provide-the-filing-date-for-any-financial-reports ; changelog (financials sunset): https://massive.com/changelog ; https://massive.com/docs/rest/stocks/fundamentals/income-statements
- [S7] Massive flat files on all paid plans: https://massive.com/blog/flat-files ; https://massive.com/docs/flat-files/stocks/day-aggregates
- [S8] Massive adjustments / splits and dividends endpoints: https://massive.com/knowledge-base/article/is-massives-stock-data-adjusted-for-splits-or-dividends ; https://massive.com/blog/new-splits-and-dividends-endpoints
- [S9] Massive official MCP server (experimental, MIT): https://github.com/massive-com/mcp_massive
- [S9b] Massive, rebuilt MCP server: https://massive.com/blog/massive-rebuilds-mcp-server
- [S10] Massive technical indicators (SMA/EMA/MACD/RSI): https://massive.com/blog/new-technical-indicators-apis ; https://massive.com/knowledge-base/article/does-massive-offer-any-technical-indicators
- [S11] SEC EDGAR APIs, rate limit, bulk ZIPs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces ; https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- [S12] companyfacts fields `filed`/`accn`/`fy`/`fp`/`frame`, and restatements as extra rows (3rd-party explainer): https://tldrfiling.com/blog/sec-edgar-api-guide/ ; https://dealcharts.org/blog/sec-edgar-api-guide
- [S13] SEC Financial Statement Data Sets (from 2009-04-15, quarterly): https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets
- [S14] EDGAR `acceptanceDateTime` handling (ET vs `Z`), 8-K items (3rd-party code reviews): https://github.com/chriskskinvestors/bank-valuation-dashboard/pull/104 ; https://github.com/Southpaw3234/Quant-Terminal/pull/61
- [S15] edgartools (MIT, MCP server): https://github.com/dgunning/edgartools ; https://pypi.org/project/edgartools/
- [S16] sec-api.io pricing and APIs: https://sec-api.io/pricing ; https://sec-api.io/docs/insider-ownership-trading-api ; comparison: https://www.edgar.tools/vs/sec-api
- [S20] Nasdaq Data Link, Sharadar Core US Equities Bundle (PIT-ready, delisted): https://data.nasdaq.com/databases/SFA
- [S21] Sharadar subscribe / pricing ($29 5-yr; $69/mo or $499/yr full history): https://sharadar.com/subscribe ; https://sharadar.com/
- [S22] Sharadar SEP (21k+ active and delisted, from 1998, update times), TICKERS SIC/sector, ACTIONS, EVENTS 8-K since 1993: https://data.nasdaq.com/databases/SEP ; https://www.quantrocket.com/sharadar/
- [S23] Sharadar dimensions (AR vs MR) and `datekey` usage (3rd-party): https://github.com/rtrimble13/fafnir/issues/83 ; https://github.com/quantrocket-llc/quantrocket-client/blob/master/quantrocket/fundamental.py ; https://pickuma.com/for-dev/financial-modeling-prep-vs-sharadar-fundamental-data-api/
- [S24] Sharadar SF1/SF2/SF3 coverage (1998; insiders 2005; 13F 2013): https://data.nasdaq.com/databases/SF3 ; https://data.nasdaq.com/databases/SF2 ; https://sharadar.com/fundamentals
- [S25] Benzinga analyst ratings history back to 2012: https://www.benzinga.com/apis/cloud-product/analyst-ratings-api/
- [S25b] Sharadar license terms (personal use, retention wording; 3rd-party reading): https://www.quantrocket.com/terms/sharadar/ ; https://github.com/rtrimble13/fafnir/issues/43
- [S26] Massive Benzinga analyst ratings / earnings endpoints: https://massive.com/docs/rest/partners/benzinga/analyst-ratings ; https://massive.com/docs/rest/partners/benzinga/earnings
- [S27] Benzinga APIs product suite, no public pricing: https://www.benzinga.com/apis/data/ ; https://datarade.ai/data-providers/benzinga/profile
- [S27b] Benzinga FDA calendar API: https://docs.benzinga.com/api-reference/calendar-api/get-fda ; https://www.benzinga.com/fda-calendar
- [S27c] Benzinga news `created`/`updated`, `updatedSince`: https://docs.benzinga.com/llms.txt ; https://www.benzinga.com/apis/blog/mastering-the-benzinga-newsfeed-api/
- [S27d] Benzinga, "Our MCP Server is LIVE": https://www.benzinga.com/apis/blog/our-mcp-server-is-live/
- [S28] Tiingo pricing (free limits; Power $30 individual / $50 commercial; fundamentals add-on; new Power plans): https://www.tiingo.com/about/pricing ; https://www.findmymoat.com/tools/tiingo
- [S29] Tiingo fundamentals (as-reported and most-recent; delisted; permaTicker) and symbology (delisted if not recycled): https://www.tiingo.com/documentation/fundamentals ; https://www.tiingo.com/documentation/appendix/symbology
- [S29b] Tiingo MCP (community): https://github.com/major7apps/tiingo-mcp ; https://pypi.org/project/tiingo-mcp/
- [S29c] Tiingo News docs (`crawlDate` vs `publishedDate`; 3-month history; commercial up to 15 yrs): https://www.tiingo.com/documentation/news ; https://www.tiingo.com/products/news-api
- [S30] Norgate packages (Platinum/Diamond, delisted, historical index constituents): https://norgatedata.com/data-package-faq.php ; https://norgatedata.com/data-content-tables.php
- [S31] Norgate is not a hosted REST API; Python package: https://github.com/api-evangelist/norgate-data ; https://pypi.org/project/norgatedata/
- [S31b] Norgate stock market package pricing: https://norgatedata.com/stockmarketpackages.php
- [S31c] Norgate review (3rd-party): https://alvarezquanttrading.com/blog/norgate-data-review/
- [S32] EODHD delisted data and coverage: https://eodhd.com/financial-apis/delisted-stock-companies-data-2 ; https://eodhd.com/financial-academy/financial-faq/historical-stock-prices-for-delisted-companies
- [S32b] EODHD official MCP: https://github.com/EodHistoricalData/EODHD-MCP-Server ; https://eodhd.com/financial-apis/mcp-server-for-financial-data-by-eodhd
- [S32c] EODHD pricing: https://eodhd.com/pricing ; https://eodhd.com/commercial-pricing
- [S32d] EODHD news API: https://eodhd.com/financial-apis/stock-market-financial-news-api
- [S33] FMP plan history depth, delisted companies, grades: https://site.financialmodelingprep.com/insights/platform/how-to-choose-the-right-financial-modeling-prep-plan-for-your-workflow ; https://site.financialmodelingprep.com/developer/docs/stable/delisted-companies ; https://site.financialmodelingprep.com/developer/docs/upgrades-and-downgrades-api
- [S33b] FMP hosted MCP: https://site.financialmodelingprep.com/developer/docs/mcp-server
- [S33c] FMP pricing (official plus 3rd-party summaries): https://site.financialmodelingprep.com/pricing-plans ; https://www.trustradius.com/products/financial-modeling-prep/pricing ; https://www.findmymoat.com/tools/financial-modeling-prep-fmp
- [S33d] FMP terms of service (personal-use restrictions): https://site.financialmodelingprep.com/terms-of-service ; https://site.financialmodelingprep.com/insights/platform/can-you-use-fmp-data-in-a-public-app-website-or-client-dashboard
- [S34] Intrinio ($150/mo individual; as-reported from 2006): https://intrinio.com/blog/a-new-intrinio-for-the-ai-era ; https://intrinio.com/pricing
- [S35] Alpha Vantage premium pricing and MCP: https://www.alphavantage.co/premium/ ; https://www.alphavantage.co/
- [S35b] Alpha Vantage news from 2022-03-01 (3rd-party research use): https://openreview.net/pdf?id=FL1VmOgiO8
- [S36] Wall Street Horizon historical data / DateBreaks: https://www.wallstreethorizon.com/historical-data ; https://www.tmxwebstore.com/products/wsh-datebreaks
- [S36b] Finnhub FDA AdCom calendar, earnings calendar: https://finnhub.io/docs/api/fda-committee-meeting-calendar ; https://finnhub.io/docs/api/earnings-calendar
- [S36c] Finnhub pricing: https://finnhub.io/pricing
- [S37] RavenPack news analytics: https://www.ravenpack.com/products/edge/data/news-analytics ; https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/ravenpack/
- [S38] QuantConnect Morningstar fundamentals and Benzinga news datasets: https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/morningstar/us-fundamental-data ; https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/benzinga/benzinga-news-feed
- [S39] GDELT: https://en.wikipedia.org/wiki/GDELT_Project ; https://blog.gdeltproject.org/gdelt-3-0-and-using-bigquery-and-streaming-google-cloud-storage-for-logging/
- [S40] Robinhood newsroom, "Robinhood is Now Open to Agents": https://robinhood.com/us/en/newsroom/robinhood-is-now-open-to-agents/ ; https://robinhood.com/us/en/support/articles/agentic-trading-overview/
- [S41] TechCrunch, 2026-05-27: https://techcrunch.com/2026/05/27/robinhood-now-lets-your-ai-agents-trade-stocks/ ; setup/scope (3rd-party): https://skiln.co/blog/robinhood-mcp-server-guide-2026
- [S42] Community read-only Robinhood MCPs: https://github.com/verygoodplugins/robinhood-mcp ; https://github.com/nischalsrinivas/robinhood-readonly-mcp
- [S43] Alpaca market data FAQ (IEX vs SIP; 15-min rule): https://docs.alpaca.markets/us/docs/market-data-faq ; https://alpaca.markets/data
- [S43b] Alpaca Elite (Algo Trader Plus $99/mo, personal use): https://alpaca.markets/elite
- [S43c] Alpaca official MCP (includes orders): https://github.com/alpacahq/alpaca-mcp-server
- [S44] Alpaca News API (free; 200/min; 2015+): https://alpaca.markets/blog/introducing-news-api-for-real-time-fiancial-news/
- [S45] Alpaca historical news docs (Benzinga source): https://docs.alpaca.markets/us/docs/historical-news-data
- [S46] openFDA (Drugs@FDA, rate limits): https://open.fda.gov/apis/drug/event/how-to-use-the-endpoint/ ; https://github.com/fda/openfda
- [S47] BPIQ API / pricing (APEX $60/mo annual, API+MCP; history from 2017; 5K+ events): https://www.bpiq.com/bpiq-api ; https://www.bpiq.com/pricing ; https://www.bpiq.com/apex ; https://x.com/BiopharmIQ/status/2045962722072990178
- [S48] pdufa.bio developers / pricing / sources: https://www.pdufa.bio/developers ; https://www.pdufa.bio/pricing ; https://www.pdufa.bio/sources
- [S49] RTTNews Biotech FDA calendar feeds: https://www.rttnews.com/products/biotechfdacalendar.aspx
- [S49b] BioPharmCatalyst terms / API inquiries: https://www.biopharmcatalyst.com/terms-of-use ; https://www.biopharmcatalyst.com/info/api-inquiries
- [S50] GICS licensing (MSCI/S&P; internal use only): https://www.msci.com/indexes/index-resources/gics ; https://www.msci.com/documents/1296102/33489517/Analytics+Online+Services+Supplement+-+as+of+April+15+2025.pdf
- [S51] SEC company tickers / SIC in submissions: https://www.sec.gov/search-filings/edgar-application-programming-interfaces ; https://github.com/danielsobrado/edgar-cik-cusip-ticker-sector-service
- [S52] Select Sector SPDR history: https://www.etfaction.com/the-ultimate-trading-tools-an-etf-story-about-the-select-sector-spdrs/ ; https://stockanalysis.com/etf/xlk/
- [S53] Kenneth French 49 industry portfolios: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_49_ind_port.html
- [S54] TA-Lib Python (wheels since 0.6.5): https://pypi.org/project/TA-Lib/ ; https://ta-lib.github.io/ta-lib-python/install.html
- [S55] pandas-ta maintenance / archival warning: https://www.pandas-ta.dev/ ; https://snyk.io/advisor/python/pandas-ta
- [S56] FRED API and ALFRED vintages (120 req/min; `realtime_start`/`realtime_end`): https://fred.stlouisfed.org/docs/api/fred/ ; https://alfred.stlouisfed.org/help/downloaddata ; https://www.stlouisfed.org/open-vault/2021/august/using-the-alfred-database
- [S56b] FRED terms (copyrighted third-party series): https://fred.stlouisfed.org/docs/api/terms_of_use.html ; https://fred.stlouisfed.org/legal
- [S57] Schwab developer portal: https://developer.schwab.com/products
- [S57b] Tradier market data: https://docs.tradier.com/docs/market-data
- [S57c] IBKR market data subscriptions: https://www.interactivebrokers.com/docs/general/market-data-subscriptions/introduction
- [S58] "Massive Problems" Parts 1–3 (ticker reuse, bogus splits, late prints; 3rd-party): https://stonkscapital.substack.com/p/massive-problems-part-1 ; https://stonkscapital.substack.com/p/massive-problems-part-2 ; https://stonkscapital.substack.com/p/massive-problems-part-3
