# Live US Equity Prices: Alternatives and Recommendation

*Researched 2026-09-25. Decision support only. Nothing here implies order placement.*

This builds on `docs/data-sources-research.md` §2.1 and §2.7. That document recommends
**Massive Starter $29/mo** (15-min delayed) for live prices, with Massive Advanced $199 for
real time. This document compares alternatives for the `QuoteProvider` role, plus
"today's bar" for `PriceDataProvider` (`src/trading_pipeline/data/base.py`).

**How to read this.** Every vendor claim carries a source tag `[Lnn]`, and the tags resolve
in §6. The egress proxy blocked **every** vendor website (massive.com, alpaca.markets,
tiingo.com, finnhub.io, databento.com, twelvedata.com, eodhd.com, FMP, IBKR, Schwab,
Tradier, tastytrade, Intrinio, Marketstack, Barchart). Only GitHub and PyPI were reachable.
So most claims come from **web-search extracts of the vendor's own pages**, cited to those
URLs. Claims that only a third-party page supports are tagged **(3rd-party)**. Claims that
could not be confirmed are tagged **unverified**. GitHub READMEs were read directly.
**Re-check prices and limits on the vendor page before you subscribe.**

---

## 1. Recommendation

### 1.1 What "good enough" means here

- **Horizon:** swing and long-term trades only. The system never places orders.
- **Workload:** a price shown next to each recommendation; tripwires on about 100 open
  tickers a few times a day; a refreshed "today" bar for the technical agent; and one
  whole-market pass (about 5,000 tickers) per day.
- **Accuracy matters more than latency.** For a stop check, a **consolidated (SIP)** price
  15 minutes old beats a real-time price from **one exchange**. A single-venue feed like
  IEX (about 2–5% of US volume [L4][L21]) can miss the day's true high and low, and its last
  trade can be minutes stale on thinly traded names. So a stop that was breached on another
  venue may not show at all.

### 1.2 The picks

| Tier | Pick | Cost | Why |
|---|---|---|---|
| **Free** | **Alpaca Basic** (Market Data API, REST only, through our own adapter) | $0 | Multi-symbol snapshots and bars in one call; 200 req/min [L2]. **SIP (consolidated) bars are free once they are ≥15 min old** [L1][L3], so tripwires and the daily whole-market pass can run on consolidated data. The real-time IEX price is fine for *display* if it is labeled "IEX". Bars come raw, split-adjusted, dividend-adjusted or fully adjusted (`adjustment=` parameter [L5]), so live and historical use one convention. |
| **Cheap (≤ ~$50)** | **Massive Starter $29** (the current plan, kept) | $29/mo | Consolidated data for the whole market, 15-min delayed; unlimited calls; **one-call full-market snapshot** (all ~5,000 tickers) [L6][L7]; the same vendor as the historical bars (split-adjusted by default [L8]); official MCP with **no order tools** [L9]. It beats Alpaca Basic on convenience (whole-market snapshot, flat files, 5 years of history), not on accuracy. Runner-up: **Tiingo Power $30**, strong adjusted EOD data but IEX-only intraday [L12][L13][L14]. |
| **Best-value real-time** | **Alpaca Algo Trader Plus $99/mo** | $99/mo | Real-time **full SIP**, 10,000 req/min, no symbol cap on WebSocket [L1][L2], same adjusted bars as the free tier. Half the price of Massive Advanced ($199 [L6]). **Alternative at $0:** **Schwab Trader API**, *if the user already has a Schwab account*: real-time quotes, multi-symbol quote call, 120 req/min (3rd-party) [L30][L31]. It costs a browser re-login every 7 days (3rd-party) [L32], and the API also supports trading, so register only the Market Data product. |

### 1.3 Is real-time worth paying for?

**No, not for this system as specified.** The horizon is swing and longer. Stops and targets
are evaluated "a few times a day". Nothing executes automatically. So a consolidated price
15 minutes old changes almost no decisions. What *does* change decisions is **single-venue
data**. Paying $0–29 for consolidated-but-delayed data is better than paying $0 for
IEX-only real-time data. Revisit real-time ($99 Alpaca SIP) only if:

