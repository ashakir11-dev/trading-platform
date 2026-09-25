"""MCP access for data adapters.

Adapters talk to MCP through the tiny ``McpToolCaller`` protocol, so the transport
(``HttpMcpClient``, a test double, ...) can be swapped. ``HttpMcpClient`` only calls
tools on an explicit allowlist, which keeps MCP use read-only.
"""

from __future__ import annotations

from typing import Any, Protocol


class McpToolCaller(Protocol):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any: ...


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
