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

    # interval -> (multiplier, timespan) in Massive/Polygon aggregate terms.
    _SPANS = {"1h": (1, "hour"), "1d": (1, "day"), "1w": (1, "week")}

    async def _snapshot(self, kind: str, tool: str, ticker: str, as_of: datetime, args: dict[str, Any]) -> DataSnapshot:
        payload = await self._mcp.call_tool(tool, args)
        return DataSnapshot(kind=kind, source="massive", subject=ticker, as_of=as_of, payload=payload)

    async def ohlcv(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        # Request data only up to as_of so backtests can't see the future.
        mult, span = self._SPANS[interval]
        args = {"ticker": ticker, "from": start.isoformat(), "to": as_of.date().isoformat(),
                "multiplier": mult, "timespan": span}
        return await self._snapshot(f"ohlcv:{interval}", self.TOOL_OHLCV, ticker, as_of, args)

    async def bars(self, ticker: str, start: date, as_of: datetime, interval: str = "1d") -> list[PriceBar]:
        snap = await self.ohlcv(ticker, start, as_of, interval)
        # TODO: parse the Massive OHLCV payload shape into PriceBar rows.
        raise NotImplementedError(f"parse Massive OHLCV payload into PriceBar: {type(snap.payload)!r}")

    async def indicators(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        args = {"ticker": ticker, "as_of": as_of.date().isoformat(), "timespan": self._SPANS[interval][1]}
        return await self._snapshot(f"indicators:{interval}", self.TOOL_INDICATORS, ticker, as_of, args)

    async def pivots(self, ticker: str, as_of: datetime, interval: str = "1d") -> DataSnapshot:
        args = {"ticker": ticker, "as_of": as_of.date().isoformat(), "timespan": self._SPANS[interval][1]}
        return await self._snapshot(f"pivots:{interval}", self.TOOL_PIVOTS, ticker, as_of, args)


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


class HttpMcpClient:
    """McpToolCaller over MCP Streamable HTTP, restricted to an explicit tool allowlist.

    The allowlist is how this codebase keeps MCP read-only: only tools named here
    can be called, so a server that also exposes write or order tools can't be
    reached through this client by accident. Use as an async context manager.
    """

    def __init__(self, url: str, *, allowed_tools: set[str], headers: dict[str, str] | None = None,
                 timeout: float = 60.0) -> None:
        self._url = url
        self._allowed = frozenset(allowed_tools)
        self._headers = headers or {}
        self._timeout = timeout
        self._stack = None
        self._session = None

    async def __aenter__(self) -> HttpMcpClient:
        from contextlib import AsyncExitStack

        import httpx2
        from mcp import ClientSession
        from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

        self._stack = AsyncExitStack()
        http = await self._stack.enter_async_context(
            create_mcp_http_client(headers=self._headers, timeout=httpx2.Timeout(self._timeout)))
        read, write = await self._stack.enter_async_context(streamable_http_client(self._url, http_client=http))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._stack is not None:
            await self._stack.aclose()
        self._stack = self._session = None

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if name not in self._allowed:
            raise PermissionError(f"MCP tool {name!r} is not in this client's allowlist")
        if self._session is None:
            raise RuntimeError("HttpMcpClient must be used inside 'async with'")
        result = await self._session.call_tool(name, arguments)
        text = "\n".join(getattr(c, "text", "") for c in getattr(result, "content", []) or [])
        if getattr(result, "is_error", False):
            raise RuntimeError(f"MCP tool {name} failed: {text[:500]}")
        return text
