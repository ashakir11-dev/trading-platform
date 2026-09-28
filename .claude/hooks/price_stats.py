"""Compact price statistics from an Equibles ``GetStockPrices`` response.

Used by ``workspace_guard.py``: agents get these numbers instead of hundreds of raw
daily rows (the full response is still saved to ``raw/``). Pure arithmetic on the rows
the agent fetched, no other data source and no judgment.

All figures use the ``Close`` column (``High``/``Low`` for ranges and ATR). Trading-day
offsets: 1w = 5, 1m = 21, 3m = 63, 6m = 126, 12m = 252 bars.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

RETURN_OFFSETS = (("1w", 5), ("1m", 21), ("3m", 63), ("6m", 126), ("12m", 252))
SMAS = (20, 50, 200)


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
        highs, lows = pivots(bars)
        lines.append("Swing highs (5 bars each side), most recent last: "
                     + (", ".join(f"{_f(b.high)} ({b.day})" for b in highs) or "none") + ".")
        lines.append("Swing lows (5 bars each side), most recent last: "
                     + (", ".join(f"{_f(b.low)} ({b.day})" for b in lows) or "none") + ".")
        weeks = weekly(bars)[-104:]
        lines.append(f"Weekly bars (last {len(weeks)} weeks; date = last trading day of the week):")
        lines.append("| Week to | Open | High | Low | Close | Volume |")
        lines.append("|---|---|---|---|---|---|")
        lines += [f"| {w.day} | {_f(w.open)} | {_f(w.high)} | {_f(w.low)} | {_f(w.close)} | {w.volume:,.0f} |"
                  for w in weeks]
    return "\n".join(lines)
