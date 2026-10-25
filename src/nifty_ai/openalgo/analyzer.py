"""Helpers for OpenAlgo's built-in paper-trading sandbox ("Analyzer Mode").

Analyzer Mode mirrors real-time broker margins / auto-square-off rules against
a virtual ₹1 Cr capital, isolated from any live trading database.
"""

from __future__ import annotations

from typing import Any

from nifty_ai.openalgo.client import NiftyOpenAlgoClient


def analyzer_status(client: NiftyOpenAlgoClient) -> dict[str, Any]:
    """Return current analyzer mode state + virtual balances."""
    return client._post("/analyzerstatus", {})


def enable_analyzer(client: NiftyOpenAlgoClient) -> dict[str, Any]:
    """Turn Analyzer Mode ON (subsequent orders route to the sandbox)."""
    return client._post("/analyzertoggle", {"mode": True})


def disable_analyzer(client: NiftyOpenAlgoClient) -> dict[str, Any]:
    """Turn Analyzer Mode OFF (subsequent orders route to live broker)."""
    return client._post("/analyzertoggle", {"mode": False})


def is_analyzer_on(client: NiftyOpenAlgoClient) -> bool:
    """Convenience boolean check."""
    data = analyzer_status(client) or {}
    return bool(data.get("analyzer_mode") or data.get("mode"))
