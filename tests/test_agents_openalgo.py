from __future__ import annotations

import importlib

import pandas as pd
import pytest

from nifty_ai.agents import tools_openalgo
from nifty_ai.agents.vendor_injection import apply_openalgo_patch, restore_upstream_tools


class FakeClient:
    def history(self, **kwargs):
        self.last_history_kwargs = kwargs
        return [
            {
                "date": "2026-05-25",
                "open": 100,
                "high": 105,
                "low": 99,
                "close": 104,
                "volume": 1000,
            },
            {
                "date": "2026-05-26",
                "open": 104,
                "high": 108,
                "low": 103,
                "close": 107,
                "volume": 1200,
            },
        ]

    def optionchain(self, **kwargs):
        return [{"strike": 25000, "ce_ltp": 150.5, "pe_ltp": 120.25}]

    def optiongreeks(self, **kwargs):
        return {"delta": 0.51, "theta": -8.2}


@pytest.fixture(autouse=True)
def reset_client():
    tools_openalgo.set_client(None)
    yield
    tools_openalgo.set_client(None)


def test_get_stock_data_uses_openalgo_history():
    client = FakeClient()
    tools_openalgo.set_client(client)  # type: ignore[arg-type]

    report = tools_openalgo.get_stock_data.invoke(
        {"symbol": "RELIANCE", "start_date": "2026-05-25", "end_date": "2026-05-26"}
    )

    assert "Source: OpenAlgo" in report
    assert "RELIANCE" in report
    assert "2026-05-25" in report
    assert client.last_history_kwargs["symbol"] == "RELIANCE"
    assert client.last_history_kwargs["exchange"] == "NSE"
    assert client.last_history_kwargs["interval"] == "D"


def test_option_tools_return_csv_and_key_value_reports():
    client = FakeClient()
    tools_openalgo.set_client(client)  # type: ignore[arg-type]

    chain = tools_openalgo.get_option_chain.invoke({"underlying": "NIFTY", "expiry": "2026-05-28"})
    greeks = tools_openalgo.get_option_greeks.invoke({"symbol": "NIFTY25MAY2525000CE"})

    assert "strike" in chain
    assert "25000" in chain
    assert "delta: 0.51" in greeks


def test_vendor_injection_replaces_upstream_registry_if_available():
    try:
        registry_mod = importlib.import_module("tradingagents.agents.utils.tool_registry")
    except ImportError:
        pytest.skip("tradingagents optional dependency not installed")

    original_market = registry_mod.ANALYST_TOOL_REGISTRY["market"]
    try:
        apply_openalgo_patch()
        patched_market = registry_mod.ANALYST_TOOL_REGISTRY["market"]
        assert patched_market is tools_openalgo.OPENALGO_MARKET_TOOLS
        assert patched_market[0].name == "get_stock_data"
    finally:
        restore_upstream_tools()

    assert registry_mod.ANALYST_TOOL_REGISTRY["market"] == original_market


def test_openalgo_history_dataframe_normalization():
    client = FakeClient()
    tools_openalgo.set_client(client)  # type: ignore[arg-type]

    df = tools_openalgo._fetch_history_df("TCS", "2026-05-25", "2026-05-26")

    assert list(df.columns) == ["Date", "Open", "High", "Low", "Close", "Volume"]
    assert pd.Timestamp("2026-05-26") == df.iloc[1]["Date"]
