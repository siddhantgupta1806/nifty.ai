"""Inject OpenAlgo-backed tools into the TradingAgents framework.

TradingAgents resolves analyst tools through a single module-level dict:
``tradingagents.agents.utils.tool_registry.ANALYST_TOOL_REGISTRY``. The same
dict is imported by graph setup, the four analyst nodes, and the public
``get_analyst_tools(...)`` helper. Mutating this dict in place — *before*
constructing a ``TradingAgentsGraph`` — replaces the upstream yfinance-backed
tools with our OpenAlgo wrappers everywhere, with no fork required.

The patch is **idempotent**: repeat calls are safe. ``restore_upstream_tools``
puts the original tuples back (useful in tests).
"""

from __future__ import annotations

import logging
from typing import Any

from nifty_ai.agents.tools_openalgo import (
    OPENALGO_FUNDAMENTALS_TOOLS,
    OPENALGO_MARKET_TOOLS,
    OPENALGO_NEWS_TOOLS,
    OPENALGO_SOCIAL_TOOLS,
)

logger = logging.getLogger(__name__)

_PATCHED = False
_ORIGINAL: dict[str, tuple[Any, ...]] = {}


def apply_openalgo_patch() -> None:
    """Replace ``ANALYST_TOOL_REGISTRY`` entries with OpenAlgo-backed tools.

    Raises:
        RuntimeError: If the upstream registry symbol cannot be located.
    """
    global _PATCHED
    if _PATCHED:
        return

    try:
        from tradingagents.agents.utils import tool_registry  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover — defensive guard
        raise RuntimeError(
            "tradingagents is not installed; cannot apply OpenAlgo patch."
        ) from exc

    registry = tool_registry.ANALYST_TOOL_REGISTRY
    expected_keys = {"market", "social", "news", "fundamentals"}
    missing = expected_keys - registry.keys()
    if missing:
        raise RuntimeError(
            f"Upstream ANALYST_TOOL_REGISTRY missing expected keys: {sorted(missing)}. "
            "tradingagents may have introduced a breaking change."
        )

    # Snapshot originals for restore_upstream_tools()
    for key in expected_keys:
        _ORIGINAL[key] = registry[key]

    registry["market"] = OPENALGO_MARKET_TOOLS
    registry["social"] = OPENALGO_SOCIAL_TOOLS
    registry["news"] = OPENALGO_NEWS_TOOLS
    registry["fundamentals"] = OPENALGO_FUNDAMENTALS_TOOLS

    _PATCHED = True
    logger.info(
        "OpenAlgo vendor patch applied: market=%d social=%d news=%d fundamentals=%d tools",
        len(OPENALGO_MARKET_TOOLS),
        len(OPENALGO_SOCIAL_TOOLS),
        len(OPENALGO_NEWS_TOOLS),
        len(OPENALGO_FUNDAMENTALS_TOOLS),
    )


def restore_upstream_tools() -> None:
    """Restore the original upstream tool registry (mainly for tests)."""
    global _PATCHED
    if not _PATCHED:
        return
    from tradingagents.agents.utils import tool_registry  # noqa: WPS433

    for key, tools in _ORIGINAL.items():
        tool_registry.ANALYST_TOOL_REGISTRY[key] = tools
    _ORIGINAL.clear()
    _PATCHED = False


def is_patched() -> bool:
    """Return whether the OpenAlgo patch is currently active."""
    return _PATCHED
