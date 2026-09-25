"""Pre-flight data check (`trading-pipeline check`).

Calls every data provider once for a known ticker and sector, with no LLM involved, and
reports what came back. The adapters were built from Equibles' open-source code; a format
difference on the hosted server does not raise, it silently yields empty data. This check
makes that visible before a run spends model calls on half-empty prompts.

Each result is OK, WARN (usable but degraded, e.g. a documented gap) or FAIL (a data type
the pipeline depends on came back empty).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Literal

from .data.base import DataProviders, DataSnapshot

Status = Literal["OK", "WARN", "FAIL"]


@dataclass
class CheckResult:
    component: str
    status: Status
    detail: str


def _note(s: DataSnapshot) -> str:
    return (s.note or "")[:160]


async def _guard(component: str, fn: Callable[[], Awaitable[CheckResult]]) -> CheckResult:
    try:
        return await fn()
    except Exception as e:  # a provider crash is a failure, not a crash of the check
        return CheckResult(component, "FAIL", f"{type(e).__name__}: {e}"[:200])


async def run_checks(data: DataProviders, as_of: datetime, *, ticker: str = "AAPL",
                     sector: str = "Health Care") -> list[CheckResult]:
    t = ticker.upper()

    async def fundamentals() -> CheckResult:
        s = await data.fundamentals.fundamentals(t, as_of)
        facts = (s.payload or {}).get("facts", []) if not s.is_gap else []
        if not facts:
            return CheckResult("fundamentals", "FAIL", f"no facts for {t}. {_note(s)}")
        concepts = sorted({f["concept"] for f in facts})
        return CheckResult("fundamentals", "OK", f"{len(facts)} facts across {len(concepts)} concepts for {t}")

    async def prices() -> CheckResult:
        bars = await data.prices.bars(t, (as_of - timedelta(days=30)).date(), as_of)
        if not bars:
            return CheckResult("prices", "FAIL", f"no daily bars for {t} in the last 30 days")
        return CheckResult("prices", "OK", f"{len(bars)} daily bars, last {bars[-1].ts.date()} close {bars[-1].close}")

    async def technicals() -> CheckResult:
        ind = await data.prices.indicators(t, as_of)
        piv = await data.prices.pivots(t, as_of)
        bad = [s.kind for s in (ind, piv) if s.is_gap]
        if bad:
            return CheckResult("indicators/pivots", "FAIL", f"gap for {', '.join(bad)}: {_note(ind if ind.is_gap else piv)}")
        return CheckResult("indicators/pivots", "OK", "daily indicators and pivots computed")

    async def quote() -> CheckResult:
        s = await data.quotes.quote(t)
        if s.is_gap:
            return CheckResult("quote", "FAIL", _note(s))
        p: dict[str, Any] = s.payload or {}
        status: Status = "OK" if "live" in str(p.get("basis", "")).lower() and "not live" not in str(p.get("basis", "")) else "WARN"
        return CheckResult("quote", status, f"{p.get('price')} ({p.get('basis', 'unknown basis')})")

    async def overview() -> CheckResult:
        snaps = await data.sectors.market_overview(as_of)
        perf = next((s for s in snaps if s.kind == "sector_performance" and not s.is_gap), None)
        if perf is None:
            return CheckResult("market overview", "FAIL", _note(snaps[0]) if snaps else "no snapshots")
        sectors = (perf.payload or {}).get("sectors") or {}
        return CheckResult("market overview", "OK", f"benchmark + {len(sectors)} sector ETFs")

    async def screen() -> CheckResult:
        snaps = await data.sectors.sector_screen(sector, as_of)
        rows = [s for s in snaps if s.kind == "screen" and not s.is_gap]
        if not rows:
            gap = next((s for s in snaps if s.is_gap), None)
            return CheckResult("sector screen", "FAIL", f"no constituents for {sector}. {_note(gap) if gap else ''}")
        return CheckResult("sector screen", "OK", f"{len(rows)} constituents for {sector} ({', '.join(s.subject for s in rows[:5])}...)")

    async def breadth() -> CheckResult:
        s = await data.sectors.sector_breadth(sector, as_of)
        if s.is_gap:
            return CheckResult("sector breadth", "FAIL", _note(s))
        n = (s.payload or {}).get("constituents_with_prices")
        return CheckResult("sector breadth", "OK" if n else "WARN", f"{n} constituents with prices")

    async def filings() -> CheckResult:
        s = await data.filings.recent_filings(t, as_of - timedelta(days=365), as_of)
        rows = s.payload or [] if not s.is_gap else []
        if not rows:
            return CheckResult("filings", "FAIL", f"no filings for {t} in a year. {_note(s)}")
        return CheckResult("filings", "OK", f"{len(rows)} filings, newest {rows[0].get('form')} {rows[0].get('filed')}")

    async def events() -> CheckResult:
        s = await data.news.events(t, as_of - timedelta(days=180), as_of)
        rows = s.payload or [] if not s.is_gap else []
        if s.is_gap:
            return CheckResult("catalyst events", "FAIL", _note(s))
        return CheckResult("catalyst events", "OK" if rows else "WARN", f"{len(rows)} events in 180 days")

    async def earnings() -> CheckResult:
        s = await data.news.upcoming_earnings(t, as_of)
        if s.is_gap:
            return CheckResult("earnings date", "WARN", _note(s))
        p = s.payload or {}
        conf = "confirmed" if p.get("confirmed") else "estimated"
        return CheckResult("earnings date", "OK", f"next {p.get('next_earnings_date')} ({conf}; {p.get('basis', '')})"[:200])

    async def macro() -> CheckResult:
        snaps = await data.macro.macro(as_of)
        gaps = [s.kind for s in snaps if s.is_gap]
        kinds = sorted(s.kind for s in snaps if not s.is_gap)
        if not kinds:
            return CheckResult("macro", "FAIL", _note(snaps[0]) if snaps else "no snapshots")
        return CheckResult("macro", "WARN" if gaps else "OK", f"{', '.join(kinds)}" + (f"; gaps: {gaps}" if gaps else ""))

    checks = [("fundamentals", fundamentals), ("prices", prices), ("indicators/pivots", technicals),
              ("quote", quote), ("market overview", overview), ("sector screen", screen),
              ("sector breadth", breadth), ("filings", filings), ("catalyst events", events),
              ("earnings date", earnings), ("macro", macro)]
    return [await _guard(name, fn) for name, fn in checks]


def render_checks(results: list[CheckResult], *, ticker: str, sector: str, as_of: date) -> str:
    width = max(len(r.component) for r in results)
    lines = [f"Data check as of {as_of} (ticker {ticker.upper()}, sector {sector}):", ""]
    lines += [f"  {r.status:<4}  {r.component:<{width}}  {r.detail}" for r in results]
    fails = sum(r.status == "FAIL" for r in results)
    warns = sum(r.status == "WARN" for r in results)
    lines += ["", f"{len(results) - fails - warns} OK, {warns} WARN, {fails} FAIL"]
    if fails:
        lines.append("Fix FAILs before a run: agents would reason over missing data.")
    return "\n".join(lines)
