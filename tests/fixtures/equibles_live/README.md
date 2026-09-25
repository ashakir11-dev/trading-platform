Real responses from the hosted Equibles MCP server (https://mcp.equibles.com/mcp),
captured 2026-09-25 through the session's Equibles connector with small maxResults.
`tests/test_equibles_live_formats.py` replays them through every adapter to catch
format drift between the hosted server and the open-source code the adapters were
built from. Refresh them if Equibles changes its output.
