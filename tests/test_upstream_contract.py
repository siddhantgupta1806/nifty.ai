from __future__ import annotations

import importlib

import pytest


def test_tradingagents_contract_symbols_exist():
    """Fail loudly when upstream TradingAgents moves the patch points."""
    modules = {
        "tradingagents.agents.utils.tool_registry": [
            "ANALYST_TOOL_REGISTRY",
            "get_analyst_tools",
            "get_analyst_tool_names",
        ],
        "tradingagents.graph.trading_graph": ["TradingAgentsGraph"],
        "tradingagents.config": ["TradingAgentsConfig"],
    }

    for module_name, attrs in modules.items():
        try:
            mod = importlib.import_module(module_name)
        except ImportError as exc:
            pytest.skip(f"tradingagents optional dependency unavailable: {exc}")
        for attr in attrs:
            assert hasattr(mod, attr), f"{module_name}.{attr} missing"

    registry = importlib.import_module("tradingagents.agents.utils.tool_registry")
    expected_keys = {"market", "social", "news", "fundamentals"}
    assert expected_keys <= set(registry.ANALYST_TOOL_REGISTRY)
