"""Compact price statistics from an Equibles ``GetStockPrices`` response.

Used by ``workspace_guard.py``: agents get these numbers instead of hundreds of raw
daily rows (the full response is still saved to ``raw/``). Pure arithmetic on the rows
the agent fetched, no other data source and no judgment.

All figures use the ``Close`` column (``High``/``Low`` for ranges and ATR). Trading-day
offsets: 1w = 5, 1m = 21, 3m = 63, 6m = 126, 12m = 252 bars.

For the technical agent (``with_levels``) it adds the chart-reading inputs: MA slopes and
the 30-week MA (stage analysis), MA order and extension in ATRs, ATR and Bollinger-width
contraction, volume accumulation/dry-up, RSI14 at each swing point, and (``relative``)
the relative-strength line of one ticker against another from two responses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

RETURN_OFFSETS = (("1w", 5), ("1m", 21), ("3m", 63), ("6m", 126), ("12m", 252))
SMAS = (20, 50, 200)
RS_OFFSETS = (("1m", 21), ("3m", 63), ("6m", 126), ("12m", 252))
BENCHMARKS = ("SPY", "IVV", "VOO")  # the market benchmark, in order of preference


@dataclass(frozen=True)
class Bar:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: float


def _num(s: str) -> float:
    return float(s.replace(",", "").replace("$", "").strip())


def parse(text: str) -> tuple[str, list[Bar]]:
    """(title line, bars oldest first). Raises ValueError if the table isn't there."""
    lines = text.splitlines()
    header = next((i for i, l in enumerate(lines) if l.startswith("|") and "Close" in l and "Date" in l), None)
    if header is None:
        raise ValueError("no price table")
    cols = [c.strip().lower() for c in lines[header].strip("|").split("|")]
    idx = {name: cols.index(name) for name in ("date", "open", "high", "low", "close", "volume")}
    bars = []
    for line in lines[header + 2:]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        try:
            bars.append(Bar(date.fromisoformat(cells[idx["date"]]), _num(cells[idx["open"]]),
                            _num(cells[idx["high"]]), _num(cells[idx["low"]]), _num(cells[idx["close"]]),
                            _num(cells[idx["volume"]])))
        except (ValueError, IndexError):
            continue
    if not bars:
        raise ValueError("empty price table")
    bars.sort(key=lambda b: b.day)
    return next((l for l in lines if l.strip()), ""), bars


def _pct(a: float, b: float) -> float:
    return (a / b - 1) * 100


def atr(bars: list[Bar], n: int = 14) -> float | None:
    """Wilder's average true range."""
    if len(bars) < n + 1:
        return None
    trs = [max(b.high - b.low, abs(b.high - p.close), abs(b.low - p.close)) for p, b in zip(bars, bars[1:])]
    value = sum(trs[:n]) / n
    for tr in trs[n:]:
        value = (value * (n - 1) + tr) / n
    return value


def rsi(bars: list[Bar], n: int = 14) -> float | None:
    """Wilder's RSI on closes."""
    if len(bars) < n + 1:
        return None
    changes = [b.close - p.close for p, b in zip(bars, bars[1:])]
    gain = sum(c for c in changes[:n] if c > 0) / n
    loss = sum(-c for c in changes[:n] if c < 0) / n
    for c in changes[n:]:
        gain = (gain * (n - 1) + max(c, 0.0)) / n
        loss = (loss * (n - 1) + max(-c, 0.0)) / n
    if loss == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + gain / loss)


def _ema(values: list[float], n: int) -> list[float]:
    k = 2.0 / (n + 1)
    out = [sum(values[:n]) / n]
    for v in values[n:]:
        out.append(out[-1] + k * (v - out[-1]))
    return out