1. tripwires start to alert *intraday* on fast gap moves and a 15-minute lag becomes a
   real cost, or
2. the middleware wants a live price at the moment the user reviews a recommendation.
   Even then, a real-time IEX price labeled "IEX, indicative" is usually enough for display.

**Suggested stack:** start on **Alpaca Basic (free)**. Tripwires use SIP 1-minute or daily
bars with `end ≤ now − 15 min`. Display uses IEX real-time, labeled. The daily scan uses
multi-symbol daily SIP bars after the close. Keep **Massive Starter $29** only if the
one-call market snapshot, flat files or MCP convenience are worth $29, or as a second
source to cross-check. Upgrade to Alpaca SIP $99 only if a real-time trigger appears.

### 1.4 Implications for `QuoteProvider` (no code changed here)

- `QuoteProvider.quote(ticker)` is one ticker per call. Every recommended vendor has a
  **batch** endpoint (Alpaca `/v2/stocks/snapshots?symbols=…` [L3], Massive full-market
  snapshot [L7], Schwab multi-symbol quotes [L30]). A `quotes(tickers)` method would avoid
  100 calls per tripwire sweep. This is a suggested protocol change; `ARCHITECTURE.md` rules
  apply before making it.
- Set `DataSnapshot.as_of` to the **vendor's trade or bar timestamp**, not the fetch time. A
  delayed quote is then correctly dated 15 minutes back, and the payload should carry
  `feed: "sip" | "iex" | "delayed_sip"` so stages and humans know which one they saw.
- `positions()`: this repo's rules keep brokerage access read-only. Of the options here,
  only Schwab, Tradier, IBKR and tastytrade give positions, and each of them is also an
  order-capable API. See §3.3.

---

## 2. Comparison table

Legend: **RT** = real-time; **Delayed** = 15-min delayed; **SIP** = consolidated tape
(all exchanges, 100% of volume); **IEX / single-venue** = one exchange only.
"Poll 100" = can it refresh ~100 tickers every few minutes? "Scan 5k" = can it pull a
~5,000-ticker daily snapshot?

