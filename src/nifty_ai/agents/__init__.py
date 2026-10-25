"""TradingAgents adaptation layer (Phase 3).

Public re-exports for convenience; submodules `tools_openalgo`, `config`,
`vendor_injection`, `graph_factory` can also be imported directly.
"""

from nifty_ai.agents.config import build_nifty_config
from nifty_ai.agents.graph_factory import build_nifty_graph
from nifty_ai.agents.vendor_injection import (
    apply_openalgo_patch,
    is_patched,
    restore_upstream_tools,
)

__all__ = [
    "apply_openalgo_patch",
    "build_nifty_config",
    "build_nifty_graph",
    "is_patched",
    "restore_upstream_tools",
]

