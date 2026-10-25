"""OpenAlgo integration layer for Indian markets.

Wraps the official `openalgo` Python SDK with typed, retry-aware helpers
plus Indian-market-specific utilities (symbol formatting, IST calendar,
analyzer-mode toggling, MCP tool binding).
"""

from nifty_ai.openalgo.errors import (
    OpenAlgoAuthError,
    OpenAlgoError,
    OpenAlgoMarketClosedError,
    OpenAlgoRateLimitError,
)
from nifty_ai.openalgo.symbols import (
    Exchange,
    OptionType,
    build_future_symbol,
    build_option_symbol,
    parse_option_symbol,
)

__all__ = [
    "Exchange",
    "OpenAlgoAuthError",
    "OpenAlgoError",
    "OpenAlgoMarketClosedError",
    "OpenAlgoRateLimitError",
    "OptionType",
    "build_future_symbol",
    "build_option_symbol",
    "parse_option_symbol",
]