| Vendor / plan | Latency | Consolidated? | REST / WS | Batch endpoint | Poll 100 / Scan 5k | Price (individual) | License & fees | SDK / MCP (order tools?) | Same-vendor adjusted history |
|---|---|---|---|---|---|---|---|---|---|
| **Massive Basic** | EOD [L6] | SIP-based (EOD) [L10] | REST | Grouped daily "Daily Market Summary": all US stocks in 1 call [L11] | Poll: no (5 calls/min [S3 in prior doc]); Scan: **yes** (1 call, EOD) | $0 | Personal, non-pro [L10] | Official Python client; MCP, no orders [L9] | Yes, 2 yrs |
| **Massive Starter / Developer** | Delayed [L6] | **Yes**: "100% market coverage", individual plans SIP-based [L6][L10] | REST + WS + flat files | Full-market snapshot; `tickers=` list or all [L7] | Yes / **Yes (1 call)** | $29 / $79 [L6] | Personal, non-pro; no exchange paperwork for individual plans (unverified) | Same | Yes, 5 / 10 yrs; split-adjusted by default [L8] |
| **Massive Advanced** | **RT** [L6] | Yes | same | same | Yes / Yes | $199 [L6] | Personal, non-pro [L10] | same | Yes, 20+ yrs |
| **Alpaca Basic** | **RT IEX**; SIP free once ≥15 min old [L1][L3] | IEX only for "latest"/snapshots; **SIP for bars ≥15 min old** [L1][L3] | REST + WS (IEX, 30 symbols) [L2] | `/v2/stocks/snapshots?symbols=`; multi-symbol bars [L3] | **Yes** (200 req/min [L2]) / **Yes** (SIP daily bars after close) | $0 | Personal. `delayed_sip` feed exists in the SDK [L5]; whether the free plan can use it for "latest" calls is **conflicting** [L1][L3] | `alpaca-py`; official MCP **has order tools** (filterable with `ALPACA_TOOLSETS`) [L15] | Yes: `adjustment=raw/split/dividend/all` [L5]; 7+ yrs (prior doc) |
| **Alpaca Algo Trader Plus** | **RT SIP** [L1][L2] | **Yes** | REST + WS, unlimited symbols [L2] | same | Yes / Yes | **$99/mo** [L1][L2] | Personal (prior doc S43b) | same | same |
| **Tiingo Free / Power** | RT IEX [L12] | **IEX only** (Tiingo fills in prices between trades with its own algorithm, "when inline with the overall market") [L12] | REST + WS [L12] | `/iex/` with many tickers per call [L13] | Free: 50 req/h (prior doc), marginal. Power: 10k req/h (yes) / EOD endpoint | $0 / **$30** [L14] | Basic/Power: internal, personal only [L12] | Community SDK and MCP (prior doc) | **Yes**: CRSP-style `adjClose` etc., `splitFactor`, `divCash` [L16]; 30+ yrs EOD |
| **Finnhub** | RT (source venue not documented) [L17] | **unverified** | REST + WS (50 symbols free) [L17] | `/quote` is one symbol per call [L18] | Poll: 100 calls at 60/min, about 2 min per sweep, marginal; Scan: **no** | $0; paid market data from $49.99 (3rd-party) [L19] | Free = personal, non-commercial (3rd-party) [L17] | Official SDKs; no official MCP found | Candles exist; adjustment convention **unverified** |
| **Twelve Data** | "RT" on all plans [L20] | **No**: venues that need no extra license, about 5% of US volume [L21] | REST + WS | Batch up to 120 symbols, but **1 credit per symbol** [L22] | Free 8 credits/min: **no**. Grow: yes | $0; Grow $79, Pro $229, Ultra $999 [L20] (another page says Grow "$29", 3rd-party [L23]) | Individual pricing; redistribution needs add-on [L21] | Official Python SDK | Yes (convention unverified) |
| **EODHD** | Live endpoint delayed 15–20 min; WebSocket RT [L24][L25] | Delayed: **unverified**; **WS = Cboe EDGX only** (single venue) [L25] | REST + WS | Live endpoint `s=` for multiple tickers [L24] | Yes (100k calls/day [L26]) / Yes (bulk EOD, prior doc) | EOD+Intraday All World Extended €29.99 (includes WS) (3rd-party) [L26]; All-in-One €99.99 [L26] | Standard plans personal only [L26] | Official MCP, 72 tools, data only (prior doc S32b) | Yes (splits/dividends endpoints) |
| **FMP** | Starter+ "real-time US" [L27] | **unverified** (source not disclosed) | REST | `batch-quote` [L28] | Yes (300/min Starter) / Yes (bulk on Ultimate) [L27] | ~$29 Starter / $69 / $149 Ultimate (3rd-party) [L29] | Personal plan: no display to third parties (prior doc S33d) | Hosted official MCP, data only (prior doc) | Yes |
| **Alpha Vantage** | Free: delayed or historical; RT needs premium + entitlement [L33][L34] | unverified | REST | `REALTIME_BULK_QUOTES` up to 100 symbols (premium) [L33] | Free: 25/day, **no**. $49.99 plan: delayed; RT from $99.99 (3rd-party) [L33] | $49.99–$249.99 [L33] | Personal use through the "Alpha X Terminal" entitlement process [L33] | Official MCP (prior doc) | Yes (adjusted daily is premium, unverified) |
| **Databento EQUS.MINI** | **RT** [L35] | **Partial**: synthetic NBBO from 4 venues (NYSE Chicago, NYSE National, IEX, MIAX) [L35] | Live TCP/WS client, historical API | Stream the whole market | Yes / Yes (EQUS.SUMMARY gives consolidated EOD [L36]) | Usage-based, or flat $825/mo unlimited; Standard plan $199 [L35][L36] | **No exchange license fees** [L35] | Official Python/Rust/C++ SDKs | EOD consolidated; adjustment handling **unverified** |
| **Intrinio** | RT IEX or Nasdaq Basic; delayed Cboe / SIP [L37] | Nasdaq Basic ≈ Nasdaq venues + TRF; not full SIP | REST + WS | yes (per docs) | Yes / Yes | Individual real-time from **$150/mo** [L37] | "No exchange fees or paperwork" for IEX feed [L37] | Official SDKs | Yes |
| **Marketstack** | Basic: IEX intraday at ≥15-min intervals; RT on Professional (3rd-party) [L38] | IEX | REST | multi-symbol (unverified) | Basic 10k req/month: **no** | $9.99 / $49.99 (3rd-party) [L38] | APILayer ToS (unverified) | none | EOD adjusted (unverified) |
| **Barchart OnDemand** | RT / delayed / EOD via `getQuote` [L39] | depends on entitlement | REST | multi-symbol `getQuote` | unverified | **Quote-based**; commercially licensed [L39] | Commercial | none | Yes (`getHistory`) |
| **Schwab Trader API** | **RT** for accounts with real-time quotes (3rd-party) [L31] | Presumably consolidated (**unverified**) | REST + streamer [L31] | Quotes for a comma-separated symbol list (3rd-party) [L30] | **Yes** (120 req/min) / Yes (about 50 calls, **unverified**) | **$0 for Schwab clients** (3rd-party) [L31] | App approval takes days; refresh token lasts 7 days (3rd-party) [L32] | Community MCPs, some read-only (3rd-party) [L40]. **API can trade** | `pricehistory` split-adjusted, **not dividend-adjusted** (3rd-party) [L41] |
| **Tradier** | RT for brokerage account holders; sandbox delayed [L42] | unverified | REST + streaming [L42] | multi-symbol quotes [L42] | Yes / unverified | Account needed; Pro $10 / Pro Plus $35 per month (3rd-party) [L43] | Brokerage terms | Official SDKs. **API can trade** | Yes (history endpoint) |
| **Interactive Brokers** | RT with subscriptions; snapshots $0.01 each [L44][L45] | Yes with Network A/B/C bundles | TWS / Client Portal APIs | Streaming watchlists | Yes / costly | Snapshot bundle $10 (waived at $30 commissions); streaming add-on $4.50 [L44] | Non-pro attestation in the IBKR portal (unverified) | TWS has a **"Read-Only API"** setting [L45] | Yes; overkill |
| **tastytrade** | RT for **funded** non-pro accounts (DXLink) [L46] | via dxFeed (unverified) | WS | Streaming | Yes / unverified | Account needed | Brokerage terms | **Official MCP has order tools; `TASTYTRADE_READ_ONLY=1` withholds all 14 write tools** [L47] | Limited |
| **Yahoo / yfinance** | Near-RT or delayed (unofficial) | Unknown | Scraped endpoints | `download()` of many tickers | Rate-limited (429s; one report ~950 tickers then blocked) [L48][L49] | $0 | **Unofficial; Yahoo's API "intended for personal use only"**; not affiliated with Yahoo [L50] | none | Adjusted closes, but provenance unverifiable |

