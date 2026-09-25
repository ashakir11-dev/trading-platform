"""Test doubles: a scripted LLM and in-memory point-in-time data providers."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel

from trading_pipeline.data.base import DataProviders, DataSnapshot, PriceBar
from trading_pipeline.data.gaps import UnavailableFundamentals
from trading_pipeline.schemas import (
    Catalyst,
    CatalystCheck,
    CompanyDeepDiveOutput,
    FullReviewOutput,
    MarketScanOutput,
    ProcessReviewOutput,
    ReasoningFactor,
    RiskAssessment,
    SectorCall,
    SectorDeepDiveOutput,
    ShortlistEntry,
    Stage,
    StageGrade,
    StageReasoning,
    TechnicalOutput,
    TradePlan,
)

AS_OF = datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc)


def reasoning(summary: str = "ok", confidence: float = 0.7) -> StageReasoning:
    return StageReasoning(
        summary=summary,
        factors=[ReasoningFactor(direction="toward", factor="f", weight="medium", evidence="snap")],
        risks_considered=[RiskAssessment(risk="rates", category="macro", assessment="limited")],
        data_gaps=[],
        confidence=confidence,
    )


def plan(entry: float = 100.0, target: float = 120.0, stop: float = 90.0, direction="long") -> TradePlan:
    return TradePlan(direction=direction, entry_price=entry, entry_condition="close above", target_price=target,
                     stop_loss=stop, horizon="swing", chart_timeframe="1d", invalidation="close below stop")


def ticker_in(prompt: str) -> str:
    m = re.search(r"Company: (\w+)|Position: (\w+)", prompt)
    assert m, prompt[:200]
    return m.group(1) or m.group(2)


class ScriptedLLM:
    """Returns canned outputs per output type; records every prompt."""

    def __init__(self) -> None:
        self.calls: list[tuple[type[BaseModel], str, str]] = []
        self.handlers: dict[type[BaseModel], Callable[[str], BaseModel]] = {
            MarketScanOutput: lambda p: MarketScanOutput(
                market_summary="risk-on",
                sectors=[SectorCall(sector="Biotech", direction="upside", thesis="FDA cycle",
                                    reasoning=reasoning("biotech up", 0.6))],
            ),
            SectorDeepDiveOutput: lambda p: SectorDeepDiveOutput(
                sector="Biotech", sector_view="constructive",
                shortlist=[
                    self.entry("AAA", 80, True),
                    self.entry("BBB", 90, True),
                    self.entry("CCC", 40, False),
                ],
            ),
            CompanyDeepDiveOutput: lambda p: CompanyDeepDiveOutput(
                ticker=ticker_in(p), verdict="pass", thesis=f"{ticker_in(p)} thesis",
                catalyst_checks=[CatalystCheck(catalyst="PDUFA", status="verified", notes="")],
                reasoning=reasoning("worthy", 0.65),
            ),
            TechnicalOutput: lambda p: (
                TechnicalOutput(ticker="AAA", verdict="pass", setup="base breakout", plan=plan(),
                                reasoning=reasoning("clean", 0.55))
                if ticker_in(p) == "AAA" else
                TechnicalOutput(ticker=ticker_in(p), verdict="reject", setup="extended", plan=None,
                                reasoning=reasoning("no clean setup", 0.3))
            ),
            FullReviewOutput: lambda p: FullReviewOutput(
                ticker=ticker_in(p), action="hold", thesis_intact=True, updated_plan=None,
                reasoning=reasoning("intact")),
            ProcessReviewOutput: lambda p: ProcessReviewOutput(
                ticker=ticker_in(p),
                stage_grades=[StageGrade(stage=Stage.TECHNICAL, grade=4, reasoning_sound=True,
                                         missed_foreseeable_risks=[], notes="")],
                outcome_attribution="not_a_loss", primary_stage_at_fault=None, attribution_reasoning="won",
                improvements=[{"target_stage": Stage.MARKET_SCAN, "suggestion": "check rate sensitivity"}],
            ),
        }

    @staticmethod
    def entry(ticker: str, score: int, passed: bool) -> ShortlistEntry:
        return ShortlistEntry(
            ticker=ticker, company_name=f"{ticker} Inc", potential_score=score, passed=passed,
            catalysts=[Catalyst(kind="fda", description="PDUFA", expected_date="2026-07-01", source="news")],
            reasoning=reasoning(f"{ticker} shortlist", 0.6 if passed else 0.2),
        )

    async def structured(self, *, system: str, prompt: str, output):
        self.calls.append((output, system, prompt))
        return self.handlers[output](prompt)

    def prompts(self, output: type[BaseModel]) -> list[str]:
        return [p for o, _, p in self.calls if o is output]

    def systems(self, output: type[BaseModel]) -> list[str]:
        return [s for o, s, _ in self.calls if o is output]


def make_bars(closes: list[float], start: datetime) -> list[PriceBar]:
    return [PriceBar(ts=start + timedelta(days=i), open=c, high=c + 1, low=c - 1, close=c)
            for i, c in enumerate(closes)]


class FixturePrices:
    def __init__(self, bars: dict[str, list[PriceBar]] | None = None) -> None:
        self.series = bars or {}
        self.intervals: list[str] = []

    async def bars(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> list[PriceBar]:
        return [b for b in self.series.get(ticker, []) if b.ts.date() >= start and b.ts <= as_of]

    async def ohlcv(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        self.intervals.append(interval)
        bars = await self.bars(ticker, start, as_of, interval)
        return DataSnapshot(kind=f"ohlcv:{interval}", source="fixture", subject=ticker, as_of=as_of,
                            payload=[b.model_dump(mode="json") for b in bars])

    async def indicators(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        return DataSnapshot(kind=f"indicators:{interval}", source="fixture", subject=ticker, as_of=as_of,
                            payload={"rsi": 55})

    async def pivots(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        return DataSnapshot(kind=f"pivots:{interval}", source="fixture", subject=ticker, as_of=as_of,
                            payload={"s1": 95})


class FixtureQuotes:
    def __init__(self, price: float = 101.5) -> None:
        self.price = price

    async def quote(self, ticker: str) -> DataSnapshot:
        return DataSnapshot(kind="quote", source="fixture", subject=ticker, as_of=AS_OF, payload={"price": self.price})

    async def positions(self) -> DataSnapshot:
        return DataSnapshot(kind="positions", source="fixture", subject="account", as_of=AS_OF, payload=[])


class FixtureSectors:
    def __init__(self, future_leak: bool = False) -> None:
        self.future_leak = future_leak

    async def market_overview(self, as_of: datetime) -> list[DataSnapshot]:
        ts = as_of + timedelta(days=1) if self.future_leak else as_of
        return [DataSnapshot(kind="sector_performance", source="fixture", subject="market", as_of=ts,
                             payload={"Biotech": 0.04})]

    async def sector_screen(self, sector: str, as_of: datetime) -> list[DataSnapshot]:
        return [DataSnapshot(kind="screen", source="fixture", subject=t, as_of=as_of,
                             payload={"ticker": t, "pe": pe, "screen_marker": f"SCREEN-{t}"})
                for t, pe in (("AAA", 18), ("BBB", 25), ("CCC", 40))]

    async def sector_breadth(self, sector: str, as_of: datetime) -> DataSnapshot:
        return DataSnapshot(kind="sector_breadth", source="fixture", subject=sector, as_of=as_of,
                            payload={"pct_above_50dma": 0.62})


class FixtureNews:
    def __init__(self, earnings: dict[str, str | None] | None = None) -> None:
        self.events_by_subject: dict[str, list] = {}
        self.earnings = earnings or {}

    async def upcoming_earnings(self, ticker: str, as_of: datetime) -> DataSnapshot:
        return DataSnapshot(kind="earnings_calendar", source="fixture", subject=ticker, as_of=as_of,
                            payload={"next_earnings_date": self.earnings.get(ticker), "confirmed": True})

    async def events(self, subject: str, since: datetime, as_of: datetime) -> DataSnapshot:
        items = [e for e in self.events_by_subject.get(subject, []) if since < e["ts"] <= as_of]
        return DataSnapshot(kind="news_catalysts", source="fixture", subject=subject, as_of=as_of,
                            payload=[{**e, "ts": e["ts"].isoformat()} for e in items])


class FixtureFilings:
    def __init__(self) -> None:
        self.filings: dict[str, list[dict]] = {}

    async def recent_filings(self, ticker: str, since: datetime, as_of: datetime) -> DataSnapshot:
        rows = [f for f in self.filings.get(ticker, []) if since.date().isoformat() <= f["filed"] < as_of.date().isoformat()]
        return DataSnapshot(kind="filings", source="fixture", subject=ticker, as_of=as_of, payload=rows)


class FixtureMacro:
    async def macro(self, as_of: datetime) -> list[DataSnapshot]:
        return [DataSnapshot(kind="macro", source="fixture", subject="market", as_of=as_of,
                             payload={"fed_funds_rate": 4.25, "cpi_yoy": 2.9, "macro_marker": "MACRO-OK"})]


def providers(**overrides) -> DataProviders:
    base = dict(prices=FixturePrices(), quotes=FixtureQuotes(), sectors=FixtureSectors(), news=FixtureNews(),
                fundamentals=UnavailableFundamentals(), filings=FixtureFilings(), macro=FixtureMacro())
    base.update(overrides)
    return DataProviders(**base)
