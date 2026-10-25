"""OpenAlgo MCP (Model Context Protocol) server bridge.

OpenAlgo ships an MCP server exposing tools like `get_historical_data`,
`get_option_chain`, `place_order`, `get_funds`, etc. directly to LLMs. This
module discovers those tools at runtime and binds them as LangChain `Tool`
objects for injection into TradingAgents analyst nodes.

Phase 3 deliverable (discovery + binding). Phase 8 will wire them into the
graph_factory.
"""

from __future__ import annotations

from typing import Any


class MCPToolsNotImplementedError(NotImplementedError):
    """MCP discovery + LangChain binding is wired up in Phase 3."""


def discover_openalgo_mcp_tools(*, url: str | None = None) -> list[Any]:
    """Connect to the OpenAlgo MCP server and return LangChain Tool objects.

    Implemented in Phase 3 once the agent vendor-injection layer needs them.
    """
    raise MCPToolsNotImplementedError(
        "OpenAlgo MCP tool discovery is wired up in Phase 3"
    )
