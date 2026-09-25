"""Technical indicators and support/resistance levels computed locally from price bars.

Pure functions over ``list[PriceBar]`` (or plain float lists), no I/O. Callers are
responsible for passing only bars dated at or before the run's ``as_of``; nothing here
looks at the clock. Series functions return a list aligned with the input, with
``None`` while the lookback window is still filling.

Conventions (chosen to match Equibles' own ``TechnicalIndicatorService`` where it has
the same indicator, so values line up with its GetAverageTrueRange/GetBollingerBands):

* EMA: seeded with the SMA of the first ``n`` values, then ``alpha = 2 / (n + 1)``.
* RSI: Wilder. The first average gain/loss is the simple mean of the first ``n``
  changes, then ``avg = (avg * (n - 1) + x) / n``. RSI is 100 when there are no losses.
* MACD: EMA(fast) - EMA(slow); signal is the EMA(signal) of the MACD line seeded with
  the SMA of its first ``signal`` values; histogram = MACD - signal.
* ATR: Wilder. TR[0] = high - low; the seed is the mean of TR[0..n-1] at index n-1.
* Bollinger: SMA(n) +/- k * population standard deviation (denominator n).
* Floor pivots: P = (H + L + C) / 3, R1 = 2P - L, S1 = 2P - H, R2 = P + (H - L),
  S2 = P - (H - L), R3 = H + 2(P - L), S3 = L - 2(H - P).
* Swing highs/lows (fractals): bar i is a swing high when its high is strictly above
  the ``k`` bars before it and at or above the ``k`` bars after it (mirror for lows).
  The newest ``k`` bars therefore can't be confirmed swings yet.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any

from .base import PriceBar

Series = list[float | None]


def weekly_bars(daily: Sequence[PriceBar]) -> list[PriceBar]:
    """Aggregate daily bars into Monday-Friday weeks (week ending Friday).

    Each weekly bar's ``ts`` is its last daily bar's ``ts``, so a week still in progress
    at ``as_of`` is a partial bar holding only the sessions already closed.
    """
    out: list[PriceBar] = []
    key = None
    for b in daily:
        k = _period_key(b.ts.date(), "week")
        if k != key:
            out.append(b.model_copy())
            key = k
        else:
            w = out[-1]
            out[-1] = PriceBar(ts=b.ts, open=w.open, high=max(w.high, b.high), low=min(w.low, b.low),
                               close=b.close, volume=w.volume + b.volume)
    return out


# --------------------------------------------------------------------------------------
# Moving averages and oscillators
# --------------------------------------------------------------------------------------


def sma(values: Sequence[float], n: int) -> Series:
    out: Series = [None] * len(values)
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= n:
            total -= values[i - n]
        if i >= n - 1:
            out[i] = total / n
    return out


def ema(values: Sequence[float | None], n: int) -> Series:
    """EMA seeded with the SMA of the first ``n`` non-None values (leading Nones are skipped)."""
    out: Series = [None] * len(values)
    start = next((i for i, v in enumerate(values) if v is not None), len(values))
    if len(values) - start < n:
        return out
    alpha = 2.0 / (n + 1)
    prev = sum(values[start:start + n]) / n  # type: ignore[arg-type]
    out[start + n - 1] = prev
    for i in range(start + n, len(values)):
        prev = prev + alpha * (values[i] - prev)  # type: ignore[operator]
        out[i] = prev
    return out


def rsi(closes: Sequence[float], n: int = 14) -> Series:
    out: Series = [None] * len(closes)
    if len(closes) <= n:
        return out
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    avg_gain = sum(max(c, 0.0) for c in changes[:n]) / n
    avg_loss = sum(max(-c, 0.0) for c in changes[:n]) / n

    def value(g: float, l: float) -> float:
        return 100.0 if l == 0 else 100.0 - 100.0 / (1.0 + g / l)

    out[n] = value(avg_gain, avg_loss)
    for i in range(n + 1, len(closes)):
        c = changes[i - 1]
        avg_gain = (avg_gain * (n - 1) + max(c, 0.0)) / n
        avg_loss = (avg_loss * (n - 1) + max(-c, 0.0)) / n
        out[i] = value(avg_gain, avg_loss)
    return out


def macd(closes: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[Series, Series, Series]:
    ef, es = ema(closes, fast), ema(closes, slow)
    line: Series = [f - s if f is not None and s is not None else None for f, s in zip(ef, es)]
    sig = ema(line, signal)
    hist: Series = [m - s if m is not None and s is not None else None for m, s in zip(line, sig)]
    return line, sig, hist


def true_range(bars: Sequence[PriceBar]) -> list[float]:
    out = []
    for i, b in enumerate(bars):
        if i == 0:
            out.append(b.high - b.low)
        else:
            pc = bars[i - 1].close
            out.append(max(b.high - b.low, abs(b.high - pc), abs(b.low - pc)))
    return out


def atr(bars: Sequence[PriceBar], n: int = 14) -> Series:
    tr = true_range(bars)
    out: Series = [None] * len(tr)
    if len(tr) < n:
        return out
    prev = sum(tr[:n]) / n
    out[n - 1] = prev
    for i in range(n, len(tr)):
        prev = (prev * (n - 1) + tr[i]) / n
        out[i] = prev
    return out


def bollinger(closes: Sequence[float], n: int = 20, k: float = 2.0) -> tuple[Series, Series, Series]:
    """(lower, middle, upper) with population standard deviation."""
    mid = sma(closes, n)
    lower: Series = [None] * len(closes)
    upper: Series = [None] * len(closes)
    for i, m in enumerate(mid):
        if m is None:
            continue
        window = closes[i - n + 1:i + 1]
        sd = math.sqrt(sum((x - m) ** 2 for x in window) / n)
        lower[i], upper[i] = m - k * sd, m + k * sd
    return lower, mid, upper


def average_volume(bars: Sequence[PriceBar], n: int = 20) -> float | None:
    if len(bars) < n:
        return None
    return sum(b.volume for b in bars[-n:]) / n


def fifty_two_week(bars: Sequence[PriceBar]) -> dict[str, Any] | None:
    """High/low of bar highs/lows over the 365 days ending at the newest bar."""
    if not bars:
        return None
    end = bars[-1].ts
    window = [b for b in bars if b.ts > end - timedelta(days=365)]
    hi = max(window, key=lambda b: b.high)
    lo = min(window, key=lambda b: b.low)
    return {"high": hi.high, "high_date": hi.ts.date().isoformat(),
            "low": lo.low, "low_date": lo.ts.date().isoformat(),
            "full_year": bars[0].ts <= end - timedelta(days=358)}


# --------------------------------------------------------------------------------------
# Support / resistance
# --------------------------------------------------------------------------------------


def floor_pivots(high: float, low: float, close: float) -> dict[str, float]:
    p = (high + low + close) / 3
    return {"p": p, "r1": 2 * p - low, "s1": 2 * p - high, "r2": p + (high - low), "s2": p - (high - low),
            "r3": high + 2 * (p - low), "s3": low - 2 * (high - p)}


def _period_key(d: date, period: str) -> tuple:
    if period == "day":
        return (d,)
    if period == "week":
        y, w, _ = d.isocalendar()
        return (y, w)
    if period == "month":
        return (d.year, d.month)
    if period == "quarter":
        return (d.year, (d.month - 1) // 3)
    if period == "year":
        return (d.year,)
    raise ValueError(f"unknown period {period!r}")


def _period_last_weekday(d: date, period: str) -> date:
    """Last Monday-Friday date of the period containing ``d``."""
    if period == "day":
        return d
    if period == "week":
        end = d + timedelta(days=6 - d.weekday())
    elif period == "month":
        end = (date(d.year + (d.month == 12), d.month % 12 + 1, 1)) - timedelta(days=1)
    elif period == "quarter":
        q_end_month = ((d.month - 1) // 3) * 3 + 3
        end = date(d.year + (q_end_month == 12), q_end_month % 12 + 1, 1) - timedelta(days=1)
    elif period == "year":
        end = date(d.year, 12, 31)
    else:
        raise ValueError(f"unknown period {period!r}")
    while end.weekday() >= 5:
        end -= timedelta(days=1)
    return end


def completed_period_hlc(daily: Sequence[PriceBar], period: str, as_of_date: date) -> dict[str, Any] | None:
    """High/low/close of the most recent *completed* period (day/week/month/quarter/year).

    ``daily`` must be daily bars already cut at ``as_of``. The period holding the newest
    bar counts as completed only once ``as_of_date`` is past its last calendar day or
    the newest bar is on its last weekday (e.g. Friday's bar closes the week).
    """
    if not daily:
        return None
    groups: dict[tuple, list[PriceBar]] = {}
    for b in daily:
        groups.setdefault(_period_key(b.ts.date(), period), []).append(b)
    keys = list(groups)
    last_day = daily[-1].ts.date()
    if period == "day":
        done = True
    else:
        end = _period_last_weekday(last_day, period)
        done = last_day >= end or _period_key(as_of_date, period) != keys[-1]
    if not done:
        keys = keys[:-1]
    if not keys:
        return None
    bars = groups[keys[-1]]
    return {"start": bars[0].ts.date().isoformat(), "end": bars[-1].ts.date().isoformat(),
            "high": max(b.high for b in bars), "low": min(b.low for b in bars), "close": bars[-1].close}


def swing_points(bars: Sequence[PriceBar], k: int = 2) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(swing highs, swing lows), oldest first, each ``{"date", "price"}``."""
    highs, lows = [], []
    for i in range(k, len(bars) - k):
        left, right, b = bars[i - k:i], bars[i + 1:i + k + 1], bars[i]
        if b.high > max(x.high for x in left) and b.high >= max(x.high for x in right):
            highs.append({"date": b.ts.date().isoformat(), "price": b.high})
        if b.low < min(x.low for x in left) and b.low <= min(x.low for x in right):
            lows.append({"date": b.ts.date().isoformat(), "price": b.low})
    return highs, lows


def nearest_levels(price: float, levels: Sequence[float]) -> dict[str, float | None]:
    below = [x for x in levels if x < price]
    above = [x for x in levels if x > price]
    return {"support": max(below) if below else None, "resistance": min(above) if above else None}


# --------------------------------------------------------------------------------------
# Compact payloads
# --------------------------------------------------------------------------------------


def _r(x: float | None, nd: int = 4) -> float | None:
    return None if x is None else round(x, nd)


def _last(series: Series) -> float | None:
    return series[-1] if series else None


def indicator_summary(bars: Sequence[PriceBar], *, recent: int = 10) -> dict[str, Any]:
    """Latest indicator values plus a short recent series; bars oldest first."""
    if not bars:
        return {}
    closes = [b.close for b in bars]
    ema12, ema26 = ema(closes, 12), ema(closes, 26)
    r = rsi(closes, 14)
    m_line, m_sig, m_hist = macd(closes)
    a = atr(bars, 14)
    bl, bm, bu = bollinger(closes, 20, 2.0)
    last = bars[-1]
    avg20 = average_volume(bars, 20)
    pct_b = None
    if bl[-1] is not None and bu[-1] is not None and bu[-1] != bl[-1]:
        pct_b = (last.close - bl[-1]) / (bu[-1] - bl[-1])
    tail = range(max(0, len(bars) - recent), len(bars))
    return {
        "date": last.ts.date().isoformat(),
        "bars_used": len(bars),
        "close": last.close,
        "sma": {str(n): _r(_last(sma(closes, n))) for n in (20, 50, 200)},
        "ema": {"12": _r(_last(ema12)), "26": _r(_last(ema26))},
        "rsi14": _r(_last(r), 2),
        "macd": {"line": _r(_last(m_line)), "signal": _r(_last(m_sig)), "hist": _r(_last(m_hist))},
        "atr14": _r(_last(a)),
        "atr14_pct": _r(a[-1] / last.close * 100, 2) if a[-1] is not None and last.close else None,
        "bollinger20_2": {"lower": _r(bl[-1]), "middle": _r(bm[-1]), "upper": _r(bu[-1]), "pct_b": _r(pct_b, 3)},
        "volume": {"last": last.volume, "avg20": _r(avg20, 0),
                   "rel_to_avg20": _r(last.volume / avg20, 2) if avg20 else None},
        "range_52w": fifty_two_week(bars),
        "recent": [{"date": bars[i].ts.date().isoformat(), "close": bars[i].close, "rsi14": _r(r[i], 2),
                    "macd_hist": _r(m_hist[i])} for i in tail],
    }


def pivot_summary(bars: Sequence[PriceBar], daily: Sequence[PriceBar], periods: Sequence[str], as_of_date: date,
                  *, swings: int = 5, k: int = 2) -> dict[str, Any]:
    """Floor pivots from each completed prior period plus recent swing highs/lows.

    ``bars`` are the interval's bars (for swings); ``daily`` are the daily bars the period
    highs/lows come from. Both must already be cut at ``as_of``.
    """
    if not bars:
        return {}
    close = bars[-1].close
    floor = {}
    for period in periods:
        hlc = completed_period_hlc(daily, period, as_of_date)
        if hlc:
            floor[f"prior_{period}"] = {"from": hlc, **{k_: _r(v) for k_, v in floor_pivots(
                hlc["high"], hlc["low"], hlc["close"]).items()}}
    highs, lows = swing_points(bars, k)
    highs, lows = highs[-swings:], lows[-swings:]
    levels = [p["price"] for p in highs + lows]
    for piv in floor.values():
        levels += [v for key, v in piv.items() if key != "from" and v is not None]
    return {
        "date": bars[-1].ts.date().isoformat(),
        "close": close,
        "floor_pivots": floor,
        "swing_highs": highs,
        "swing_lows": lows,
        "fractal_k": k,
        "nearest": nearest_levels(close, levels),
    }
