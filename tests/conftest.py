"""Shared pytest fixtures."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _set_test_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure every test has a non-empty OPENALGO_API_KEY so the client constructs."""
    if not os.environ.get("OPENALGO_API_KEY"):
        monkeypatch.setenv("OPENALGO_API_KEY", "test-key")
    # Reset the settings singleton so the new env var is picked up.
    import nifty_ai.settings as s

    s._settings = None
