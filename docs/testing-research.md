# Backtesting and forward (paper) testing: research

*Researched 2026-09-25. Every factual claim cites a source from the [Sources](#sources) list
as `[S#]`. arxiv.org, huggingface.co, quantconnect.com, vectorbt.pro, docs.alpaca.markets,
docs.tradier.com, interactivebrokers.com and several other sites were blocked by the egress
proxy. For those, claims come from search-engine extracts of the cited page, from GitHub
READMEs/LICENSE files read via `git clone`, or from PyPI metadata. A claim that only a
third party makes is tagged **(3rd-party)**. A claim that no source confirmed is tagged
**unverified**. Sample-size numbers marked **(own calc)** are computed here from the cited
formulas. Nothing here was run against live data.*

Read with: [`ARCHITECTURE.md`](ARCHITECTURE.md) §3 (principles), §5 (open item: testing),
§6 (Equibles as sole vendor), §7 (assessment).

---

## Executive summary

**Recommendation: build the test harness in-house, around the pipeline we already have,
and treat forward testing as the primary evidence. Adopt libraries only for analytics.
No broker paper account is needed, so the no-orders rule can stay.**

1. **The honest backtest window is tiny today.** The configured model (`claude-opus-5`) has
   a training-data cutoff of **May 2026**; the current Opus 5.5 is **June 2026** [S20]. The
   literature is consistent that an LLM recalls pre-cutoff outcomes and that prompting,
   masking and anonymization do **not** reliably stop it [S3][S4][S6][S11]. So honest
   evidence starts around June–July 2026: roughly 3–4 months of dates, and for swing trades
   held weeks to 3 months only the earliest of those have closed. Backtests over older dates
   are useful as **plumbing and process tests**, never as performance evidence.
2. **Phase 0 (safest, start now): a forward "shadow ledger".** Run the pipeline daily in
   live mode; record every recommendation (not just the ones you accept) in an append-only,
   timestamped ledger with deterministic fill rules; mark to market from Equibles daily bars
   through the existing `PriceDataProvider`; score with the existing deterministic
   `compute_outcome`. No orders, no new vendor, no broker keys.
3. **Phase 1: a replay harness over post-cutoff dates.** Loop `Middleware.run(as_of,
   live=False)` and `FollowUpLoop.tick(now)` over past dates; store results in a separate
   store; enforce `holdout_start >= max(training cutoff of every model used)`; label anything
   earlier as "contaminated / dev only". Add a simulated decision policy stored apart from
   real decisions.
4. **Phase 2: analytics.** Feed the ledger's trade list into `bt` (MIT) and `quantstats`
   (Apache-2.0) or `vectorbt` for benchmark-relative metrics and tearsheets [S34][S48].
   Evaluate at three levels: every stage's rejects vs. passes (per-stage attribution), the
   system's full recommendation set, and the user's accepted subset, separately.
5. **Do not adopt** a framework that wants to own the loop (QuantConnect/LEAN, NautilusTrader,
   Zipline, Backtrader, TradingAgents, Lumibot): each expects strategies written in its own
   framework and/or bundles its own data vendor, which clashes with "Equibles only" and with
   our stage architecture. Their useful ideas (fill models, date-grid replay, decision logs,
   anonymized-prompt ablation) are cheap to copy.
6. **Broker paper trading (Alpaca paper, IBKR paper, Tradier sandbox) is optional and
   last.** Every one of them works by *placing orders* (simulated) through the same API as
   live trading, so adopting one means relaxing the hard rule. For daily-bar swing trades it
   adds little: Alpaca paper, for example, does not simulate dividends, slippage or
   liquidity [S37].

**Key risks:** LLM look-ahead leakage (worse than it looks; mitigations only partial);
too few trades for statistical significance (a 60% hit rate needs ~150 independent trades
to distinguish from a coin flip; a Sharpe of 1 needs ~2.7 years of daily data) **(own calc)**;
Equibles data gaps that weaken any backtest (unconfirmed delisted coverage, macro only as
latest-revised values, per-share values adjusted to today, reused tickers, no news archive);
and LLM non-determinism, which means one run per date is a sample, not a measurement.

---

## 1. Backtesting approaches for an LLM agent pipeline

### 1.1 Approaches compared

| Approach | What it is | Fit here | LLM cost | Leakage exposure |
|---|---|---|---|---|
| **Event-driven replay with `as_of`** | For each past date, run the whole pipeline as if it were that day, then simulate Agent 5 ticks and outcomes forward on daily bars. | **Best fit.** The code already takes `as_of` everywhere and `RawDataBundle.add` rejects later snapshots (`data/base.py`). `Middleware.run(as_of, live=False)` and `FollowUpLoop.tick(now)` are the entry points. | Full pipeline per simulated date (Agent 0 + N sectors + ~10–30 companies each + technical). | Full: every prompt names tickers and dates. |
| **Vectorized backtest of the recommendations** | Generate recommendations once (by replay or forward), then evaluate the resulting trade list / weights in a vectorized engine; vary fill rules, costs, position sizing, "accept top-k" policies cheaply. | **Good complement.** Separates the expensive LLM step from the cheap portfolio step. `bt`, `vectorbt` or plain pandas. | None beyond generating the recommendations. | Inherits whatever leakage the recommendations had. |
| **Walk-forward** | Tune on window *k*, test on window *k+1*, roll forward. | Applies to anything we *tune* (prompts, rules thresholds, profile, approving improvement notes). With ~3–4 honest months, only a couple of folds are possible now. | As replay. | Only meaningful on post-cutoff dates. |
| **Forward (shadow/paper) test** | Run live each day; record recommendations immutably; score later. | **Primary evidence.** Nothing is known to the model in advance. | One run per trading day (or per scan cadence). | None (by construction), apart from logical leakage from prompts (§1.3). |
| **Benchmarks/competitions** (StockBench, InvestorBench, LiveTradeBench, Alpha Arena) | Fixed environments where the agent must emit buy/sell/hold. | **Poor fit.** They expect a single trading agent with their own data and action space, not a staged research pipeline with a human gate. Useful as reading, not as a harness. | — | StockBench's window (Mar–Jun 2025) [S13] is now *before* our model's cutoff, so it is no longer contamination-free for Claude Opus 5 [S20]. |

### 1.2 How others handle LLM look-ahead, and how well it works

| Mitigation | Evidence | Verdict for us |
|---|---|---|
| **Test only after the model's training cutoff** | Look-ahead propensity (LAP) "is materially positive throughout the in-sample period and collapses essentially to zero right after the training-data cutoff"; the leakage interaction "loses significance on post-training-cutoff samples" [S4]. Post-cutoff, Lopez-Lira et al. "observe no recall" [S3]. StockBench and LiveTradeBench are built on this idea [S13][S15]. HindsightBench finds *behaviorally effective* cutoffs span 22 months across vendors and **precede** vendor-reported dates by up to 8 months [S6], so the vendor's date is a conservative bound. But: "models legitimately know more about times near their cutoff, so recency mimics leakage", and a simple before/after comparison cannot separate the two [S7]. | **The only mitigation that reliably works.** Use the latest *training data cutoff* across every model the run uses (stage agents, Agent 5, process review) [S20]. Every model upgrade moves the boundary. |
| **Entity anonymization (remove company names/tickers)** | Glasserman & Lin: in-sample, anonymized headlines *outperformed*, i.e. a "distraction effect" from knowing the company was larger than look-ahead bias [S2]. Lopez-Lira et al.: "masking fails as LLMs reconstruct entities and dates from minimal context" [S3]. ai-hedge-fund withholds ticker, industry and dates in backtests and says this "reduces the recall without removing it (distinctive numbers can still give a large company away)" [S22]. | **Partial.** Also conflicts with our design: the company deep dive reads filings and names catalysts; anonymizing that guts the analysis. Use only as a **sensitivity ablation** (does performance drop when names/dates are masked? if yes, suspect recall). |
| **Date masking / relative dates (t-0, t-1 …)** | KTD-Fin masks identifiers and calendar information "consistently across prompts and tools"; masking "substantially changes agent rationales", and under leakage control returns are "largely explained by passive market and style exposure, with limited evidence of persistent stock-selection alpha" [S11]. HindsightBench shows a "date-trigger reflex" present in every 2026-generation model tested [S6]. | **Partial**, and the finding that masked agents show little alpha is a warning about what to expect. |
| **Instructions ("pretend it is date X, don't use later knowledge")** | "Instructions to respect historical boundaries fail to prevent recall-level accuracy" [S3]. | **Does not work.** Do not rely on the prompt's `as_of` wording. |
| **Point-in-time (chronologically trained) LLMs** | ChronoBERT/ChronoGPT: one vintage per year from 1999, trained only on text available then; Hugging Face releases exist (e.g. `chrono-gpt-v1-20241231`) [S9]. Scaled PiT models up to 4B params with monthly checkpoints 2013–2024 "approach" leading open-weight models [S10]. Look-Ahead-Bench finds "significant lookahead bias in standard LLMs … unlike Pitinf models" [S5]. | **Leak-free by construction, but not usable for our pipeline**: small models, no Claude equivalent, far weaker at multi-step reasoning over filings. Possible use: a cheap leak-free baseline for Agent 1 scoring. |
| **Inference-time unlearning** (FinCAD, Divergence Decoding) | FinCAD (EMNLP 2026) cuts in-sample returns by up to 67.1% on memorized dates while keeping 2025 out-of-sample returns close to baseline, across five 7–14B models and five mega-caps [S1]. Divergence Decoding adjusts a base model's logits using two small fine-tuned models and "effectively removes both verbatim and semantic knowledge" [S8]. | **Not applicable**: both need logit access / open weights; Claude via the API does not expose that. Evidence is on small models and few stocks. |
| **Detection / measurement** (LAP test, HindsightBench probes, matched clean controls) | LAP regression test [S4]; HindsightBench's four-arm date-manipulation matrix and "post-cutoff placebo" at probe-level cost [S6]; leakage-adjusted scores via matched clean controls [S7]. Leakage "concentrates on outcomes that surprised the crowd and were well covered in training" [S7]. | **Worth copying** as a cheap audit: before trusting any replay window, probe the model for recall of prices/events in that window. |

**Other leak channels specific to us:**

- **Logical leakage**: a question can reveal its own answer through what it implies about
  the evaluation date ("time traveler's paradox") [S18]. Our prompts state `as_of`; the
  model knows it is being asked about the past if it knows today's date.
- **Data leakage** (not LLM): survivorship, restatements, split-adjusted per-share values,
  revised macro. §5 of `ARCHITECTURE.md` and [§6.2](#62-data-caveats-that-weaken-any-backtest-here) below.
- **Human leakage**: prompts, rules and thresholds tuned while looking at the test window.
  Every replay over a post-cutoff window "spends" it as a holdout.

### 1.3 What the evidence says to expect

- Over 2004–2024 and 100+ S&P 500 symbols **including delisted stocks**, FinMem and FinAgent
  "do not beat buy-and-hold on risk-adjusted metrics and show no statistically significant
  alpha"; LLM strategies were too conservative in bull markets and too aggressive in bear
  markets [S12].
- StockBench: "most models struggle to outperform the simple buy-and-hold baseline" [S13].
- LiveTradeBench (50-day live evaluation of 21 LLMs): high LMArena scores do not imply
  better trading outcomes [S15].
- A six-month production record of LLM trading fleets found no directional edge (41% vs 50%
  round-trip win rate against a retail benchmark) and frontier-model decision quality
  "statistically indistinguishable" in paired replay [S17] (crypto, leveraged; different
  setting from ours).
- A review of 164 finance-LLM papers found no single bias (look-ahead, survivorship,
  narrative, objective, cost) discussed in more than 28% of studies [S19].

This matches `ARCHITECTURE.md` §7: expect mediocre early results; the value is honest
falsification.

---

## 2. Existing tools

Maintenance = date of the latest commit on the default branch, read by shallow `git clone`
on 2026-09-25, plus the latest PyPI release [S48].

### 2.1 Backtesting engines

| Tool | What it does | Drive our pipeline per date? | License | Cost | Data bundled | Last commit / release |
|---|---|---|---|---|---|---|
| **QuantConnect LEAN** (engine) | Event-driven C# engine with Python algorithms; backtest + live [S28]. | Not naturally. Algorithms run inside LEAN; our pipeline would have to run outside and be imported as **custom data** (`PythonData` with `get_source`/`reader`) [S29]. Calling an external LLM per bar inside a backtest: one comparison says QC puts "the LLM outside the backtest loop" **(3rd-party)** [S29]; QC's own forum thread asking whether LLM API calls are allowed had no confirmed answer in the extract (**unverified**). | Apache-2.0 [S28] | Engine free | None in the open-source repo beyond samples; QC data is sold separately [S29]. | 2026-09-25 |
| **LEAN CLI** | Local/cloud backtests, data download, research, local live [S28]. | Same as LEAN. | Apache-2.0 [S28] | Requires membership in a **paid-tier** organization [S29]; US-equity data needs the **US Equity Security Master** subscription plus per-symbol-day data [S29]. Paid plans quoted at $60–$1,080/mo, backtest nodes $14–$96/mo **(3rd-party)** [S29]. | QC data (survivorship-aware security master) if bought; conflicts with "Equibles only". | 2026-09-04; PyPI `lean` 1.0.229 (2026-08-28) |
| **QuantConnect Cloud** | Hosted research/backtest/live; an MCP server lets an LLM create projects, run backtests **and deploy live algorithms** [S29]. | No (same as LEAN). | Proprietary service | Free tier: one backtest node and one research node **(3rd-party)** [S29]. | QC data licensed in-cloud. | — |
| **NautilusTrader** | Rust-native, deterministic event-driven engine; Python control plane; same strategy code for backtest and live [S30]. | Only by wrapping our output as custom data/actors; "raw external data is not fed directly — you usually wrangle into Nautilus domain models first" **(3rd-party)** [S30]. Built for execution realism we don't need at daily resolution. | LGPL-3.0 [S30] | Free | None (adapters for venues). | 2026-09-26; 1.231.0 (2026-08-02) |
| **Backtrader** | Classic event-driven Python backtester. | Via custom data feed; framework-owned loop. | GPL-3.0+ [S31] | Free | None | **2023-04-19** (unmaintained) |
| **vectorbt** (open source) | Vectorized NumPy/Numba backtesting of many configurations at once [S32]. | **Yes, for the vectorized step**: feed entry/exit signals or orders from our ledger. | Apache-2.0 **with Commons Clause** ("fair code"; no selling a product whose value derives from it) [S32] | Free | None (loaders for public sources). | 2026-09-17; 1.1.0 (2026-07-05) |
| **vectorbt PRO** | Adds parallelization, portfolio optimization, limit orders, leverage, "over 100 other features" [S32]. | As above. | Private repo, membership [S32] | Annual plan quoted at $20/mo; lifetime credit option (minimum $150) [S32]. Other tiers **unverified** (site blocked). | — | — |
| **Zipline-reloaded** | Event-driven Python backtester (Quantopian lineage), pandas ≥ 2 [S33]. | Custom bundle + `handle_data`; framework-owned loop. | Apache-2.0 [S33] | Free | None; you ingest a data bundle [S33]. | 2025-11-13; 3.1.1 (2025-07-19) — slow |
| **bt** | Tree-based, weight-centric portfolio backtesting on pandas [S34]. FinRL-X uses it as its backtest engine [S23]. | **Yes, for the vectorized step**: target weights / trade list per date → equity curve vs benchmark. | MIT [S34] | Free | None | 2026-09-25; 1.2.3 (2026-09-12) |
| **Backtesting.py** | Lightweight single-instrument backtester. | Per-ticker only; awkward for a multi-name ledger. | **AGPL-3.0** [S35] | Free | Samples | 2026-08-05; 0.6.6 (2026-07-22) |
| **PyBroker** | ML-oriented backtesting with walk-forward and bootstrap metrics. | Framework-owned loop. | Apache-2.0 **with Commons Clause** ("free for non-commercial use") [S36] | Free | Loaders for public sources. | 2026-08-27; 2.0.1 (2026-08-28) |
| **FINSABER / FINSABER-2** | Research backtester built to test LLM timing strategies over 20 years with delisted stocks and explicit execution timing (`next_open`); pluggable `TradingData` loaders; writes `llm_costs.csv` [S12]. | **Closest in spirit** (LLM strategies, bias controls), but strategy interface is per-ticker timing, not a staged research pipeline. A good reference for fill timing and bias controls. | Apache-2.0 (LICENSE file and PyPI) [S12][S48]; one search extract said MIT **(3rd-party)**. | Free | S&P 500 2000–2025 parquet dataset on Hugging Face [S12] (pre-cutoff, so contaminated for our model). | 2026-09-17; 2.0.1 (2026-05-11) |

### 2.2 LLM-agent trading frameworks

| Tool | What it does | Fit | License | Status |
|---|---|---|---|---|
| **TradingAgents** (Tauric Research) | LangGraph multi-agent firm (analysts, researchers, trader, risk, portfolio manager); supports Anthropic and many providers. v0.5.0 added "point-in-time integrity across every dated path", SEC EDGAR fundamentals "served as filed", and `run_backtest` over a ticker × date grid scored on realized alpha vs a regional benchmark, with its own decision log [S21]. States it is for research, not advice, and that results vary run to run [S21]. | **Reference, not a harness.** It backtests *its own* agents. Its `run_backtest` design (grid, separate log, resume, score only closed windows) is exactly what our Phase 1 needs, and it is small enough to copy the idea. Could also serve as an external **baseline** on the same dates. Note: PyPI name `tradingagents` belongs to a different repo (Mai0313) [S48]. | Apache-2.0 [S21] | Active: v0.5.1 commit 2026-09-24 |
| **ai-hedge-fund** (virattt) | Investor-persona agents; interactive app; backtests a "mandate" at its rebalance cadence; backtests withhold ticker, industry and dates from prompts [S22]. Needs a Financial Datasets API key [S22]. | Reference for the anonymization ablation. Own data vendor and loop. "Educational … not intended for real trading" [S22]. | MIT [S22] | Active: 2026-09-25 |
| **FinRL** / **FinRL-X** | FinRL: deep-RL trading library. FinRL-X: "weight-centric" modular stack; data from FMP/Yahoo/WRDS; `bt`-powered backtests; **Alpaca live/paper execution** [S23]. | Poor: RL/ML strategies and its own data; execution path places orders. | FinRL MIT; FinRL-X Apache-2.0 [S23][S48] | FinRL repo active (2026-09-23) though PyPI 0.3.7 is from 2024-04; FinRL-X active (2026-09-18) |
| **FinMem** | LLM trading agent with layered memory and character profiling [S24]. | Poor; research code. Did not beat buy-and-hold under FINSABER [S12]. | — | **Last commit 2024-08-17** |
| **FinAgent** | Multimodal tool-augmented trading agent (KDD 2024) [S25]. | Poor; same FINSABER result [S12]. Official code location **unverified** (a 4-star third-party repo exists). | — | — |
| **Lumibot** | Python strategy framework with built-in AI-agent runtime, backtests on free daily data, 12 broker integrations; tagline "AI agents that actually place the trade" [S26]. | Poor: framework-owned lifecycle, oriented to order placement. | GPL-3.0 [S26] | Active: 2026-09-25; 4.6.0 |
| **Vibe-Trading** (HKUDS) | Personal trading agent with backtests, MCP, multi-market data; changelog mentions an "MCP order gate" and broker portfolio layer [S27]. | Poor: own agent and loop; includes order paths. | MIT [S27] | Very active (created 2026-04; 34k stars) |

### 2.3 Benchmarks and live competitions

| Benchmark | What | Relevance |
|---|---|---|
| **StockBench** | Multi-month daily buy/sell/hold simulation with prices, fundamentals, news (Polygon, Finnhub); window 2025-03-03 → 2025-06-30 chosen to be post-cutoff for the models tested; metrics: cumulative return, max drawdown, Sortino [S13]. Apache-2.0; last commit 2025-10-28. | Design template; its window is pre-cutoff for Claude Opus 5 [S20]. |
| **InvestorBench** (ACL 2025) | Tasks across stocks, crypto, ETFs; 13 LLMs; all struggle in volatile markets [S14]. | Reading only. |
| **LiveTradeBench** | Live streaming evaluation (US stocks + Polymarket) to eliminate leakage; 50-day live run of 21 LLMs [S15]. PolyForm **Noncommercial** license; last commit 2025-11-21 [S15][S48]. | Validates "forward testing is the clean test". |
| **KTD-Fin** | Masked-identifier benchmark with Barra-style attribution into market, style and selection alpha; reports per-order Brier score and ECE [S11]. | Template for attribution and calibration metrics. |
| **Look-Ahead-Bench**, **HindsightBench** | Measure look-ahead in finance LLMs [S5][S6]. | Template for leakage probes. |
| **Alpha Arena** (Nof1) | Models trade real capital ($10k each) in crypto perps on Hyperliquid; Season 1 ran 2025-10-18 → 11-03, Qwen 3 Max won with +22.3% **(3rd-party)**; as of 2026-08-06 no Season 2 results **(3rd-party)** [S16]. | Entertainment-grade evidence: tiny sample, crypto, leverage. |

---

## 3. Forward / paper testing options

### 3.1 Comparison

| Option | Needs order placement? | Cost | What you get | Safety risk | Fit |
|---|---|---|---|---|---|
| **(a) In-house simulated ledger** | **No** | Equibles calls + LLM tokens only | Exactly our semantics (entry/stop/target, `level_trigger`, horizons, Agent 5 alerts), all recommendations, per-stage attribution. | None (no broker credentials exist). | **Recommended.** |
| **(b1) Alpaca paper** | **Yes** (simulated orders via the same Trading API as live) | Free paper account [S37] | $100K simulated funds [S37]; fills only when marketable against NBBO, but order size is not checked against NBBO size; **no** dividends, market impact, latency slippage, queue position or price improvement **(3rd-party summary of Alpaca docs)** [S37]. | Paper and live differ only by key pair and base URL (`paper-api.alpaca.markets`); "the API spec is the same" [S37]. A config slip trades real money. A **paper-only account** type exists [S37] and removes that risk. | Only if the rule is relaxed. |
| **(b2) IBKR paper** | **Yes** | Needs an IBKR account | Paper shares the live account's market-data permissions (delayed if not subscribed); fills simulated from top of book; some order types unsupported; **dividends and splits not processed** **(3rd-party)** [S38]. | Paper vs live is a **port** choice: TWS 7497 vs 7496, IB Gateway 4002 vs 4001 [S38]. One wrong port = live. | Only if relaxed; heavier setup. |
| **(b3) Tradier sandbox** | **Yes** | Tradier brokerage account holders [S39] | Full trading API with paper money; data and fills **15-min delayed**; no streaming in sandbox [S39]. | Separate host `sandbox.tradier.com` [S39]. | Only if relaxed. |
| **(b4) Schwab / thinkorswim paperMoney** | n/a | — | paperMoney is **not exposed** through the Schwab Trader API; the API is live-only **(3rd-party)** [S40]. | Using the API at all means live orders. | **Unusable** programmatically. |
| **(b5) TradingView paper trading** | n/a | Webhook alerts need a paid plan **(3rd-party)** [S41] | No public API to drive TradingView paper trading from Python **(3rd-party)** [S41]. | — | **Unusable** programmatically. |
| **(c) Portfolio tracker / journal** | **No** | Free (self-hosted) or subscription | Record hypothetical trades as "activities" and get performance views. | Low (no broker link needed). | **Optional viewer** on top of (a). |
| **(d) Paper-trading MCP servers** | Varies (below) | — | — | Several expose order tools or can be flipped to live. | Not needed; see §3.4. |

### 3.2 What an in-house ledger needs (option a)

Everything below maps onto existing code; none of it places orders.

1. **Run modes and separate storage.** A `run_mode` on every run (`live`, `forward_shadow`,
   `backtest`) and a separate `Store` (e.g. a separate SQLite file) per backtest run, so
   simulated data can never mix with real positions.
2. **Simulated decision policy, stored apart.** E.g. `accept_all`, `accept_top_k_by_score`,
   `accept_if_no_flags`. Write to a `sim_decisions` table, never to the real decisions
   table; `Store.review_trail()` must not read it either (hard rule on user decisions,
   `ARCHITECTURE.md` §3.5). Score the full recommendation set as the primary series; the
   policy only defines extra "accepted" series.
3. **Fill rules (deterministic, documented).** Entry: a limit at `plan.entry_price`, filled
   on the first daily bar after `as_of` whose range touches it (or at the next open if the
   open is already past it and within `stale_entry_max_drift_pct`); expire unfilled
   entries after N days. Stop/target: per `level_trigger` (close or intraday), with gaps
   filled at the open, and a same-bar stop-and-target tie resolved pessimistically.
   Costs: configurable bps per side. FINSABER's explicit `execution_timing` (`next_open`)
   is a good reference [S12].
4. **Mark to market** via `PriceDataProvider.bars` and the existing `compute_outcome`.
5. **Immutability.** Append-only rows with the creation timestamp and a hash of the
   recommendation payload (hash-chained), so nobody can later edit a forward-test record.
   Optionally commit a daily JSON export to git for an external timestamp.
6. **Benchmarks.** SPY and the relevant sector ETF from Equibles prices (availability of ETF
   history in Equibles **unverified**), plus a "random pick from the same Agent 1 shortlist"
   baseline (see §4.3).
7. **Scheduler.** One daily job after the close: `Middleware.run(now, live=True)` →
   ledger insert → `FollowUpLoop.tick(now)` → mark to market.

### 3.3 Portfolio-tracking / journaling apps (option c)

| App | How trades get in | Order placement? | License / cost |
|---|---|---|---|
| **Ghostfolio** | REST `POST /api/v1/import` with a bearer token; also an MCP server that can read the portfolio and **import activities**, with restricted read scopes that never read monetary values [S42]. | No | AGPL-3.0, self-hosted free; hosted Premium ~€9/mo **(3rd-party)** [S42] |
| **Portfolio Performance** | CSV import wizard, manual entry; data stored locally (XML) [S43]. | No | Free desktop app **(3rd-party)** [S43]; license **unverified** |
| **Tradervue** | API to import trades programmatically [S44]. | No | Subscription (price **unverified**) |
| **TradesViz** | Imports and read-only broker syncs; can explore hypothetical stop/target variations [S44]. | No | Freemium (details **unverified**) |

These add a UI, not rigor: the ledger in §3.2 remains the source of truth.

### 3.4 MCP servers for paper trading

| Server | Order tools? | Notes |
|---|---|---|
| **Alpaca MCP server** (official) | **Yes**: the `trading` toolset covers orders, positions, option exercise [S37]. | `ALPACA_PAPER_TRADE` defaults to `true`; **setting it to `false` switches to live** [S37]. `ALPACA_TOOLSETS` can restrict to e.g. `stock-data,news` [S37]. MIT, active (2026-09-25). |
| **IBKR official MCP** (`api.ibkr.com/v1/api/mcp-public`) | Account data and portfolio tools; "every order requires your approval" suggests order tools exist **(3rd-party extract of IBKR press release)** [S38]. | Launched mid-2026 (**unverified** date from URL). |
| **interactive-brokers-mcp** (code-rabi) | **Yes**: `place_order` unless `IB_READ_ONLY_MODE` is on; `IB_PAPER_TRADING` flag [S38]. | MIT, last commit 2026-07-21. |
| **paper-trader-mcp** | Records order *intents* and estimates fills from historical Alpaca NBBO quotes, "without placing live orders" **(3rd-party)** [S45]. | Closest to "no orders"; maturity **unverified**. |
| **open-paper-trading-mcp** | Simulated orders inside its own simulator (43 MCP tools); market data from the Robinhood API [S45]. | Apache-2.0; last commit 2025-10-09. |
| **Paper Invest `mcp-server`** | Places paper orders on Paper's platform [S45]. | MIT; last commit 2025-09-18. |
| **QuantConnect MCP** | Can **deploy live algorithms** [S29]. | Avoid. |

Under the repo's rule (MCP only via `HttpMcpClient` with a read-only allowlist), none of the
order-capable servers should be connected. If one ever is, allowlist only data tools and
use a paper-only account whose keys cannot reach a live account.

---

## 4. Evaluation metrics and methodology

### 4.1 Units of evaluation (keep them separate)

1. **Stage decisions** (all candidates, including rejects): the largest sample. Used for
   per-stage attribution and calibration.
2. **System recommendations** (everything that survives the technical stage and the rules):
   the pipeline's real track record.
3. **Accepted positions** (the user's decisions): the user's track record. Reported
   separately and **never fed to the process agent or any stage prompt**.

### 4.2 Metrics

| Metric | Unit | Notes |
|---|---|---|
| **Hit rate** (target before stop; or positive excess return at horizon) | recommendation | Report with a binomial confidence interval, never alone. |
| **Excess return vs benchmark** (SPY and sector ETF) per trade, at the plan horizon and at fixed horizons (e.g. 5/20/60 trading days) | recommendation | Fixed horizons make trades comparable and let rejected candidates be scored too. |
| **Expectancy** (mean R-multiple: return ÷ planned risk to stop) | recommendation | Natural for plans with stop/target; profile already fixes max loss and min reward:risk. |
| **MAE / MFE** | recommendation | Already in `OutcomeReport`; shows whether stops/targets are placed well. |
| **Portfolio-level**: CAGR, volatility, max drawdown, Sharpe/Sortino, beta, alpha vs benchmark | ledger equity curve | Needs a sizing rule (e.g. equal risk per trade). Use `bt`/`quantstats`. Decompose returns into market/style vs selection, as KTD-Fin does with Barra-style attribution [S11], or at least regress on the benchmark. |
| **Probabilistic / Deflated Sharpe, MinTRL** | equity curve | PSR adjusts an observed Sharpe for sample length, skew and kurtosis; MinTRL gives the minimum observations to reject the null; DSR also corrects for the number of variants tried [S46]. |
| **Calibration** of the 0–1 `confidence` | stage decision | Define the event (e.g. "target before stop"). Brier score and ECE over 10 bins, as KTD-Fin does per order [S11]; with small samples use 3–5 bins plus the Brier decomposition. |
| **Rank skill (IC)** of Agent 1's `potential_score` | every scored company | Spearman correlation between score and forward excess return across the whole shortlist. Uses 10–30 companies per sector per run instead of a handful of trades. |
| **Cost per recommendation** | run | Tokens × price [S20]; Batch API is 50% off, cache reads 5–10% of input price [S20]. `ARCHITECTURE.md` says cost is not a concern yet, but it bounds how many replay dates are affordable. |
| **Stability** | repeated runs on the same `as_of` | LLM outputs vary run to run [S21]; measure agreement across 2–3 repeats of a sample of dates. |

### 4.3 Per-stage attribution

The structured stage records make counterfactual scoring cheap:

- For each stage, compare forward excess returns (fixed horizons) of **passed vs rejected**
  candidates. A stage that rejects winners as often as losers adds nothing.
- Baselines per stage: a **random pick from the same Agent 1 shortlist** (does the deep
  dive beat chance within the sector?), **all companies in the sector** (does Agent 1 beat
  the sector?), and **sector ETF** (does Agent 0's sector call beat the market?).
- Rule vetoes vs judgment rejections are already separated on `StageRecord.rules`; score
  them separately.
- The process agent's grades can be checked against outcomes only at the aggregate level;
  its purpose (§3.6) is to judge reasoning, not to predict P&L.

### 4.4 How many trades, how long

**(own calc)** One-sided α = 0.05, power 0.8, independent trades:

| Question | Needed |
|---|---|
| Is a **55%** hit rate better than 50%? | ~617 trades |
| Is a **60%** hit rate better than 50%? | ~153 trades |
| Is a **65%** hit rate better than 50%? | ~67 trades |
| With 30 trades, wins needed for p < 0.05 (exact binomial) | 20 (67%) |
| With 100 trades, wins needed | 59 |
| Mean excess return +2%/trade, SD 10%/trade | ~155 trades |
| Mean excess return +1%/trade, SD 10%/trade | ~619 trades |
| MinTRL (95%, normal returns) for annualized Sharpe **1.0** | ~685 trading days (~2.7 years) |
| MinTRL for Sharpe **0.5** / **1.5** / **2.0** | ~10.8 / ~1.2 / ~0.7 years |

Formulas: normal-approximation sample size for a proportion/mean; MinTRL per Bailey & López
de Prado [S46]. Practitioner rules of thumb ("at least 30 trades … aim for 100+") agree in
order of magnitude **(3rd-party)** [S47].

Implications:

- A low-frequency, human-gated system will **not** reach significance on accepted trades
  for years. Score the **full recommendation set** and **stage-level** decisions, which are
  10–100× more numerous.
- Trades opened in the same week in the same sector are **correlated**; effective sample
  size is lower than the count. Cluster by entry week / sector, or block-bootstrap.
- Every variant tried (prompt versions, rules thresholds, policies) is a multiple test.
  Keep a log of variants; use DSR [S46] or White's Reality Check / Hansen's SPA for
  "best of N" comparisons [S47].
- A reasonable forward-test gate: at least ~6 months and ~100 closed system
  recommendations before reading anything into P&L, with process-quality and calibration
  reviewed monthly from the start. This is a judgment call, not a sourced standard.

---

## 5. Recommendation: phased plan

Ordered safest first. None of Phases 0–3 places orders or needs a broker.

### Phase 0 — Forward shadow ledger (start immediately)

- **Build:** `run_mode`; append-only hash-chained ledger of every recommendation with
  timestamps; deterministic fill and mark-to-market module (§3.2); `sim_decisions` table and
  one or two decision policies; daily scheduler job; a small deterministic metrics module
  (hit rate with CI, excess return vs SPY/sector ETF, R-multiples, MAE/MFE, IC of Agent 1
  scores, Brier/ECE).
- **Codebase impact:** new modules (e.g. `backtest/ledger.py`, `backtest/fills.py`,
  `backtest/metrics.py`), a new table in `store.py`, CLI commands. The middleware and agents
  stay unchanged. Depends on "Remaining work" items 1–4 (Equibles price, sector,
  filings adapters, CLI).
- **Rule impact:** none.

### Phase 1 — Replay harness over post-cutoff dates

- **Build:** `Backtester(start, end, step, models)` that loops `Middleware.run(as_of,
  live=False)` and replays `FollowUpLoop.tick` over daily bars into a separate store;
  a **model-cutoff registry** and enforcement of `holdout_start >= max(cutoffs)` (wires up
  the unused `holdout_start`, item 8); runs before it are labelled `contaminated` and
  excluded from reports; split the post-cutoff window into a dev part (for tuning) and a
  sealed part (touched once); resume and skip completed dates (as TradingAgents does [S21]);
  an LLM-response cache keyed by (model, prompt hash) so metric changes don't re-bill.
- **Leakage audit:** before trusting a window, run cheap recall probes (e.g. "what did
  TICKER close at on DATE+30?") in the spirit of HindsightBench / LAP [S4][S6]; optionally
  run a masked-ticker/relative-date ablation on a sample of dates [S22][S11] as a
  sensitivity check.
- **Also needed:** adapter tests proving every Equibles adapter filters payloads by
  `as_of` (item 9); explicit handling of §6.2 data caveats.
- **Rule impact:** none. Replay of older dates is allowed for *plumbing and process*
  tests only.

### Phase 2 — Analytics and attribution (adopt libraries)

- **Adopt:** `bt` (MIT) or `vectorbt` (Commons Clause; fine for personal use) for
  vectorized portfolio simulations over the ledger; `quantstats` (Apache-2.0) for
  tearsheets [S34][S32][S48]. Optional: `jsharpe` or own code for PSR/MinTRL/DSR [S46].
- **Build:** per-stage attribution report (§4.3), calibration report, variant log for
  multiple-testing corrections.
- **Optional:** mirror ledger activities into a self-hosted Ghostfolio via its import API
  for a UI [S42] (AGPL service run separately; nothing linked into our code).

### Phase 3 — Baselines

- Random-from-shortlist, sector ETF, buy-and-hold SPY (deterministic, free).
- Optional: run TradingAgents' `run_backtest` on the same tickers/dates as an external LLM
  baseline [S21] (Apache-2.0; separate environment; uses its own data vendors, so treat as
  indicative only).

### Phase 4 — Broker paper account (only with an explicit decision to relax the rule)

- **Adds:** broker-simulated fills and a second opinion on execution. For daily-bar swing
  trades this is marginal: Alpaca paper does not model dividends, slippage or liquidity
  **(3rd-party)** [S37]; IBKR paper does not process dividends or splits **(3rd-party)**
  [S38].
- **If chosen:** an Alpaca **paper-only** account (no live account behind the keys) [S37];
  a separate `PaperBroker` module outside `data/`, never reachable from agents or MCP
  allowlists; startup assertion that the base URL is the paper host; no live keys on the
  machine. Avoid IBKR (paper vs live is only a port number) and Schwab/TradingView (no
  programmatic paper) [S38][S40][S41].

### Decisions needed from the user

1. Approve Phase 0/1 scope and the fill rules (§3.2 item 3).
2. Choose the default simulated decision policy (recommend: score all recommendations;
   add "top-k by Agent 1 score" as a second series).
3. Confirm Equibles coverage for SPY/sector ETF history and delisted tickers.
4. Decide whether Phase 4 is ever wanted (default: no; the rule stays).

---

## 6. Risks and caveats

### 6.1 Method risks

- **Leakage is larger and subtler than date filtering.** Recall survives masking and
  instructions [S3]; leakage concentrates on well-covered surprises [S7], which is exactly
  what a catalyst-driven pipeline looks for.
- **The honest window keeps moving and shrinking.** Switching `claude-opus-5` (cutoff May
  2026) to Opus 5.5 (June 2026) pushes the boundary a month later [S20]. Pin model IDs
  (Claude IDs are pinned snapshots) and note retirement dates (Opus 5: not before
  2027-07-24) [S20] so replays stay reproducible.
- **Non-determinism.** One run per date is one sample; repeat a subset [S21].
- **Human-in-the-loop bias.** If you tune prompts or approve improvement notes while
  watching forward results, those months stop being a holdout.
- **Regime dependence.** A few months of forward data covers one regime; LLM agents have
  shown regime-dependent behaviour (too cautious in bull markets, too aggressive in bear)
  [S12].
- **Benchmarks age.** Public benchmarks built to be contamination-free (StockBench [S13])
  stop being so when newer models train past their window.

### 6.2 Data caveats that weaken any backtest here

From `ARCHITECTURE.md` §6 and [`equibles-evaluation.md`](equibles-evaluation.md):

- **Delisted coverage unconfirmed** for Equibles prices (self-hosted prices come from
  Yahoo): survivorship bias in sector screens and breadth.
- **Macro (FRED) only as latest-revised values**, no vintages: macro inputs in replays are
  revised data the model could not have seen.
- **Per-share values adjusted to today's share basis**: dropped in backtests (reveals
  future splits).
- **Hosted tool resolves tickers to today's company**: reused tickers can point at the
  wrong company.
- **No historical news archive**; earnings calendar unconfirmed; PDUFA dates deferred:
  replays under-feed the catalyst stages compared with the design.

These make forward testing *more* important, not less: in live mode, these gaps affect
live runs and forward results equally, so the forward record measures the system as it
actually runs.

### 6.3 Safety

- Every broker paper option works by placing orders through a live-grade API; the only
  difference is a key, a URL, an env var or a port [S37][S38][S39]. Treat any such
  integration as live-capable code.
- Several MCP servers bundle order tools with data tools and can be switched to live with
  one setting [S37][S38][S29].

---

## Sources

Blocked sites are marked *(via search extract)*; GitHub facts come from READMEs/LICENSE files
read via shallow `git clone` on 2026-09-25.

- **[S1]** Li et al., "Summoning the Oracle to Slay It: Mitigating Look-Ahead Bias in Financial Backtesting with LLMs" (FinCAD), arXiv:2605.24564 — https://arxiv.org/abs/2605.24564 *(via search extract)*; code: https://github.com/waylonli/FinCAD
- **[S2]** Glasserman & Lin, "Assessing Look-Ahead Bias in Stock Return Predictions Generated by GPT Sentiment Analysis", arXiv:2309.17322 — https://arxiv.org/abs/2309.17322 *(via search extract)*
- **[S3]** Lopez-Lira, Tang & Zhu, "The Memorization Problem: Can We Trust LLMs' Economic Forecasts?" — https://arxiv.org/abs/2504.14765 ; https://papers.ssrn.com/abstract=5217505 *(via search extract)*
- **[S4]** Gao, Jiang & Yan, "Detecting Lookahead Bias in LLM Forecasts", arXiv:2512.23847 — https://arxiv.org/abs/2512.23847 *(via search extract)*
- **[S5]** Benhenda, "Look-Ahead-Bench", arXiv:2601.13770 — https://arxiv.org/abs/2601.13770 ; https://github.com/benstaf/lookaheadbench *(via search extract)*
- **[S6]** "HindsightBench: A Black-Box Behavioral Audit Protocol for Parametric Hindsight", arXiv:2607.18867 — https://arxiv.org/abs/2607.18867 *(via search extract)*
- **[S7]** Zhang & Stadie, "Temporal Leakage in LLM Backtesting: Measurement, Validation, and Adjusted Scores", arXiv:2608.02985 — https://arxiv.org/abs/2608.02985 *(via search extract)*
- **[S8]** Merchant & Levy, "A Fast and Effective Solution to the Problem of Look-ahead Bias in LLMs", arXiv:2512.06607 — https://arxiv.org/abs/2512.06607 ; https://github.com/fin-ai-lab/fast-effective-solution-to-lab *(via search extract)*
- **[S9]** He, Lv, Manela & Wu, "Chronologically Consistent Large Language Models" — https://arxiv.org/html/2502.21206v2 ; https://huggingface.co/manelalab/chrono-gpt-v1-20241231 *(via search extract)*
- **[S10]** "Scaling Point-in-Time Language Models", arXiv:2607.11889 — https://arxiv.org/abs/2607.11889 *(via search extract)*
- **[S11]** "From Knowing to Doing: A Memory-Controlled Benchmark for LLM Trading Agents on Stock Markets" (KTD-Fin), arXiv:2605.28359 — https://arxiv.org/abs/2605.28359 ; https://arxiv.org/html/2605.28359v1 *(via search extract)*
- **[S12]** Li et al., "Can LLM-based Financial Investing Strategies Outperform the Market in Long Run?" (FINSABER, KDD 2026) — https://arxiv.org/abs/2505.07078 *(via search extract)*; code: https://github.com/waylonli/FINSABER
- **[S13]** "StockBench: Can LLM Agents Trade Stocks Profitably in Real-world Markets?", arXiv:2510.02209 — https://arxiv.org/abs/2510.02209 *(via search extract)*; https://github.com/ChenYXxxx/stockbench ; https://stockbench.github.io/
- **[S14]** "INVESTORBENCH", ACL 2025 — https://aclanthology.org/2025.acl-long.126/ ; https://arxiv.org/abs/2412.18174 *(via search extract)*
- **[S15]** LiveTradeBench — https://github.com/ulab-uiuc/live-trade-bench ; https://www.emergentmind.com/papers/2511.03628 *(via search extract)*
- **[S16]** Alpha Arena — https://nof1.ai/ ; https://www.iweaver.ai/blog/alpha-arena-ai-trading-season-1-results/ (3rd-party); https://www.traderank.ai/blog/alpha-arena-alternatives-2026 (3rd-party)
- **[S17]** "What LLM Trading Agents Actually Do in Production", arXiv:2609.05663 — https://arxiv.org/abs/2609.05663 ; https://github.com/ProjectDXAI/continuous-record-llm-trading-agents *(via search extract)*
- **[S18]** Paleka et al., "Pitfalls in Evaluating Language Model Forecasters" (ICLR 2026) — https://arxiv.org/abs/2506.00723 *(via search extract)*
- **[S19]** "Evaluating LLMs in Finance Requires Explicit Bias Consideration", arXiv:2602.14233 — https://arxiv.org/abs/2602.14233 *(via search extract)*
- **[S20]** Anthropic model docs — https://platform.claude.com/docs/en/models/overview ; https://platform.claude.com/docs/en/models/opus-5/overview (fetched)
- **[S21]** TradingAgents README and LICENSE — https://github.com/TauricResearch/TradingAgents
- **[S22]** ai-hedge-fund README and LICENSE — https://github.com/virattt/ai-hedge-fund
- **[S23]** FinRL-X README/LICENSE — https://github.com/AI4Finance-Foundation/FinRL-Trading ; FinRL — https://github.com/AI4Finance-Foundation/FinRL
- **[S24]** FinMem — https://github.com/pipiku915/FinMem-LLM-StockTrading ; https://arxiv.org/abs/2311.13743
- **[S25]** FinAgent (KDD 2024) — https://arxiv.org/abs/2402.18485 ; https://dl.acm.org/doi/10.1145/3637528.3671801 *(via search extract)*
- **[S26]** Lumibot README/LICENSE — https://github.com/Lumiwealth/lumibot
- **[S27]** Vibe-Trading README/LICENSE — https://github.com/HKUDS/Vibe-Trading
- **[S28]** LEAN — https://github.com/QuantConnect/Lean ; LEAN CLI — https://github.com/QuantConnect/lean-cli
- **[S29]** QuantConnect docs *(via search extract)*: CLI install (paid tier) https://www.quantconnect.com/docs/v2/lean-cli/installation/installing-lean-cli ; US equities data https://www.quantconnect.com/docs/v2/lean-cli/datasets/quantconnect/download-in-bulk/us-equities ; data costs https://www.quantconnect.com/docs/v2/lean-cli/datasets/quantconnect/download-by-ticker/costs ; custom data https://www.quantconnect.com/docs/v2/lean-cli/datasets/custom-data ; MCP https://www.quantconnect.com/mcp ; pricing https://www.quantconnect.com/pricing/ ; LLM forum thread https://www.quantconnect.com/forum/discussion/20504/using-llm-apis-claude-gpt-in-quantconnect-research-environment-allowed/ ; 3rd-party: https://newyorkcityservers.com/blog/quantconnect-review , https://lumibot.lumiwealth.com/agents.html
- **[S30]** NautilusTrader README/LICENSE — https://github.com/nautechsystems/nautilus_trader ; https://nautilustrader.io/docs/latest/concepts/backtesting/ *(via search extract)*
- **[S31]** Backtrader — https://github.com/mementum/backtrader
- **[S32]** vectorbt README/LICENSE — https://github.com/polakowo/vectorbt ; VectorBT PRO — https://vectorbt.pro/become-a-member/ , https://ko-fi.com/s/88d8ca176c *(via search extract)*
- **[S33]** zipline-reloaded — https://github.com/stefan-jansen/zipline-reloaded
- **[S34]** bt — https://github.com/pmorissette/bt
- **[S35]** Backtesting.py — https://github.com/kernc/backtesting.py
- **[S36]** PyBroker — https://github.com/edtechre/pybroker
- **[S37]** Alpaca *(via search extract)*: https://docs.alpaca.markets/us/docs/paper-trading ; https://alpaca.markets/learn/connect-to-alpaca-api ; https://blog.traderspost.io/article/alpaca-paper-trading (3rd-party); Alpaca MCP server README — https://github.com/alpacahq/alpaca-mcp-server ; $100K simulated funds: https://alpaca.markets/mcp-server
- **[S38]** IBKR *(via search extract)*: https://interactivebrokers.github.io/tws-api/initial_setup.html ; https://www.interactivebrokers.com/campus/trading-lessons/paper-trading-vs-live-trading-whats-the-difference/ ; https://www.ibkrguides.com/clientportal/aboutpapertradingaccounts.htm ; https://www.interactivebrokers.com/en/general/about/mediaRelations/7-28-26.php ; interactive-brokers-mcp README — https://github.com/code-rabi/interactive-brokers-mcp
- **[S39]** Tradier *(via search extract)*: https://docs.tradier.com/docs/faq ; https://docs.tradier.com/docs/endpoints
- **[S40]** Schwab (3rd-party): https://blog.traderspost.io/article/does-schwab-have-paper-trading ; https://usethinkscript.com/threads/schwab-api-paper-trading-for-automated-trading-systems.22197/
- **[S41]** TradingView (3rd-party): https://autoview.com/guides/does-tradingview-have-an-api/ ; https://trading-strategies.academy/archives/390
- **[S42]** Ghostfolio README/LICENSE — https://github.com/ghostfolio/ghostfolio ; hosting price (3rd-party) https://blog.elest.io/ghostfolio-free-open-source-privacy-first-portfolio-wealth-tracker/
- **[S43]** Portfolio Performance — https://www.portfolio-performance.info/en/ ; https://www.findmymoat.com/tools/portfolio-performance (3rd-party)
- **[S44]** Tradervue API — https://help.tradervue.com/article/3439-api ; TradesViz — https://www.tradesviz.com/blog/import-complete-guide/ *(via search extract)*
- **[S45]** Paper-trading MCP servers: https://glama.ai/mcp/servers/emile-fortier/paper-trader-mcp (3rd-party, via search extract); https://github.com/Open-Agent-Tools/open-paper-trading-mcp ; https://github.com/paperinvest/mcp-server
- **[S46]** Bailey & López de Prado: Deflated Sharpe Ratio — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 , https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf ; PSR/MinTRL — https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length/ ; https://github.com/tschm/jsharpe *(via search extract)*
- **[S47]** Multiple testing / sample size (3rd-party): https://financial-hacker.com/whites-reality-check/ ; https://www.researchgate.net/publication/256066609 ; https://medium.com/@trading.dude/how-many-trades-are-enough-a-guide-to-statistical-significance-in-backtesting-093c2eac6f05
- **[S48]** PyPI JSON metadata (versions, release dates, license fields), fetched 2026-09-25 — https://pypi.org/project/lean/ , /vectorbt/ , /zipline-reloaded/ , /bt/ , /backtesting/ , /lib-pybroker/ , /nautilus_trader/ , /backtrader/ , /tradingagents/ , /finrl/ , /finsaber/ , /live-trade-bench/ , /lumibot/ , /quantstats/ , /alpaca-py/ , /vibe-trading-ai/
