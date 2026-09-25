"""Skeleton adapters for the Massive.com and Robinhood MCP servers.

These are the original *candidate* providers, not a commitment (docs/ARCHITECTURE.md
§5). Other vendors plug in by implementing the protocols in ``data/base.py``.

The pipeline talks to MCP through the tiny ``McpToolCaller`` protocol so the
transport (an MCP client session, a Claude MCP connector, a test double) can be
swapped. The concrete tool names and argument shapes of each server are NOT
mapped yet; fill in ``TOOL_*`` constants after listing the servers' tools.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Protocol

from .base import DataSnapshot, PriceBar


class McpToolCaller(Protocol):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any: ...


class MassivePriceData:
    """PriceDataProvider backed by the Massive.com MCP (historical OHLCV, indicators, pivots)."""

    # TODO: map to the real Massive MCP tool names once listed.
    TOOL_OHLCV = "TODO_massive_ohlcv"
    TOOL_INDICATORS = "TODO_massive_indicators"
    TOOL_PIVOTS = "TODO_massive_pivots"

    def __init__(self, mcp: McpToolCaller) -> None:
        self._mcp = mcp

    async def _snapshot(self, kind: str, tool: str, ticker: str, as_of: datetime, args: dict[str, Any]) -> DataSnapshot:
        payload = await self._mcp.call_tool(tool, args)
        return DataSnapshot(kind=kind, source="massive", subject=ticker, as_of=as_of, payload=payload)

    async def ohlcv(self, ticker: str, start: date, as_of: datetime) -> DataSnapshot:
        # Request data only up to as_of so backtests can't see the future.
        args = {"ticker": ticker, "from": start.isoformat(), "to": as_of.date().isoformat(), "timespan": "day"}
        return await self._snapshot("ohlcv", self.TOOL_OHLCV, ticker, as_of, args)

    async def bars(self, ticker: str, start: date, as_of: datetime) -> list[PriceBar]:
        snap = await self.ohlcv(ticker, start, as_of)
        # TODO: parse the Massive OHLCV payload shape into PriceBar rows.
        raise NotImplementedError(f"parse Massive OHLCV payload into PriceBar: {type(snap.payload)!r}")

    async def indicators(self, ticker: str, as_of: datetime) -> DataSnapshot:
        args = {"ticker": ticker, "as_of": as_of.date().isoformat()}
        return await self._snapshot("indicators", self.TOOL_INDICATORS, ticker, as_of, args)

    async def pivots(self, ticker: str, as_of: datetime) -> DataSnapshot:
        args = {"ticker": ticker, "as_of": as_of.date().isoformat()}
        return await self._snapshot("pivots", self.TOOL_PIVOTS, ticker, as_of, args)


class RobinhoodQuotes:
    """QuoteProvider backed by the Robinhood MCP.

    READ-ONLY by design: this adapter must never expose order placement, cancellation,
    or any account-mutating tool. The user executes trades themselves.
    """

    # TODO: map to the real Robinhood MCP tool names once listed.
    TOOL_QUOTE = "TODO_robinhood_quote"
    TOOL_POSITIONS = "TODO_robinhood_positions"

    def __init__(self, mcp: McpToolCaller) -> None:
        self._mcp = mcp

    async def quote(self, ticker: str) -> DataSnapshot:
        payload = await self._mcp.call_tool(self.TOOL_QUOTE, {"symbol": ticker})
        return DataSnapshot(kind="quote", source="robinhood", subject=ticker, as_of=datetime.now(timezone.utc), payload=payload)

    async def positions(self) -> DataSnapshot:
        payload = await self._mcp.call_tool(self.TOOL_POSITIONS, {})
        return DataSnapshot(kind="positions", source="robinhood", subject="account", as_of=datetime.now(timezone.utc), payload=payload)
