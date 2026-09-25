"""Placeholder providers for data that has no source yet (see docs/ARCHITECTURE.md §6).

They return snapshots marked ``is_gap=True`` so agents are told explicitly that the
data is missing, and the process agent can attribute failures to data gaps rather
than to bad reasoning. Replace each with a real provider once a source is chosen.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from .base import DataSnapshot, PriceBar


def _gap(kind: str, subject: str, as_of: datetime, note: str) -> DataSnapshot:
    return DataSnapshot(kind=kind, source="unavailable", subject=subject, as_of=as_of, is_gap=True, note=note)


class UnavailableSectorData:
    async def market_overview(self, as_of: datetime) -> list[DataSnapshot]:
        return [_gap("sector_performance", "market", as_of, "OPEN GAP: no live/historical sector performance source.")]

    async def sector_screen(self, sector: str, as_of: datetime) -> list[DataSnapshot]:
        return [_gap("screen", sector, as_of, "OPEN GAP: no sector screening source.")]

    async def sector_breadth(self, sector: str, as_of: datetime) -> DataSnapshot:
        return _gap("sector_breadth", sector, as_of, "OPEN GAP: no sector breadth source.")


class UnavailableNews:
    async def events(self, subject: str, since: datetime, as_of: datetime) -> DataSnapshot:
        return _gap("news_catalysts", subject, as_of, "OPEN GAP: no dated news/catalyst archive.")

    async def upcoming_earnings(self, ticker: str, as_of: datetime) -> DataSnapshot:
        return _gap("earnings_calendar", ticker, as_of, "OPEN GAP: no earnings calendar source.")


class UnavailableFundamentals:
    async def fundamentals(self, ticker: str, as_of: datetime) -> DataSnapshot:
        return _gap("fundamentals", ticker, as_of, "No fundamentals source chosen yet.")


class UnavailableFilings:
    async def recent_filings(self, ticker: str, since: datetime, as_of: datetime) -> DataSnapshot:
        return _gap("filings", ticker, as_of, "No filings source configured.")


class UnavailableMacro:
    async def macro(self, as_of: datetime) -> list[DataSnapshot]:
        return [_gap("macro", "market", as_of, "No macro data source configured.")]


class UnavailablePrices:
    """Gap placeholder for prices: explicit gap snapshots, no bars."""

    async def bars(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> list[PriceBar]:
        return []

    async def ohlcv(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        return _gap(f"ohlcv:{interval}", ticker, as_of, "No price source configured.")

    async def indicators(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        return _gap(f"indicators:{interval}", ticker, as_of, "No price source configured.")

    async def pivots(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        return _gap(f"pivots:{interval}", ticker, as_of, "No price source configured.")


class UnavailableQuotes:
    """Gap placeholder for live quotes. The stale-entry rule falls back to the last close."""

    async def quote(self, ticker: str) -> DataSnapshot:
        return _gap("quote", ticker, datetime.now(timezone.utc), "No live quote source configured.")

    async def positions(self) -> DataSnapshot:
        return _gap("positions", "account", datetime.now(timezone.utc), "No account source configured.")
