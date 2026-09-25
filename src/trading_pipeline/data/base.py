"""Data provider interfaces and the raw-data bundle that travels between stages.

Every call takes ``as_of``: a provider must return only data that was knowable at
that time. That makes the same code path usable for live runs and honest backtests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field

from ..schemas import new_id, utcnow


class LookaheadError(ValueError):
    """A snapshot dated after the run's as_of tried to enter a bundle."""


class DataSnapshot(BaseModel):
    id: str = Field(default_factory=new_id)
    kind: str  # e.g. "ohlcv", "sector_breadth", "news", "fundamentals", "quote"
    source: str  # e.g. "massive", "robinhood", "unavailable"
    subject: str  # ticker, sector, or "market"
    as_of: datetime  # the latest point in time this data reflects
    fetched_at: datetime = Field(default_factory=utcnow)
    payload: Any = None
    is_gap: bool = False  # True when no source exists yet (see ARCHITECTURE.md, data gaps)
    note: str = ""

    def prompt_view(self) -> dict[str, Any]:
        view: dict[str, Any] = {
            "snapshot_id": self.id,
            "kind": self.kind,
            "source": self.source,
            "subject": self.subject,
            "as_of": self.as_of.isoformat(),
        }
        if self.is_gap:
            view["UNAVAILABLE"] = self.note or "No data source configured for this category."
        else:
            view["data"] = self.payload
        return view


class RawDataBundle(BaseModel):
    """Raw data behind a stage's report. Passed forward with the report (pass-through rule)."""

    as_of: datetime
    snapshots: list[DataSnapshot] = []

    def add(self, snapshot: DataSnapshot) -> None:
        if snapshot.as_of > self.as_of:
            raise LookaheadError(
                f"{snapshot.kind}/{snapshot.subject} from {snapshot.source} is dated "
                f"{snapshot.as_of.isoformat()}, after run as_of {self.as_of.isoformat()}"
            )
        self.snapshots.append(snapshot)

    def extend(self, snapshots: list[DataSnapshot]) -> None:
        for s in snapshots:
            self.add(s)

    def merged(self, other: RawDataBundle) -> RawDataBundle:
        out = RawDataBundle(as_of=self.as_of)
        seen: set[str] = set()
        for s in [*self.snapshots, *other.snapshots]:
            if s.id not in seen:
                out.add(s)
                seen.add(s.id)
        return out

    def filter(self, *, subjects: set[str] | None = None) -> RawDataBundle:
        """Keep market-level data plus snapshots about the given subjects."""
        out = RawDataBundle(as_of=self.as_of)
        for s in self.snapshots:
            if subjects is None or s.subject == "market" or s.subject in subjects:
                out.add(s)
        return out

    @property
    def ids(self) -> list[str]:
        return [s.id for s in self.snapshots]

    def to_prompt(self) -> str:
        return json.dumps([s.prompt_view() for s in self.snapshots], indent=1, default=str)


# --------------------------------------------------------------------------------------
# Provider interfaces
# --------------------------------------------------------------------------------------


class PriceBar(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class PriceDataProvider(Protocol):
    """Historical OHLCV, indicators, pivots. (Candidate: Massive.com MCP.)

    ``ohlcv``/``indicators``/``pivots`` return raw snapshots for agent prompts;
    ``bars`` returns typed daily bars for deterministic code (tripwires, outcomes).
    """

    async def bars(self, ticker: str, start: date, as_of: datetime) -> list[PriceBar]: ...

    async def ohlcv(self, ticker: str, start: date, as_of: datetime) -> DataSnapshot: ...
    async def indicators(self, ticker: str, as_of: datetime) -> DataSnapshot: ...
    async def pivots(self, ticker: str, as_of: datetime) -> DataSnapshot: ...


class QuoteProvider(Protocol):
    """Live quotes and, optionally, account positions. (Candidate: Robinhood MCP.) READ-ONLY."""

    async def quote(self, ticker: str) -> DataSnapshot: ...
    async def positions(self) -> DataSnapshot: ...


class SectorDataProvider(Protocol):
    """Sector performance / breadth / screening. OPEN GAP."""

    async def market_overview(self, as_of: datetime) -> list[DataSnapshot]: ...
    async def sector_constituents(self, sector: str, as_of: datetime) -> DataSnapshot: ...
    async def sector_breadth(self, sector: str, as_of: datetime) -> DataSnapshot: ...


class NewsCatalystProvider(Protocol):
    """Dated news and catalyst events (earnings, FDA, analyst actions). OPEN GAP (esp. historical)."""

    async def events(self, subject: str, since: datetime, as_of: datetime) -> DataSnapshot: ...


class FundamentalsProvider(Protocol):
    """Financials, filings, ownership, valuation. No source chosen yet."""

    async def fundamentals(self, ticker: str, as_of: datetime) -> DataSnapshot: ...


@dataclass
class DataProviders:
    prices: PriceDataProvider
    quotes: QuoteProvider
    sectors: SectorDataProvider
    news: NewsCatalystProvider
    fundamentals: FundamentalsProvider
