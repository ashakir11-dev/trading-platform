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
    """Historical OHLCV, indicators, pivots. (Source: Equibles.)

    ``ohlcv``/``indicators``/``pivots`` return raw snapshots for agent prompts;
    ``bars`` returns typed bars for deterministic code (tripwires, outcomes, rules).
    ``interval`` is "1h", "1d" or "1w" (see profile.HORIZONS). Snapshot ``kind`` is
    suffixed with the interval, e.g. "ohlcv:1d".
    """

    async def bars(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> list[PriceBar]: ...

    async def ohlcv(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> DataSnapshot: ...
    async def indicators(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot: ...
    async def pivots(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot: ...


class QuoteProvider(Protocol):
    """Live quotes and, optionally, account positions. (Source: Equibles.) READ-ONLY."""

    async def quote(self, ticker: str) -> DataSnapshot: ...
    async def positions(self) -> DataSnapshot: ...


class SectorDataProvider(Protocol):
    """Sector performance / breadth / screening. OPEN GAP (breadth to be derived from prices)."""

    async def market_overview(self, as_of: datetime) -> list[DataSnapshot]: ...
    async def sector_screen(self, sector: str, as_of: datetime) -> list[DataSnapshot]:
        """Cheap bulk screening data for every company in the sector (Agent 1's input).

        One snapshot per company, ``subject`` = its ticker, ``kind`` = "screen": key ratios,
        size, recent filings/events. Full per-company fundamentals are fetched later, only
        for shortlisted companies (company deep dive). A gap may return one sector-level
        snapshot instead.
        """
        ...
    async def sector_breadth(self, sector: str, as_of: datetime) -> DataSnapshot: ...


class NewsCatalystProvider(Protocol):
    """Dated news and catalyst events (earnings, FDA, analyst actions). OPEN GAP (esp. historical).

    ``events`` payload: a list of event dicts. Recognised keys (all optional except
    ``ts`` and ``headline``): ``ts`` (ISO time), ``headline``, ``category`` (e.g.
    "earnings", "fda", "m_and_a", "analyst_rating_change", "price_action"),
    ``source``, ``sec_form`` (e.g. "8-K"), ``sec_items`` (e.g. ["2.02"]), ``url``.
    ``rules.is_material`` uses these to separate material news from noise.

    ``upcoming_earnings`` payload: ``{"next_earnings_date": "YYYY-MM-DD" | None,
    "confirmed": bool}`` as known at ``as_of``.
    """

    async def events(self, subject: str, since: datetime, as_of: datetime) -> DataSnapshot: ...
    async def upcoming_earnings(self, ticker: str, as_of: datetime) -> DataSnapshot: ...


class FundamentalsProvider(Protocol):
    """Financial statements, point-in-time by filing date. (Source: Equibles.)"""

    async def fundamentals(self, ticker: str, as_of: datetime) -> DataSnapshot: ...


class FilingsProvider(Protocol):
    """A company's recent SEC filings (10-K, 10-Q, 8-K, ...) as known at ``as_of``.

    Payload: a list of dicts with ``form``, ``filed`` (ISO date/time), ``period``,
    ``sec_items`` (8-K item numbers), ``title``/``summary`` and optional ``excerpt``.
    Only filings made before ``as_of`` may appear. ``kind`` = "filings".
    """

    async def recent_filings(self, ticker: str, since: datetime, as_of: datetime) -> DataSnapshot: ...


class MacroProvider(Protocol):
    """Market-level macro data (rates, inflation, employment, FX, spreads) as known at ``as_of``.

    Returns snapshots with ``subject`` = "market" so they reach every stage through the
    relevant-subset filter. ``kind`` starts with "macro".
    """

    async def macro(self, as_of: datetime) -> list[DataSnapshot]: ...


@dataclass
class DataProviders:
    prices: PriceDataProvider
    quotes: QuoteProvider
    sectors: SectorDataProvider
    news: NewsCatalystProvider
    fundamentals: FundamentalsProvider
    filings: FilingsProvider
    macro: MacroProvider