---

## 3. Cautions

### 3.1 IEX-only prices for stop checks

- IEX is one exchange, about 2–5% of US volume depending on how it is measured [L4][L21].
  A free "real-time" feed from Alpaca Basic, Tiingo, Twelve Data (about 5% of volume [L21]),
  Marketstack, or EODHD's WebSocket (**Cboe EDGX only** [L25]) is **not** the market price.
- **Risk:** tripwires use the day's low and high to detect a stop or target touch. Single-venue
  bars **understate the range**, so a real breach can go undetected. The last trade on a
  small cap may also be many minutes old.
- **Rule:** tripwires and outcomes use **SIP** data: Alpaca SIP bars ≥15 min old, Massive, or
  paid SIP. IEX real-time is allowed only for display, labeled with its feed.
- Tiingo "improves" IEX prices with an internal algorithm [L12]. That is useful for display,
  but it is not an auditable exchange print.

### 3.2 Unofficial APIs

- **yfinance** is unofficial and not affiliated with Yahoo. Yahoo's API is "intended for
  personal use only" [L50]. It breaks when Yahoo changes endpoints, and it is aggressively
  rate-limited [L48][L49]. At most, use it as a manual cross-check. **Never** use it as the
  tripwire source.
- **IEX Cloud** shut down with three months' notice (announced 2024-05-31, off 2024-08-31)
  [L51]. Even official cheap feeds can disappear, which is one more reason to keep vendors
  behind `data/base.py`.