def macd(bars: list[Bar], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[float, float, float] | None:
    """(MACD line, signal line, histogram) from EMAs of the closes; None when too few bars."""
    closes = [b.close for b in bars]
    if len(closes) < slow + signal:
        return None
    fast_e, slow_e = _ema(closes, fast), _ema(closes, slow)
    line = [f - s for f, s in zip(fast_e[slow - fast:], slow_e)]
    sig = _ema(line, signal)
    return line[-1], sig[-1], line[-1] - sig[-1]


def vwap(bars: list[Bar], n: int = 20) -> float | None:
    """Volume-weighted average of the typical price over the last n bars."""
    window = bars[-n:]
    vol = sum(b.volume for b in window)
    if len(window) < n or vol == 0:
        return None
    return sum((b.high + b.low + b.close) / 3 * b.volume for b in window) / vol


def relative_volume(bars: list[Bar], n: int = 20) -> float | None:
    """Last bar's volume over the mean volume of the n bars before it."""
    if len(bars) < n + 1:
        return None
    base = sum(b.volume for b in bars[-n - 1:-1]) / n
    return None if base == 0 else bars[-1].volume / base


def pivots(bars: list[Bar], k: int = 5, keep: int = 6) -> tuple[list[Bar], list[Bar]]:
    """Swing highs/lows: a bar whose high (low) is the extreme of the k bars on each side."""
    highs, lows = [], []
    for i in range(k, len(bars) - k):
        window = bars[i - k:i + k + 1]
        if bars[i].high == max(b.high for b in window):
            highs.append(bars[i])
        if bars[i].low == min(b.low for b in window):
            lows.append(bars[i])
    return highs[-keep:], lows[-keep:]


def weekly(bars: list[Bar]) -> list[Bar]:
    """ISO-week bars: first open, highest high, lowest low, last close, summed volume."""
    out: list[Bar] = []
    for b in bars:
        if out and out[-1].day.isocalendar()[:2] == b.day.isocalendar()[:2]:
            w = out[-1]
            out[-1] = Bar(b.day, w.open, max(w.high, b.high), min(w.low, b.low), b.close, w.volume + b.volume)
        else:
            out.append(b)
    return out


def ticker_of(title: str) -> str | None:
    """The ticker in an Equibles title line ("Daily prices for AAPL (Apple Inc.):")."""
    m = re.search(r"prices for ([A-Za-z0-9.^\-]+)", title)
    return m.group(1).upper() if m else None


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _direction(change: float) -> str:
    return "rising" if change > 0 else "falling" if change < 0 else "flat"


def _sma_slope(closes: list[float], n: int, back: int, label: str, unit: str) -> tuple[str, float | None]:
    """'<label> X vs Y <back> <unit> earlier (+a%, rising)' and the current value."""
    if len(closes) < n + back:
        return f"{label} slope n/a (needs {n + back} {unit}, have {len(closes)})", \
            (_mean(closes[-n:]) if len(closes) >= n else None)
    now, then = _mean(closes[-n:]), _mean(closes[-n - back:-back])
    ch = _pct(now, then)
    return f"{label} {_f(now)} vs {_f(then)} {back} {unit} earlier ({ch:+.2f}%, {_direction(ch)})", now


def trend_lines(bars: list[Bar]) -> list[str]:
    """MA slopes, the 30-week MA (Weinstein), MA order and extension from SMA50 in ATRs."""
    closes = [b.close for b in bars]
    wcloses = [w.close for w in weekly(bars)]
    last = bars[-1].close
    s50_txt, s50 = _sma_slope(closes, 50, 20, "SMA50", "bars")
    s200_txt, s200 = _sma_slope(closes, 200, 20, "SMA200", "bars")
    w30_txt, w30 = _sma_slope(wcloses, 30, 5, "30-week MA", "weeks")
    if w30 is not None:
        w30_txt += f", last weekly close {_pct(wcloses[-1], w30):+.2f}% vs it"
    out = [f"Trend: {s50_txt}; {s200_txt}; {w30_txt} (weekly closes; the last week may be partial)."]
    ranked = [("close", last), ("SMA50", s50), ("30-week MA", w30), ("SMA200", s200)]
    known = sorted(((n, v) for n, v in ranked if v is not None), key=lambda x: -x[1])
    missing = [n for n, v in ranked if v is None]
    order = " > ".join(f"{n} {_f(v)}" for n, v in known) + (f" ({', '.join(missing)} n/a)" if missing else "")
    a = atr(bars)
    ext = f"; close vs SMA50: {(last - s50) / a:+.2f} ATR14" if a and s50 is not None else ""
    out.append(f"MA order, highest first: {order}{ext}.")
    return out


def bollinger_widths(bars: list[Bar], n: int = 20, k: float = 2.0) -> list[float]:
    """Bollinger band width (upper − lower) as % of the middle band, one per bar from bar n."""
    closes = [b.close for b in bars]
    out = []
    for i in range(n, len(closes) + 1):
        w = closes[i - n:i]
        m = _mean(w)
        sd = (sum((x - m) ** 2 for x in w) / n) ** 0.5
        out.append(2 * k * sd / m * 100 if m else 0.0)
    return out


def volatility_line(bars: list[Bar], lookback: int = 126) -> str:
    """ATR14 now vs 20 bars earlier; Bollinger(20,2) width and its percentile over lookback."""
    parts = []
    a_now, a_then = atr(bars), atr(bars[:-20]) if len(bars) > 20 else None
    if a_now is not None and a_then:
        parts.append(f"ATR14 {_f(a_now)} vs {_f(a_then)} 20 bars earlier (ratio {a_now / a_then:.2f})")
    else:
        parts.append("ATR14 trend n/a (needs 35 bars)")
    widths = bollinger_widths(bars)
    if len(widths) >= 20:
        cur, win = widths[-1], widths[-lookback:]
        pctile = sum(1 for w in win if w < cur) / len(win) * 100
        parts.append(f"Bollinger(20,2) width {cur:.2f}% of SMA20; over the last {len(win)} bars low "
                     f"{min(win):.2f}%, high {max(win):.2f}%, current at the {pctile:.0f}th percentile "
                     f"(share of those bars with a narrower band)")
    else:
        parts.append("Bollinger width percentile n/a (needs 39 bars)")
    return "Volatility: " + "; ".join(parts) + "."


def volume_line(bars: list[Bar], n: int = 50, recent: int = 10, heaviest: int = 3) -> str:
    """Average volume, recent dry-up, up/down volume ratio and the heaviest bars of the last n."""
    if len(bars) < n + 1:
        return f"Volume: n/a (needs {n + 1} bars, have {len(bars)})."
    pairs = list(zip(bars[-n - 1:-1], bars[-n:]))
    avg = _mean([b.volume for _, b in pairs])
    rec = _mean([b.volume for b in bars[-recent:]])
    up = sum(b.volume for p, b in pairs if b.close > p.close)
    down = sum(b.volume for p, b in pairs if b.close < p.close)
    ud = f"{up / down:.2f}" if down else "n/a (no down-close bars)"
    top = sorted(pairs, key=lambda pb: -pb[1].volume)[:heaviest]
    heavy = ", ".join(f"{b.day} ({_pct(b.close, p.close):+.2f}%, {b.volume / avg:.2f}x)" for p, b in top) \
        if avg else "n/a"
    ratio = f" ({rec / avg:.2f}x the {n}-bar average)" if avg else ""
    return (f"Volume: {n}-bar average {avg:,.0f}; last {recent} bars average {rec:,.0f}{ratio}. "
            f"Up/down volume, last {n} bars: {ud} (volume on up-close bars / volume on down-close bars). "
            f"Heaviest bars of the last {n} (close change, x the {n}-bar average): {heavy}.")


def relative(name: str, bars: list[Bar], bench_name: str, bench_bars: list[Bar],
             window: int = 252, pullback_window: int = 126) -> str | None:
    """Relative strength of ``name`` against ``bench_name`` on their common dates.

    RS line = close / benchmark close. Return differences are percentage points over the
    same common dates. None when fewer than 22 common dates."""
    bench = {b.day: b.close for b in bench_bars}
    common = [(b.day, b.close, bench[b.day]) for b in bars if bench.get(b.day) and b.close]
    if len(common) < 22:
        return None
    d_last, s_last, m_last = common[-1]
    diffs = []
    for label, n in RS_OFFSETS:
        if len(common) > n:
            _, s0, m0 = common[-1 - n]
            diffs.append(f"{label} {_pct(s_last, s0) - _pct(m_last, m0):+.2f} pp")
        else:
            diffs.append(f"{label} n/a")
    rs = [s / m for _, s, m in common]
    win, days = rs[-window:], [d for d, _, _ in common][-window:]
    hi = max(range(len(win)), key=lambda i: (win[i], i))
    lo = min(range(len(win)), key=lambda i: (win[i], -i))
    recent_from = len(win) - 5
    closes_win = [s for _, s, _ in common][-window:]
    price_hi = max(range(len(closes_win)), key=lambda i: (closes_win[i], i))
    ma = f"{_pct(rs[-1], _mean(rs[-50:])):+.2f}%" if len(rs) >= 50 else "n/a (needs 50 common dates)"
    text = (f"Relative strength, {name} vs {bench_name} (RS line = {name} close / {bench_name} close, "
            f"{len(common)} common dates {common[0][0]} to {d_last}): {name} return minus {bench_name} "
            f"return {', '.join(diffs)}. RS line over the last {len(win)} common dates: high on {days[hi]} "
            f"(last value {_pct(win[-1], win[hi]):+.2f}% from it), low on {days[lo]} (last value "
            f"{_pct(win[-1], win[lo]):+.2f}% from it); new RS high in the last 5 dates: "
            f"{'yes' if hi >= recent_from else 'no'}; new RS low in the last 5 dates: "
            f"{'yes' if lo >= recent_from else 'no'}. RS line vs its 50-date mean: {ma}. {name} closing "
            f"high over the same dates: {days[price_hi]}.")
    pw = common[-pullback_window:]
    peak, worst = 0, (0.0, 0, 0)
    for i in range(len(pw)):
        if pw[i][2] > pw[peak][2]:
            peak = i
        dd = _pct(pw[i][2], pw[peak][2])
        if dd < worst[0]:
            worst = (dd, peak, i)
    if worst[0] < 0:
        dd, p, t = worst
        text += (f" {bench_name}'s deepest pullback in the last {len(pw)} common dates: {dd:+.2f}% "
                 f"({_f(pw[p][2])} on {pw[p][0]} to {_f(pw[t][2])} on {pw[t][0]}); {name} over the same "
                 f"dates: {_pct(pw[t][1], pw[p][1]):+.2f}% ({_f(pw[p][1])} to {_f(pw[t][1])}).")
    else:
        text += f" {bench_name} had no pullback in the last {len(pw)} common dates."
    return text


def relative_blocks(subject: str, series: dict[str, list[Bar]], new: str) -> list[str]:
    """Relative-strength blocks for the pairs that involve ``new`` (the ticker just fetched).

    Pairs: the subject against every other ticker fetched (the market benchmark, its
    sector ETF), and every other non-benchmark ticker against the market benchmark (the
    sector ETF vs SPY). Computed when the later of the two tickers arrives."""
    subject, new = subject.upper(), new.upper()
    bench = next((b for b in BENCHMARKS if b in series), None)
    pairs = []
    for other in sorted(series):
        if other == subject:
            continue
        pairs.append((subject, other))
        if bench and other != bench:
            pairs.append((other, bench))
    out = []
    for a, b in dict.fromkeys(pairs):
        if new in (a, b) and a in series and b in series:
            block = relative(a, series[a], b, series[b])
            if block:
                out.append(block)
    return out


def _f(x: float) -> str:
    return f"{x:,.2f}"


def summary(text: str, *, raw_file: str, with_levels: bool = False) -> str:
    title, bars = parse(text)
    last = bars[-1]
    lines = [
        f"{title.rstrip(':')}: statistics computed from {len(bars)} daily bars, "
        f"{bars[0].day} to {last.day}. Full bars: {raw_file} (read it only if you need individual rows).",
        f"Last close: {_f(last.close)} on {last.day} (high {_f(last.high)}, low {_f(last.low)}).",
    ]
    rets = []
    for label, n in RETURN_OFFSETS:
        if len(bars) > n:
            base = bars[-1 - n]
            rets.append(f"{label} {_pct(last.close, base.close):+.2f}% (from {_f(base.close)} on {base.day})")
        else:
            rets.append(f"{label} n/a (only {len(bars)} bars)")
    prior_year = [b for b in bars if b.day.year < last.day.year]
    if prior_year:
        base = prior_year[-1]
        rets.append(f"YTD {_pct(last.close, base.close):+.2f}% (from {_f(base.close)} on {base.day})")
    else:
        rets.append("YTD n/a (no bar from the prior year fetched)")
    lines.append("Returns: " + "; ".join(rets) + ".")
    smas = []
    for n in SMAS:
        if len(bars) >= n:
            m = sum(b.close for b in bars[-n:]) / n
            smas.append(f"SMA{n} {_f(m)} (close {_pct(last.close, m):+.2f}% vs it)")
        else:
            smas.append(f"SMA{n} n/a (needs {n} bars, have {len(bars)})")
    lines.append("Moving averages (mean of every close in the window): " + "; ".join(smas) + ".")
    year = bars[-252:]
    hi_c, lo_c = max(year, key=lambda b: b.close), min(year, key=lambda b: b.close)
    hi, lo = max(year, key=lambda b: b.high), min(year, key=lambda b: b.low)
    lines.append(
        f"Range over the last {len(year)} bars: closing high {_f(hi_c.close)} ({hi_c.day}), closing low "
        f"{_f(lo_c.close)} ({lo_c.day}); intraday high {_f(hi.high)} ({hi.day}), intraday low {_f(lo.low)} "
        f"({lo.day}). Last close is {_pct(last.close, hi_c.close):+.2f}% from the closing high and "
        f"{_pct(last.close, lo_c.close):+.2f}% from the closing low.")
    a = atr(bars)
    recent = bars[-20:]
    dollar = sum(b.close * b.volume for b in recent) / len(recent)
    lines.append(
        (f"ATR14 {_f(a)} ({a / last.close * 100:.2f}% of the last close). " if a is not None else "ATR14 n/a. ")
        + f"Average daily dollar volume, last {len(recent)} bars: ${dollar / 1e6:,.1f}M.")
    r, m, v, rv = rsi(bars), macd(bars), vwap(bars), relative_volume(bars)
    lines.append("Indicators: "
                 + (f"RSI14 {r:.1f}" if r is not None else "RSI14 n/a")
                 + (f"; MACD(12,26,9) line {m[0]:,.2f}, signal {m[1]:,.2f}, histogram {m[2]:+,.2f}"
                    if m is not None else "; MACD n/a")
                 + (f"; VWAP20 {_f(v)} (close {_pct(last.close, v):+.2f}% vs it)" if v is not None else "; VWAP20 n/a")
                 + (f"; relative volume {rv:.2f}x (last bar vs its 20-bar average)" if rv is not None
                    else "; relative volume n/a") + ".")
    if with_levels:
        lines += trend_lines(bars)
        lines.append(volatility_line(bars))
        lines.append(volume_line(bars))
        highs, lows = pivots(bars)
        index = {b.day: i for i, b in enumerate(bars)}

        def at(b: Bar, level: float) -> str:
            r_at = rsi(bars[:index[b.day] + 1])
            return f"{_f(level)} ({b.day}, RSI14 {r_at:.1f})" if r_at is not None else f"{_f(level)} ({b.day})"

        lines.append("Swing highs (5 bars each side), most recent last: "
                     + (", ".join(at(b, b.high) for b in highs) or "none") + ".")
        lines.append("Swing lows (5 bars each side), most recent last: "
                     + (", ".join(at(b, b.low) for b in lows) or "none") + ".")
        weeks = weekly(bars)[-104:]
        lines.append(f"Weekly bars (last {len(weeks)} weeks; date = last trading day of the week):")
        lines.append("| Week to | Open | High | Low | Close | Volume |")
        lines.append("|---|---|---|---|---|---|")
        lines += [f"| {w.day} | {_f(w.open)} | {_f(w.high)} | {_f(w.low)} | {_f(w.close)} | {w.volume:,.0f} |"
                  for w in weeks]
    return "\n".join(lines)
