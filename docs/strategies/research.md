# Trading strategies by trade type: research

*Researched 2026-09-29. Survey behind the three draft strategies in this folder
([`investment.md`](investment.md), [`swing.md`](swing.md), [`short-swing.md`](short-swing.md));
decisions still to make are in [`open-questions.md`](open-questions.md). Nothing here is used
by any agent yet.*

Read with: [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §3 (principle 1: no cross-comparison;
principle 7: no day trading), §4 (horizons, rules), §6 (data), and
[`../../prompts/technical-analysis/role.md`](../../prompts/technical-analysis/role.md).

**Evidence grades used below.**

| Grade | Meaning |
|---|---|
| **A** | Peer-reviewed, and/or replicated out of sample by people other than the author |
| **B** | The author's own published tests, practitioner white papers, or unrefereed working papers |
| **C** | Rules from a book or a track record, no systematic test found (anecdote) |

Numbers are quoted only where a source was read (abstract or full text). A claim only a
search-engine summary gave is marked **(summary)**; a claim not confirmed is **unverified**.
Most academic evidence is **cross-sectional** (long top decile, short bottom decile, monthly
rebalance) and **before costs**; the pipeline trades one stock at a time, long-mostly, with
absolute thresholds (principle 1 forbids ranking candidates against each other). So academic
results tell us *which effect exists*, not *what our version earns*. That gap is what the
backtests have to close.

---

## 1. Cross-cutting evidence (applies to every type)

| Finding | Source | Grade | What it means here |
|---|---|---|---|
| Published anomalies earn **26% less out of sample and 58% less after publication** (97 predictors). Decline is larger for predictors with high in-sample returns. | McLean & Pontiff, *JF* 2016, [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365) | A | Expect every edge below to be smaller than its paper. Budget for decay. |
| After adjusting for data snooping over the full universe of rules, Brock-Lakonishok-LeBaron-type moving-average and range-break rules on the DJIA showed **low profitability in the 10-year out-of-sample period**. | Sullivan, Timmermann & White, *JF* 1999, [SSRN](https://www.ssrn.com/abstract=160330) | A | Simple index timing rules decayed; don't tune many variants and keep the best. |
| Momentum strategies suffer **infrequent, persistent crashes**, partly forecastable: in "panic" states after market declines with high volatility, contemporaneous with rebounds. | Daniel & Moskowitz, *JFE* 2016, [NBER](https://www.nber.org/papers/w20439) | A | A market-regime filter and caution after bear-market lows matter for trend strategies. |
| Scaling momentum exposure by its recent realised volatility **"virtually eliminates crashes and nearly doubles the Sharpe ratio"**. | Barroso & Santa-Clara, *JFE* 2015, [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2041429) | A | Supports volatility-based (ATR) sizing over fixed-notional sizing. |
| Short-term reversal returns are a proxy for **liquidity provision**, and are **highly predictable with the VIX**: they spike in turmoil (e.g. 2007-09). | Nagel, *RFS* 2012, [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1988706) | A | Mean reversion and trend want *opposite* volatility regimes (see §5). |
| Monthly returns after **public news drift** (strongly after bad news); extreme moves **without news reverse**. Mainly in smaller, less liquid stocks. | Chan, *JFE* 2003, [SSRN](https://ssrn.com/abstract=262452) | A | Separates "pullback on no news" (buy) from "drop on news" (avoid). |
| Returns not explained by cash-flow news (analyst revisions) **reverse more**; an enhanced reversal strategy earns ~4× the standard one (risk-adjusted). | Da, Liu & Schaumburg, *Mgmt Sci* 2014, [INFORMS](https://pubsonline.informs.org/doi/10.1287/mnsc.2013.1766) | A | Same as above: condition mean reversion on "no fundamental news". |

---

## 2. Investment (6+ months, weekly chart)

### 2.1 Summary

| Strategy | Goal | Core rule | Evidence |
|---|---|---|---|
| Weinstein stage analysis | Trend persistence | Buy stage 2: breakout above a base, above a rising 30-week MA, on volume; sell below the MA | B/C; one 2026 working paper: only "stage 2" (= rising-MA filter) carries the edge |
| O'Neil CAN SLIM (chart part) | Momentum + breakout from bases | Buy a proper base breakout near highs, in a confirmed uptrend; cut at 7-8% | B (IBD's own studies, studies of past winners); weak academic replications |
| Faber 10-month MA | Avoid bear markets (trend) | Hold when the monthly close > 10-month SMA, else cash | A/B: author's paper, widely replicated, index/asset-class level |
| Antonacci dual momentum | Relative + absolute momentum | Hold the stronger asset only if its own 12-month return beats T-bills | B: author's paper (NAAIM award), asset-class level |
| 12-1 momentum (Jegadeesh-Titman) | Under-reaction / momentum | Buy past 3-12 month winners, hold 3-12 months | A: foundational, replicated globally; decayed and crash-prone |
| 52-week-high proximity (George-Hwang) | Anchoring near highs | Buy stocks closest to their 52-week high | A |
| Trend following on single stocks (Wilcox-Crittenden) | Right-tail capture | Buy all-time highs, exit on a wide ATR trailing stop | B: practitioner papers, large samples |
| Moving-average distance / MA timing on stocks | Trend | Close vs long MA (21/200-day distance; MA timing on volatile portfolios) | A |

### 2.2 Entries

**Weinstein stage analysis.** *Goal:* ride the advancing phase (stage 2) of a stock's
four-stage cycle; avoid basing (1), topping (3) and declining (4) stocks. *Method:* weekly
chart; stage 2 = weekly close breaks above a trading-range ceiling while above a **rising
30-week MA**, on volume at least 2× average (ideally more); alternate entry = the pullback
that retests and holds the breakout level; stop under the prior correction low, later
trailed under the 30-week MA; sell when price closes below a flattening/falling MA; market
and sector must be in stage 2 too. *Evidence:* the book (Weinstein, *Secrets for Profiting in
Bull and Bear Markets*, 1988) has examples, no systematic test. A 2026 SSRN working paper
mechanised the four stages over ~901,500 S&P 500 stock-weeks (1992-2026, survivorship-free):
basing weeks did **not** out-earn topping weeks (the taxonomy's distinctive claim); **only
stage 2 earned a positive market-excess return (+2.3%/yr, t=2.7)**, and stage 2 is by
construction a rising-MA trend filter (Roskill, [SSRN 7429238](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7429238);
**(summary)**, unrefereed, full text not read). Rules as summarised by
[ChartMill](https://www.chartmill.com/documentation/technical-analysis/indicators/92-Weinstein-Stage-Analysis-Indicators)
and [TraderLion](https://traderlion.com/trading-strategies/stage-analysis/). *Grade:* B/C.
*Takeaway:* keep the rising 30-week MA; don't expect extra edge from stage labelling.

**O'Neil CAN SLIM, chart part (N, L, M).** *Goal:* buy leaders as they break out of a
proper base to new highs, in a confirmed market uptrend. *Method:* base (cup-with-handle,
flat base, double bottom) of several weeks; buy within ~5% above the pivot on above-average
volume; "L" = relative-strength leader; "M" = only when the market is in a confirmed
uptrend; **cut every loss at 7-8% below cost**; take most profits at **20-25%**, except hold
at least **8 weeks** a stock that gains 20%+ within 3 weeks of the breakout
([ChartMill on the 7-8% rule](https://www.chartmill.com/documentation/trading-and-investing/methodologies/527-William-ONeils-7-8-Sell-Rule-Explained),
[AAII](https://www.aaii.com/journal/article/68036-a-tribute-to-william-o-neil-revisiting-the-can-slim-strategy)).
*Evidence:* the rules come from IBD's studies of **past big winners**, which is survivorship
by design (only winners studied). Academic tests (Lutey, Crum & Rayome, *J. Accounting and
Finance* 2014, [PDF](http://www.na-businesspress.com/JAF/LuteyM_LWeb14_5_.pdf)) automate a
simplified version and report outperformance, including a 2014-2017 live period **(summary)**;
small journals, the authors' own interpretation of the rules. *Grade:* B.

**Faber 10-month moving average.** *Goal:* sidestep bear markets, where returns are low and
volatility high. *Method:* monthly; hold when the month-end price > 10-month SMA, else
T-bills; total-return data. *Evidence:* on the S&P 500 1901-2012, compounded return
**10.18% timed vs 9.32% buy-and-hold**, max drawdown **42.24% vs 83.66%**, invested ~70% of the
time, **less than one round trip per year**; timing underperformed in roughly half of all
years (Faber, [2013 update of SSRN 962461](https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf),
read). Index/asset-class level, not single stocks. The paper itself reports real-time
performance since 2006 as consistent. *Grade:* A/B (author's paper; widely replicated, e.g.
[Marmi et al.](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID2022037_code327190.pdf?abstractid=1476225&mirid=1)).
*Takeaway:* the MA filter mainly cuts drawdown, not return; its value is in bear markets.

**Antonacci dual momentum.** *Goal:* hold the stronger asset (relative momentum) only while
it trends up in absolute terms (absolute momentum). *Method:* 12-month lookback; if the
winner's excess return over T-bills is negative, hold bonds/bills. *Evidence:* "absolute
momentum does far more to lessen volatility and drawdown", combining both is best
(Antonacci, [SSRN 2042750](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2042750),
abstract). Asset classes, author's own paper. *Grade:* B. *Takeaway:* require **both** a
positive own trend and outperformance of the benchmark.

**12-1 momentum (Jegadeesh-Titman).** *Goal:* capture under-reaction: past 3-12 month
winners keep outperforming for 3-12 months. *Method:* rank on past return (usually skipping
the last month, which reverses), buy the top decile, hold 3-12 months. *Evidence:* significant
positive returns over 3-12 month holds, not explained by systematic risk; **part of the
first-year abnormal return dissipates over the following two years**
(Jegadeesh & Titman, *JF* 1993, [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1993.tb04702.x)).
Much of stock momentum is **industry momentum** (Moskowitz & Grinblatt, *JF* 1999,
[Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00146)). Time-series
(own-trend) momentum holds across 58 futures markets with 1-12 month persistence that partly
reverses later (Moskowitz, Ooi & Pedersen, *JFE* 2012,
[AQR](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum)). Crash risk
as in §1. *Grade:* A. *Takeaway:* skip the last month; require sector strength too.

**52-week-high proximity (George-Hwang).** *Goal:* anchoring: investors under-react to good
news near a stock's 52-week high. *Method:* rank on price / 52-week high; buy the nearest.
*Evidence:* nearness to the 52-week high **dominates and improves on past returns** in
forecasting returns, and its forecasts **do not reverse** in the long run (George & Hwang,
*JF* 2004, [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00695.x),
abstract). Later work reports weaker results after 2000 **(summary)**. *Grade:* A. *Takeaway:*
"near the high" is a better entry condition than "up a lot".

**Trend following on single stocks (Wilcox-Crittenden).** *Goal:* capture the rare, very
large winners (right skew). *Method:* buy a stock at an **all-time high**, exit on a **10×ATR
trailing stop**, 0.5% round-turn costs. *Evidence:* 18,000+ trades over 22 years; win rate
**49.3%**; **17% of trades gained 50%+** (Wilcox & Crittenden 2005,
[PDF](https://www.cis.upenn.edu/~mkearns/finread/trend.pdf), **(summary)**). A 2024 update
(survivorship-free, 1950-2024, 66,000+ trades) finds **fewer than 7% of trades generate most
of the profit**; a portfolio version 1991-2024: 15.19% CAGR, 6.18% alpha gross of fees,
hard to implement below ~$1M (Zarattini, Pagani & Wilcox, [SSRN 5084316](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5084316),
via [Concretum](https://concretumgroup.com/does-trend-following-still-work-on-stocks/)). *Grade:* B.
*Takeaway:* the edge lives in the tail; **early fixed profit-taking destroys it**.

**Moving-average distance / MA timing on stocks.** *Goal:* trend at the stock level.
*Evidence:* the distance between the 21- and 200-day MAs predicts cross-sectional returns
beyond momentum and 52-week highs, ~9% annual value-weighted hedge alphas, surviving
institutional costs, **stronger on the long side** (Avramov, Kaplanski & Subrahmanyam, *RFE*
2021, [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111334), 1977-2018). MA
timing applied to volatility-sorted portfolios beats buy-and-hold, most for high-volatility
stocks (Han, Yang & Zhou, *JFQA* 2013, [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1656460)).
*Grade:* A. *Takeaway:* price above a rising long MA is the best-supported single filter.

Also considered: **Clenow, *Stocks on the Move*** (S&P 500 names ranked by 90-day regression
slope × R², new buys only while the S&P 500 is above its 200-day MA, ATR-based sizing, exit
below the 100-day MA or after a >15% gap; [summary](https://teddykoker.com/2019/05/momentum-strategy-from-stocks-on-the-move-in-python/)).
Grade B (author's tests). Useful for its index filter and volatility sizing.

### 2.3 Synthesis: investment

- **Common:** (1) own trend up: price above a **rising** long MA (30-week/200-day/10-month);
  (2) relative strength vs the market, and industry strength; (3) near the 52-week high, not
  far below it; (4) a market filter (index above its long MA); (5) exits on trend failure
  (close below the long MA or a wide volatility trail), not on fixed targets.
- **Disagree:** breakout entry (Weinstein, O'Neil) vs no entry timing at all (Faber, momentum
  rebalance monthly); tight 7-8% loss cut (O'Neil) vs wide trails (Weinstein under the MA,
  Wilcox 10×ATR); fixed profit-taking at 20-25% (O'Neil) vs letting winners run (all
  trend-followers).
- **Implication:** the evidence is strongest for the *filter* (trend + RS + near highs) and
  the *trend-failure exit*; entry timing adds little over 6+ months, so it should be simple,
  and fixed targets should be small or absent. That clashes with the pipeline's
  target-based plans (see [`open-questions.md`](open-questions.md)).

---

## 3. Swing (3-12 weeks, daily chart)

### 3.1 Summary

| Strategy | Goal | Core rule | Evidence |
|---|---|---|---|
| Minervini trend template + VCP | Momentum leaders breaking out of tightening bases | 8-point MA/52-week template; buy the pivot of a volatility-contraction base | B/C (author's books and record) |
| O'Neil cup-with-handle / base breakouts | Breakout from a proper base | Buy the handle high; stop 7-8% or the handle low | B (Bulkowski's pattern statistics, IBD studies) |
| Darvas box | Breakout of a range near highs | Buy above the box top on volume; stop just under the box bottom; trail boxes | C (one trader's account) |
| Pullback to the 20/50-day MA in an uptrend | Buy temporary weakness in a trend | Wait for a pullback to a rising MA, buy the resumption | B/C (Raschke's Holy Grail, practitioner) |
| Relative-strength leaders | Momentum | Hold the strongest stocks vs the index | A via momentum (§2) |
| Post-earnings drift / earnings-gap continuation | Under-reaction to news | Buy after a strong earnings reaction | A historically; **decayed** for large caps |
| Donchian / Turtle channel breakout | Trend following | Buy an N-day high, 2N (ATR) stop, exit on an M-day low | B (futures); decayed on single-market tests |

### 3.2 Entries

**Minervini trend template + VCP.** *Goal:* buy stage-2 leaders just as supply dries up.
*Method:* trend template: price above the 150- and 200-day MAs; 150 > 200; 200-day rising
for at least 1 month (preferably 4-5); 50 > 150 and 200; price above the 50-day; at least
25-30% above the 52-week low; within 25% of the 52-week high (closer is better); high
relative strength ([ChartMill](https://www.chartmill.com/documentation/stock-screener/technical-analysis-trading-strategies/496-Mark-Minervini-Trend-Template-A-Step-by-Step-Guide-for-Beginners),
[Deepvue](https://deepvue.com/screener/minervini-trend-template/)). VCP: a base of 2-6
successively smaller pullbacks (e.g. 20%, 10%, 5%) with volume drying up, bought on the
break of the final tight pivot ([TraderLion](https://traderlion.com/technical-analysis/volatility-contraction-pattern/)).
*Evidence:* the author's books (*Trade Like a Stock Market Wizard*, 2013) and track record;
no independent systematic test of the VCP found. The template itself is close to the MA and
52-week-high effects in §2 (grade A there). *Grade:* B/C.

**O'Neil cup-with-handle / base breakouts.** *Goal:* breakout from a proper base. *Method:*
cup 7-65 weeks, U-shaped; handle at least 1 week in the upper half of the cup; buy a close
above the right rim (or the handle's down-trendline); stop at the handle low; measured-move
target (Bulkowski's version). *Evidence:* Bulkowski's bull-market sample of 913 "perfect
trades": average rise 54%, 5% break-even failure rate, throwback in 62%; but in a newer look
at 300 patterns (1990-March 2024), **47% dropped substantially within two months of the
breakout** (Bulkowski, [thepatternsite.com/cup.html](https://thepatternsite.com/cup.html)).
Patterns are identified by eye, after the fact, which inflates "perfect trade" statistics.
*Grade:* B. *Takeaway:* breakouts from bases work often enough to trade, but throwbacks and
failures are normal; the stop and the first weeks matter.

**Darvas box.** *Goal:* ride stocks making new highs, stacking "boxes". *Method:* buy when
price closes above the box top on rising volume; stop just under the box bottom; raise the
stop as new boxes form; only in rising markets
([CFI](https://corporatefinanceinstitute.com/resources/equities/darvas-box-theory/),
[Wikipedia](https://en.wikipedia.org/wiki/Nicolas_Darvas); Darvas, *How I Made $2,000,000 in
the Stock Market*, 1960). *Evidence:* one trader's 1950s account. *Grade:* C. *Takeaway:* a
clean, mechanical definition of "range near highs" and "stop under the range".

**Pullback to the 20/50-day MA (Raschke's Holy Grail).** *Goal:* join an established trend
at a better price. *Method:* ADX(14) > 30 and rising; price pulls back to the 20-period EMA;
**buy stop above the high of the bar that touched the EMA**; stop at the new swing low,
trailed ([Trading Setups Review](https://www.tradingsetupsreview.com/the-holy-grail-trading-setup/);
Raschke & Connors, *Street Smarts*, 1995). *Evidence:* book examples; no independent test
found. *Grade:* C. *Takeaway:* the entry is the *resumption*, not the touch: "reaching the EMA
is not an entry". ADX isn't available in the pipeline (see the swing draft).

**Relative-strength leaders.** Practitioner form (IBD RS rating, "L" in CAN SLIM) of
cross-sectional momentum; academic support is §2's momentum and industry-momentum evidence.
*Grade:* A for the effect, B for any specific rating.

**Post-earnings-announcement drift (PEAD) and earnings-gap continuation.** *Goal:*
under-reaction to earnings news. *Method:* buy after a positive surprise (SUE) or a strong
announcement-window return (EAR, the "earnings gap"), hold weeks to a quarter. *Evidence:*
drift is a delayed price response, not a risk premium (Bernard & Thomas, *JAR* 1989,
[IDEAS](https://ideas.repec.org/a/bla/joares/v27y1989ip1-36.html)). EAR sorts earned 6.3% a
year abnormal (vs 5.6% for SUE), but those returns are **concentrated around the next
earnings announcements** (a 3-day ~3.3%), not a smooth drift (Brandt et al. 2007,
[PDF](https://www.anderson.ucla.edu/documents/areas/fac/finance/ear.pdf), read). And PEAD has
**disappeared: non-existent for large stocks since 2006**, only recently gone for microcaps
(Martineau, *CFR* 2022, [SSRN 3111607](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607)).
*Grade:* A (for the decay). *Takeaway:* not a standalone swing edge for the liquid names this
pipeline trades; at most a condition (a strong post-earnings reaction inside the base).

**Donchian / Turtle channel breakout.** *Goal:* trend following. *Method:* N = 20-day
exponential average of true range; a unit risks 1% of equity per N; System 1 buys a 20-day
high, exits on a 10-day low; System 2 buys a 55-day high, exits on a 20-day low; stop 2N from
entry; add units every ½N (Faith, *The Original Turtle Trading Rules*,
[PDF](https://oxfordstrat.com/coasdfASD32/uploads/2016/01/turtle-rules.pdf), read).
*Evidence:* futures portfolio results of the 1980s; channel breakouts are among the rules
Sullivan et al. (§1) found to decay. On single stocks, the Wilcox-Crittenden results (§2)
are the closest test. *Grade:* B. *Takeaway:* ATR-based stops and sizing, and channel exits,
are portable; the entry needs a trend/RS filter on stocks.

### 3.3 Synthesis: swing

- **Common:** (1) stage-2 trend (price > rising 50/150/200-day MAs); (2) within ~25% of the
  52-week high, ideally much closer; (3) relative strength vs the market (and sector); (4)
  entry after **contraction** (a tight range, falling volume) at a well-defined level; (5) a
  stop just beyond the structure (box low, handle low, swing low, or ~2 ATR), and small
  (O'Neil's 7-8% is a ceiling); (6) exits: part at 2-3R / 20-25%, the rest trailed.
- **Disagree:** breakout (Minervini, O'Neil, Darvas, Turtle) vs pullback (Holy Grail, MA
  pullbacks). Both need the same trend filter; they differ only in *where* in the swing they
  enter. The bucket's `entry_style` already expresses this choice, so the swing draft keeps
  one filter and two entry variants.
- **Also disagree:** whether earnings drift is an edge (decayed; see Martineau).
- **Implication:** the strongest shared ingredients are the filters, not the pattern names.
  Pattern identification "by eye" (cups, VCPs) must be replaced by a numeric contraction test
  to be backtestable.

---

## 4. Short-term swing (2-10 trading days, daily chart)

### 4.1 Summary

| Strategy | Goal | Core rule | Evidence |
|---|---|---|---|
| Connors-Alvarez RSI(2) / Double 7s / 3-day pullback | Mean reversion inside an uptrend | Above the 200-day; buy an oversold close; exit on a close above the 5-day MA or a 7-day high | B (authors' tests); A for the reversal effect underneath |
| Raschke setups (Holy Grail, Turtle Soup, 80-20) | Trend resumption / failed-breakout reversal | Buy stop over the trigger bar; stop under the new extreme | C (book examples; several are intraday) |
| NR7 / inside-day breakouts | Volatility contraction → expansion | Trade the break of the narrowest range in 7 days | B/C; weak on stocks in Bulkowski's data |
| 3-day pullbacks in strong trends | Mean reversion | Three lower highs and lows above the 200-day | B (Connors-Alvarez) |
| Academic short-term reversal | Liquidity provision / over-reaction | Buy last week's/month's losers | A; strong decay and cost sensitivity |
| Gap-fill / gap-and-go | Overnight over-reaction or continuation | Fade or follow an opening gap | C on daily bars; academic work is on overnight vs intraday returns |

### 4.2 Entries

**Connors-Alvarez RSI(2) and relatives.** *Goal:* buy short-term oversold moves in stocks
that are in a long-term uptrend. *Method:* price above its 200-day SMA; RSI(2) below 5 (or
10); buy (on the close in the original); exit on a close above the 5-day SMA; the mirror for
shorts below the 200-day with RSI(2) above 95; **no stops**: Connors reports stops "hurt"
performance on stocks and indices in his tests ([StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2);
Connors & Alvarez, *Short Term Trading Strategies That Work*, 2008). Double 7s: above the
200-day, buy a close at a 7-day low, sell a close at a 7-day high. 3-Day High/Low (ETFs):
above the 200-day, below the 5-day, three consecutive lower highs and lows; exit on a close
above the 5-day ([summary](https://quantifiedstrategies.substack.com/p/larry-connors-3-day-highlow-method-4f3);
Connors & Alvarez, *High Probability ETF Trading*, 2009). Headline win rates of 65-75% are
widely quoted and **unverified** here. *Evidence on decay:* Alvarez (co-author) finds index
RSI(2) edges little changed since the mid-2000s ([blog](https://alvarezquanttrading.com/blog/mean-reversion-vs-trend-following-through-the-years/),
S&P 500 1957-2023, no costs), and for Russell 1000 stocks (RSI(2) < 5, exit RSI(2) > 70,
1995-2015) that "the edges shrunk ... [but not] to where it is not worth trading"
([blog](https://alvarezquanttrading.com/blog/the-health-of-stock-mean-reversion-readers-ideas/),
no costs). *Grade:* B. *Takeaway:* the most-tested daily-bar short-term setup; its enemies are
costs, gap risk without stops, and news-driven drops.

**Raschke setups.** Holy Grail (above, a 2-10 day trade on a pullback). **Turtle Soup:** a
new 20-day low, with the previous 20-day low at least 4 sessions old; buy stop back above that
prior low; stop under the new low ([summary](https://www.luxalgo.com/library/concept/turtle-soup/);
*Street Smarts*). **80-20:** a bar that opens in the top 20% of its range and closes in the
bottom 20%; the next day's trade is intraday ([MQL5](https://www.mql5.com/en/articles/2785)).
*Evidence:* book examples, no independent test found. *Grade:* C. *Fit here:* 80-20 is a day
trade (principle 7 excludes it); Turtle Soup's trigger and tight stop assume watching the
market intraday.

**NR7 / inside-day breakouts (Crabel).** *Goal:* volatility contraction precedes expansion.
*Method:* the day with the narrowest range of the last 7 (NR7), often combined with an
inside day; trade the break of its high/low, usually the next day via an opening-range
breakout (Crabel, *Day Trading with Short Term Price Patterns*, 1990;
[StockCharts](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/narrow-range-day-nr7)).
*Evidence:* Crabel's work is on pre-1990 futures. On stocks 1990-2013, Bulkowski finds upward
breakouts average **+7% with a 46% failure rate**, and in his target-exit test NR7 beats the
benchmark **only in downtrends, and not by much** ([thepatternsite.com/nr7.html](https://www.thepatternsite.com/nr7.html)).
*Grade:* B/C. *Takeaway:* contraction is a useful *condition* (it sets a tight stop), weak as
a standalone signal, and the classic version is intraday.

**Academic short-term reversal.** *Goal:* earn the premium for providing liquidity to
over-reacting or forced sellers. *Evidence:* negative first-order serial correlation of
monthly returns (Jegadeesh, *JF* 1990, [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1990.tb05110.x);
~2%/month reported for 1934-1987 **(summary)**); weekly reversal (Lehmann, *QJE* 1990).
**Costs:** reversal profits mostly vanish after costs in small caps, but restricted to large
caps with turnover control they earn **30-50 bp/week net** (de Groot, Huij & Zhou, *JBF* 2012,
[PDF](https://repub.eur.nl/pub/25718/AnotherLook_2011.pdf)). **Decay:** a simulated
contrarian strategy's average daily return fell from **0.57% in 1998 to 0.13% in 2007**
(Khandani & Lo, [MIT](https://web.mit.edu/Alo/www/Papers/august07.pdf)). **Regime:** returns
rise sharply with the VIX (Nagel, §1). **News:** reversal is for no-news moves (Chan; Da et al.,
§1). *Grade:* A. *Takeaway:* real but thin, cost-sensitive and decaying; best in liquid names,
on non-news moves, and larger in high-volatility regimes.

**Gap-fill / gap-and-go.** *Goal:* fade over-reaction at the open, or follow news gaps.
*Evidence:* academic work decomposes returns into overnight and intraday parts with
persistent opposite-signed patterns (Lou, Polk & Skouras, *JFE* 2019,
[PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)); momentum profits are earned
overnight. No clean evidence found for a daily-bar gap-fill or gap-and-go rule on stocks.
News gaps behave like the drift in Chan (2003). *Grade:* C for the trading rules. *Fit
here:* both are decided in the first minutes of the session, which the pipeline can't see
(no intraday data, runs after the close).

### 4.3 Synthesis: short-term swing

- **Common:** (1) trade *with* the long-term trend (above the 200-day) even when the entry is
  counter-trend short term; (2) enter on a short, sharp, **no-news** pullback (RSI(2) low,
  N-day low, 3 lower lows); (3) exit fast on the bounce (5-day MA, N-day high), with a time
  stop; (4) high win rate, small average win, fat left tail, so costs and gap risk decide
  the result.
- **Disagree:** mean reversion (Connors, academic reversal) vs short-term breakouts (NR7,
  Turtle Soup's failed breakout, gap-and-go); stops (Connors: none) vs tight structural stops
  (Raschke, Crabel). Breakout variants are mostly intraday and weakly evidenced on stocks.
- **Regime disagreement:** Connors switches mean reversion off below the 200-day; Nagel finds
  reversal pays most when VIX is high, i.e. in exactly those markets. Both can be true (a
  stock above its 200-day in a high-VIX market is the sweet spot); the draft keeps the
  stock-level trend rule and leaves the market rule as an open question.
- **Implication for this pipeline:** only the mean-reversion family survives the
  constraints: daily bars, limit/stop-limit entries placed hours after the signal, and exits
  watched on closes. A limit **below** the signal close is naturally robust to delay (it only
  fills on further weakness). But a small target with a wide stop gives reward:risk well
  below every bucket's minimum.

---

## 5. Across all three types

**What they share.**

1. **Trade with the higher-timeframe trend.** Every type's best-evidenced ingredient is a
   long-MA trend filter (Faber, Weinstein stage 2, MAD, Connors' 200-day, Minervini).
2. **Relative strength, including the sector.** Momentum is partly industry momentum;
   investment and swing require it, short swing uses it only as "don't buy laggards".
3. **Enter where risk is defined and small:** after contraction (base, box, tight range) or a
   short pullback, with the stop at the structure that would prove the idea wrong.
4. **Market regime filter:** new longs mostly off when the index is below its long MA.
5. **Volatility-based stops and sizing** (ATR multiples; Turtle N; Barroso-Santa-Clara).
6. **Cut losers fast, and use time stops** for trades that don't work.
7. **Avoid news you can't price:** earnings inside a short hold; news-driven drops for mean
   reversion.

**Where they genuinely disagree, and what it implies.**

| Axis | One side | Other side | Implication |
|---|---|---|---|
| Entry | Breakout (buy strength) | Pullback (buy weakness) | Same trend filter, different entry; map to the bucket's `entry_style` rather than pick one |
| Signal | Momentum (continuation) | Mean reversion (reversal) | Horizon decides: continuation at 3-12 months, reversal at 1 day-1 month; the short swing is the one mean-reversion strategy |
| Exits | Fixed targets (O'Neil 20-25%, Connors' 5-day MA) | Trailing / trend-failure exits (Weinstein, Turtle, Wilcox) | Trend edges live in the right tail, so trail; mean reversion edges live in the win rate, so take the bounce |
| Stops | Tight structural (O'Neil 7-8%, Raschke) | Wide or none (Connors, Wilcox 10×ATR) | Stop width must match the edge; a single `max_loss` cap per bucket suits breakouts, not mean reversion or long-term trend |
| Volatility regime | Trend wants calm, rising markets | Reversal pays most in turmoil (Nagel) | Regime filters differ per strategy |

**What this means for the pipeline.** The bucket profile (§4a) fixes limits per *reward
shape*, while these strategies need limits per *strategy*: a trend trade wants a wide stop and
no fixed target, a mean-reversion trade wants a small target and a high win rate. Those
conflicts, and the data and cadence gaps, are listed in [`open-questions.md`](open-questions.md).
