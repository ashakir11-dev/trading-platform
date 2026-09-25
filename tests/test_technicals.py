"""Locally computed technicals, checked against hand-computed values."""

from datetime import date, datetime, timedelta, timezone

import pytest

from trading_pipeline.data import technicals as ta
from trading_pipeline.data.base import PriceBar

approx = pytest.approx


def bar(d: date, o, h, l, c, v=1000.0) -> PriceBar:
    return PriceBar(ts=datetime(d.year, d.month, d.day, 20, 0, tzinfo=timezone.utc), open=o, high=h, low=l, close=c,
                    volume=v)


def trading_days(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def test_sma_and_ema():
    assert ta.sma([1, 2, 3, 4, 5], 3) == [None, None, 2, 3, 4]
    # seed = SMA(1,2,3) = 2 at index 2; alpha = 0.5 -> 3, 4
    assert ta.ema([1, 2, 3, 4, 5], 3) == [None, None, 2, 3, 4]
    assert ta.ema([1, 2], 3) == [None, None]


def test_rsi_wilder():
    # changes +1, -1, +2, +1 ; n=3: avg gain 1, avg loss 1/3 -> RS 3 -> 75
    # next: gain (1*2+1)/3 = 1, loss (1/3*2+0)/3 = 2/9 -> RS 4.5 -> 100 - 100/5.5
    out = ta.rsi([10, 11, 10, 12, 13], 3)
    assert out[:3] == [None, None, None]
    assert out[3] == approx(75.0)
    assert out[4] == approx(100 - 100 / 5.5)
    assert ta.rsi([1, 2, 3, 4, 5], 3)[-1] == 100.0  # no losses


def test_macd_small_periods():
    # fast=2: seed 1.5 @1, alpha 2/3 -> 3.16667, 6.38889, 12.79630
    # slow=3: seed 2.33333 @2, alpha 1/2 -> 5.16667, 10.58333
    # line: .83333, 1.22222, 2.21296 ; signal(2): seed 1.02778 @3 -> 1.81790 ; hist .39506
    line, sig, hist = ta.macd([1, 2, 4, 8, 16], fast=2, slow=3, signal=2)
    assert line[:2] == [None, None]
    assert line[2:] == approx([0.83333, 1.22222, 2.21296], abs=1e-4)
    assert sig[:3] == [None, None, None]
    assert sig[3:] == approx([1.02778, 1.81790], abs=1e-4)
    assert hist[4] == approx(0.39506, abs=1e-4)


def test_atr_wilder_seeded_like_equibles():
    d = trading_days(date(2026, 1, 5), 4)
    bars = [bar(d[0], 9, 10, 8, 9), bar(d[1], 9, 11, 9, 10), bar(d[2], 10, 12, 9, 11), bar(d[3], 11, 11, 10, 10.5)]
    # TR = 2, 2, 3, 1 ; seed (2+2+3)/3 @2 ; next (7/3*2 + 1)/3 = 17/9
    assert ta.true_range(bars) == [2, 2, 3, 1]
    assert ta.atr(bars, 3) == approx([None, None, 7 / 3, 17 / 9])


def test_bollinger_population_sd():
    lower, mid, upper = ta.bollinger([1, 2, 3], 3, 2.0)
    sd = (2 / 3) ** 0.5
    assert mid[2] == 2 and upper[2] == approx(2 + 2 * sd) and lower[2] == approx(2 - 2 * sd)
    assert upper[:2] == [None, None]


def test_average_volume_and_52_week():
    days = trading_days(date(2025, 1, 6), 300)
    bars = [bar(d, 100, 100 + i % 7, 90 - i % 5, 95, v=float(i)) for i, d in enumerate(days)]
    assert ta.average_volume(bars, 20) == approx(sum(range(280, 300)) / 20)
    assert ta.average_volume(bars[:5], 20) is None
    r = ta.fifty_two_week(bars)
    assert r["high"] == 106 and r["low"] == 86 and r["full_year"]
    assert ta.fifty_two_week(bars[:30])["full_year"] is False


def test_floor_pivots():
    p = ta.floor_pivots(110, 100, 105)
    assert p == approx({"p": 105, "r1": 110, "s1": 100, "r2": 115, "s2": 95, "r3": 120, "s3": 90})


def test_swing_points_fractals():
    highs = [3, 4, 9, 5, 4, 6, 8, 7, 5, 6]
    days = trading_days(date(2026, 3, 2), len(highs))
    bars = [bar(d, h - 1, h, h - 2, h - 1) for d, h in zip(days, highs)]
    sh, sl = ta.swing_points(bars, 2)
    assert [(s["date"], s["price"]) for s in sh] == [(days[2].isoformat(), 9), (days[6].isoformat(), 8)]
    assert [(s["date"], s["price"]) for s in sl] == [(days[4].isoformat(), 2)]
    # the newest k bars can't be confirmed swings
    assert all(s["date"] < days[-2].isoformat() for s in sh + sl)


def test_nearest_levels():
    assert ta.nearest_levels(100, [90, 95, 105, 120]) == {"support": 95, "resistance": 105}
    assert ta.nearest_levels(100, [110]) == {"support": None, "resistance": 110}


def test_weekly_bars_week_ending_friday():
    # Mon 2026-09-14 .. Fri 09-18, then Mon 09-21, Tue 09-22 (partial week)
    days = trading_days(date(2026, 9, 14), 7)
    daily = [bar(d, 10 + i, 12 + i, 9 + i, 11 + i, v=100) for i, d in enumerate(days)]
    weeks = ta.weekly_bars(daily)
    assert len(weeks) == 2
    w1, w2 = weeks
    assert (w1.open, w1.high, w1.low, w1.close, w1.volume) == (10, 16, 9, 15, 500)
    assert w1.ts == daily[4].ts
    assert (w2.open, w2.high, w2.low, w2.close, w2.volume) == (15, 18, 14, 17, 200)
    assert w2.ts == daily[6].ts


def test_completed_period_hlc():
    days = trading_days(date(2026, 9, 14), 8)  # Mon 14 .. Wed 23
    daily = [bar(d, 10, 20 + i, 5 + i, 15 + i) for i, d in enumerate(days)]
    wk = ta.completed_period_hlc(daily, "week", date(2026, 9, 23))
    assert (wk["start"], wk["end"], wk["high"], wk["low"], wk["close"]) == ("2026-09-14", "2026-09-18", 24, 5, 19)
    # Friday's bar completes its own week
    wk = ta.completed_period_hlc(daily[:5], "week", date(2026, 9, 18))
    assert wk["end"] == "2026-09-18"
    # prior day = the newest (closed) bar
    assert ta.completed_period_hlc(daily, "day", date(2026, 9, 23))["close"] == 22
    # September is still running, August has no bars
    assert ta.completed_period_hlc(daily, "month", date(2026, 9, 23)) is None
    assert ta.completed_period_hlc(daily, "month", date(2026, 10, 1))["end"] == "2026-09-23"


def test_indicator_summary_on_a_trend():
    days = trading_days(date(2025, 6, 2), 250)
    bars = [bar(d, i, i + 1, i - 1, float(i), v=1000) for i, d in enumerate(days, start=1)]
    s = ta.indicator_summary(bars)
    assert s["close"] == 250 and s["bars_used"] == 250
    assert s["sma"]["20"] == approx(240.5) and s["sma"]["50"] == approx(225.5) and s["sma"]["200"] == approx(150.5)
    assert s["rsi14"] == 100.0
    assert s["atr14"] == approx(2.0)
    assert s["macd"]["line"] > 0
    assert s["volume"]["rel_to_avg20"] == 1.0
    assert len(s["recent"]) == 10 and s["recent"][-1]["date"] == days[-1].isoformat()
    assert ta.indicator_summary([]) == {}