### 3.3 Broker APIs that allow trading

- Schwab, Tradier, IBKR, tastytrade and Alpaca's brokerage API can all **place orders**. The
  repo rule is decision support only.
  - **Alpaca:** use the *Market Data* REST endpoints through our own adapter. Do **not**
    connect `alpaca-mcp-server`: by default it enables all tools, including
    `place_stock_order` and `cancel_all_orders` [L15]. `ALPACA_TOOLSETS=stock-data` narrows
    the tools, but the rule is "no MCP that exposes order tools", and a config flag is one
    typo away from exposing them.
  - **tastytrade:** the official MCP places real orders unless `TASTYTRADE_READ_ONLY=1` is
    set [L47]. Same verdict: don't connect it.
  - **Schwab:** register the app **only** for "Market Data Production", not "Accounts and
    Trading Production" [L32]. Note that `positions()` needs the trading product.
  - **IBKR:** keep TWS's "Read-Only API" setting on. It blocks API orders [L45].
- Keep broker credentials out of any stage prompt, and give the adapter no order methods.
  `ARCHITECTURE.md` already requires this.

### 3.4 Non-professional status and paperwork

- Massive individual plans are **non-professional only**: a natural person, personal and
  non-business use. Professional users must buy Business plans [L10].
- Tiingo Power and Twelve Data individual plans are personal or internal use only [L12][L21].
  EODHD standard plans are personal only [L26].
- Broker feeds (Schwab, IBKR, E*TRADE, tastytrade) need **exchange market-data agreements**
  and a **non-professional attestation** at signup [L44][L52]. Anyone registered with a
  regulator, or trading for an entity, may be classed as professional and pay many times
  more. Answer these questions accurately.
- None of these licenses allows showing the data to other people. If this pipeline is ever
  shared, every choice above has to be re-licensed.

### 3.5 Split-adjustment consistency

