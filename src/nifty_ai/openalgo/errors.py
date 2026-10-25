"""Typed exceptions for the OpenAlgo client layer."""

from __future__ import annotations


class OpenAlgoError(Exception):
    """Base class for all OpenAlgo client errors."""

    def __init__(self, message: str, *, payload: dict | None = None) -> None:
        super().__init__(message)
        self.payload = payload or {}


class OpenAlgoAuthError(OpenAlgoError):
    """Authentication failed (invalid / missing API key)."""


class OpenAlgoRateLimitError(OpenAlgoError):
    """Server signaled rate-limit / throttle."""


class OpenAlgoMarketClosedError(OpenAlgoError):
    """Order placement attempted outside market hours."""


class OpenAlgoSymbolError(OpenAlgoError):
    """Malformed or unknown Indian-market symbol."""