- Live quotes are always **unadjusted** (today's actual price). Stops and targets set on
  adjusted history must be re-based when a split takes effect between the day a
  recommendation is made and the day it is checked.
- Use the same vendor for history and today's bar where possible:
  - **Alpaca:** `adjustment=split`, so the convention can match exactly [L5].
  - **Massive:** split-adjusted by default, not dividend-adjusted (prior doc S8) [L8].
  - **Schwab:** `pricehistory` is split-adjusted, not dividend-adjusted (3rd-party) [L41].
  - **Tiingo:** CRSP-style adjusted fields [L16].
- Store raw bars plus split factors, and apply the adjustment locally. That avoids
  depending on each vendor's convention.

---

## 4. Workload fit (worked numbers)

| Job | Alpaca Basic | Massive Starter | Alpaca SIP $99 | Schwab |
|---|---|---|---|---|
| ~100 tickers every 5 min (tripwires) | 1 snapshot call (IEX) or 1 multi-symbol bars call (SIP, ≥15 min old). Limit is 200/min [L2] | 1 snapshot call [L7] | 1 call, real-time SIP | 1 quote call; limit 120/min [L30] |
| ~5,000 tickers once a day | Multi-symbol daily bars after the close, a few dozen calls, SIP | **1 call** (full-market snapshot or grouped daily) [L7][L11] | same as Basic | about 50 calls (**unverified** symbol cap per call) |
| Today's bar for the technical agent | SIP bar ≥15 min old, `adjustment=split` [L5] | Snapshot `day` bar, delayed | real-time | quote plus `pricehistory` |

---

## 5. What was not verified

- Whether Alpaca's free plan can use `feed=delayed_sip` on the *latest* and *snapshot*
  endpoints. Sources conflict [L1][L3]. The documented fallback, SIP **bars** ≥15 min old,
  is enough.
- Whether a brokerage account is required for Alpaca market data. Basic is "the default for
  Paper and Live accounts" [L2]; data-only signup is **unverified**.
- The symbol-per-call caps for Schwab quotes and Alpaca snapshots.
- Finnhub's and FMP's real-time source venue (IEX? Cboe? SIP?).
- Current FMP, EODHD, Marketstack and Finnhub paid prices. Only 3rd-party pages were reachable.

---

## 6. Sources

- [L1] Alpaca market data FAQ and About Market Data API (Basic = IEX real time; SIP needs Algo Trader Plus $99; SIP queries need `end` ≥15 min old on the free plan): https://docs.alpaca.markets/us/docs/market-data-faq ; https://docs.alpaca.markets/us/docs/about-market-data-api ; https://docs.alpaca.markets/us/docs/historical-stock-data-1
- [L2] Alpaca data plans (Basic 200 req/min, 30 WebSocket symbols; Algo Trader Plus 10,000 req/min, no symbol cap; Basic is the default for Paper/Live): https://alpaca.markets/data ; https://docs.alpaca.markets/us/docs/about-market-data-api ; summary (3rd-party): https://apis.io/plans/alpaca/alpaca-plans-pricing/
- [L3] Alpaca snapshots endpoint (`/v2/stocks/snapshots?symbols=`; free plan gets IEX latest trade/quote/minute bar, daily bars aggregated the same for both plans); `delayed_sip`: https://alpaca.markets/learn/snapshot-api ; https://docs.alpaca.markets/reference/stocksnapshots-1 ; https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data ; https://forum.alpaca.markets/t/free-account-paper-trading-iex-sip-questions/19208
- [L4] IEX market share (Q2 2026: 3.8% overall, 4.7% intraday): https://www.marketsmedia.com/outlook-2026-bryan-harkins-iex-group/ ; https://www.iex.io/news
- [L5] `alpaca-py` enums, read directly on GitHub: `DataFeed` (IEX, SIP, DELAYED_SIP, …) and `Adjustment` (raw/split/dividend/all): https://github.com/alpacahq/alpaca-py/blob/master/alpaca/data/enums.py
- [L6] Massive pricing (Starter $29 / Developer $79 delayed; Advanced $199 real time; Starter: unlimited calls, 100% market coverage, WebSockets, snapshots, flat files): https://massive.com/pricing ; https://massive.com/stocks
- [L7] Massive full-market snapshot (`tickers` list or all): https://massive.com/docs/rest/stocks/snapshots/full-market-snapshot
- [L8] Massive aggregates are split-adjusted by default (`adjusted=true`): https://massive.com/docs/rest/stocks/aggregates/custom-bars ; https://massive.com/knowledge-base/categories/aggregates
- [L9] Massive MCP README (experimental; data tools; no order tools), read on GitHub: https://github.com/massive-com/mcp_massive
- [L10] Massive professional status (individual plans non-pro only; individual plans SIP-based; Business add-ons for proprietary feeds): https://massive.com/blog/understanding-professional-status ; https://massive.com/knowledge-base/article/what-are-the-different-massive-subscriptions-i-can-use
- [L11] Massive Daily Market Summary / grouped daily (all US stocks for a date in one request): https://massive.com/docs/rest/stocks/aggregates/daily-market-summary ; https://massive.com/knowledge-base/article/how-can-i-get-the-daily-prices-for-all-stocks-using-massives-market-data
- [L12] Tiingo IEX API (direct IEX connection; prices filled in between trades; Basic/Power internal and personal use only): https://www.tiingo.com/products/iex-api ; https://www.tiingo.com/documentation/iex ; https://www.tiingo.com/documentation/websockets/iex
- [L13] Tiingo `/iex/` multi-ticker behaviour, `tngoLast` (client libraries): https://github.com/hydrosquall/tiingo-python ; https://business-science.github.io/riingo/reference/riingo_iex_prices.html
- [L14] Tiingo Power $30/mo individual, 10,000 req/h, 100,000/day, ~108–110k symbols/month: https://www.tiingo.com/about/pricing ; https://www.tiingo.com/account/billing/pricing ; https://www.tiingo.com/blog/iex-cloud-alternatives/
- [L15] Alpaca MCP server README, read on GitHub (all toolsets enabled by default; `trading` toolset includes `place_stock_order`, `cancel_all_orders`; `ALPACA_TOOLSETS` filter): https://github.com/alpacahq/alpaca-mcp-server
- [L16] Tiingo EOD adjusted fields and CRSP method: https://www.tiingo.com/documentation/end-of-day ; https://www.tiingo.com/products/end-of-day-stock-price-data
- [L17] Finnhub free tier (60 calls/min, real-time US quotes, WebSocket 50 symbols, personal use) (partly 3rd-party): https://finnhub.io/pricing ; https://apicostcalc.com/finnhub.html ; https://freeapi.watch/finnhub/
- [L18] Finnhub quote endpoint (single `symbol`): https://finnhub.io/docs/api/quote
- [L19] Finnhub Market Data Basic from $49.99/mo (3rd-party): https://apicostcalc.com/finnhub.html ; https://tradingdatacompare.com/providers/finnhub/
- [L20] Twelve Data individual pricing (Basic free 8/min, 800/day; Grow $79, Pro $229, Ultra $999): https://twelvedata.com/pricing ; https://support.twelvedata.com/en/articles/5335783-trial
- [L21] Twelve Data US equities (licence-free venues, about 5% of US volume; add-on for external display): https://support.twelvedata.com/en/articles/9935903-us-equities-market-data
- [L22] Twelve Data batch requests (up to 120 symbols; 1 credit each): https://support.twelvedata.com/en/articles/5203360-batch-api-requests
- [L23] Twelve Data "Grow from $29" claim (3rd-party, conflicts with L20): https://www.codewords.ai/blog/twelve-data-api
- [L24] EODHD Live (delayed) prices API (15–20 min; `s=` multi-ticker): https://eodhd.com/financial-apis/live-ohlcv-stocks-api
- [L25] EODHD real-time WebSockets (US trades/quotes from Cboe EDGX; <50 ms): https://eodhd.com/financial-apis/new-real-time-data-api-websockets ; https://eodhd.com/financial-apis-blog/real-time-feed-major-update
- [L26] EODHD pricing (100k calls/day; All-in-One €99.99; EOD+Intraday All World Extended €29.99 with WebSockets; personal use) (partly 3rd-party): https://eodhd.com/pricing ; https://www.findmymoat.com/tools/eodhd ; https://www.g2.com/products/eodhd-financial-data-apis/pricing
- [L27] FMP plan guide (Starter adds real-time US; call limits; Ultimate bulk): https://site.financialmodelingprep.com/insights/platform/how-to-choose-the-right-financial-modeling-prep-plan-for-your-workflow ; https://site.financialmodelingprep.com/faqs
- [L28] FMP batch quote: https://site.financialmodelingprep.com/developer/docs/stable/batch-quote
- [L29] FMP prices (3rd-party): https://www.trustradius.com/products/financial-modeling-prep/pricing ; https://www.findmymoat.com/tools/financial-modeling-prep-fmp
- [L30] Schwab quotes by comma-separated list; 120 req/min (3rd-party): https://mylinedchart.com/resources/articles/schwab-api-for-technical-traders-workflow-fit-checklist ; https://medium.com/@carstensavage/the-unofficial-guide-to-charles-schwabs-trader-apis-14c1f5bc1d57
- [L31] Schwab API free for account holders; real-time if the account has real-time quotes; streamer (3rd-party): https://github.com/api-evangelist/charles-schwab ; https://grokipedia.com/page/Schwab_Trader_API ; https://developer.schwab.com/products
- [L32] Schwab app registration (Market Data Production vs Accounts and Trading Production; refresh token 7 days, access token 30 min) (3rd-party): https://medium.com/@carstensavage/the-unofficial-guide-to-charles-schwabs-trader-apis-14c1f5bc1d57 ; https://altanalytics.github.io/schwabr/
- [L33] Alpha Vantage premium ($49.99–$249.99; `REALTIME_BULK_QUOTES` 100 symbols; entitlement process) (tier to real-time mapping partly 3rd-party): https://www.alphavantage.co/premium/ ; https://www.alphavantage.co/documentation/ ; https://www.findmymoat.com/tools/alpha-vantage
- [L34] Alpha Vantage free 25 requests/day: https://www.alphavantage.co/support/ ; https://www.macroption.com/alpha-vantage-api-limits/
- [L35] Databento US Equities Mini (4 venues, synthetic NBBO, no exchange licence fees; flat $825/mo unlimited): https://databento.com/blog/databento-us-equities-mini-now-available ; https://databento.com/docs/venues-and-datasets/equs-mini ; https://databento.com/equities
- [L36] Databento pricing plans (Standard $199/mo) and EQUS.SUMMARY consolidated EOD: https://databento.com/blog/upcoming-changes-to-pricing-plans-in-january-2025 ; https://databento.com/blog/introducing-databento-us-equities ; https://databento.com/docs/venues-and-datasets/equs-summary
- [L37] Intrinio real-time (IEX, Nasdaq Basic; delayed Cboe/SIP; individual from $150/mo): https://intrinio.com/pricing ; https://intrinio.com/financial-market-data/real-time-prices ; https://intrinio.com/financial-market-data/stock-prices-iex
- [L38] Marketstack plans (3rd-party): https://www.findmymoat.com/tools/marketstack ; https://marketstack.com/pricing
- [L39] Barchart OnDemand getQuote / FAQ: https://www.barchart.com/ondemand/api/getQuote ; https://www.barchart.com/ondemand/faq ; https://github.com/api-evangelist/barchart
- [L40] Schwab read-only community MCPs (3rd-party): https://lobehub.com/mcp/tapojit-schwab-mcp ; https://glama.ai/mcp/servers/psonhoang/schwab-mcp
- [L41] Schwab `pricehistory` split-adjusted, not dividend-adjusted (3rd-party): https://altanalytics.github.io/schwabr/reference/schwab_priceHistory.html
- [L42] Tradier market data (real-time for account holders; sandbox 15-min delayed): https://docs.tradier.com/docs/market-data ; https://documentation.tradier.com/brokerage-api/markets/get-quotes
- [L43] Tradier Pro $10 / Pro Plus $35 (3rd-party): https://brokerchooser.com/broker-reviews/tradier-review/tradier-fees ; https://tradier.com/individuals/pricing
- [L44] IBKR market data pricing (snapshot bundle $10 waived at $30 commissions; streaming add-on $4.50): https://www.interactivebrokers.com/en/pricing/market-data-pricing.php ; https://www.interactivebrokers.com/en/pricing/research-news-marketdata.php
- [L45] IBKR TWS API read-only setting; $0.01 regulatory snapshots: https://interactivebrokers.github.io/tws-api/initial_setup.html ; https://interactivebrokers.github.io/tws-api/md_request.html ; https://www.interactivebrokers.com/campus/ibkr-api-page/market-data-subscriptions/
- [L46] tastytrade streaming market data; live quotes once funded: https://developer.tastytrade.com/streaming-market-data/ ; https://support.tastytrade.com/support/s/solutions/articles/43000475299
- [L47] tastytrade official MCP README, read on GitHub (real-money orders; `TASTYTRADE_READ_ONLY=1` withholds 14 write tools): https://github.com/tastytrade/tastytrade-mcp
- [L48] yfinance 429 rate-limit issues: https://github.com/ranaroussi/yfinance/issues/2125 ; https://github.com/ranaroussi/yfinance/issues/2128
- [L49] Why yfinance gets blocked (3rd-party): https://medium.com/@trading.dude/why-yfinance-keeps-getting-blocked-and-what-to-use-instead-92d84bb2cc01
- [L50] yfinance README legal notice, read on GitHub (v1.7.0 on PyPI): https://github.com/ranaroussi/yfinance ; https://pypi.org/project/yfinance/
- [L51] IEX Cloud shutdown: https://www.alphavantage.co/iexcloud_shutdown_analysis_and_migration/ ; https://massive.com/blog/iex-cloud-migration-guide
- [L52] E*TRADE API requires signing the market data agreement for real-time quotes: https://developer.etrade.com/getting-started ; https://apisb.etrade.com/docs/api/market/api-quote-v1.html
