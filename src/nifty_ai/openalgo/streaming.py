"""Streaming helpers for OpenAlgo real-time market data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

import pandas as pd

from nifty_ai.openalgo.client import NiftyOpenAlgoClient


class StreamingNotImplementedError(NotImplementedError):
    """Raised when a supplied client does not expose streaming methods."""


@dataclass(slots=True)
class Tick:
    """Normalized real-time tick."""

    symbol: str
    exchange: str
    ltp: float
    timestamp: datetime
    volume: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


def normalize_tick(payload: dict[str, Any]) -> Tick:
    """Normalize common OpenAlgo tick payload variants."""
    symbol = str(payload.get("symbol") or payload.get("tradingsymbol") or "").upper()
    exchange = str(payload.get("exchange") or payload.get("exch") or "NSE").upper()
    ltp = float(payload.get("ltp") or payload.get("last_price") or payload.get("price"))
    raw_ts = payload.get("timestamp") or payload.get("time") or datetime.now()
    timestamp = pd.Timestamp(raw_ts).to_pydatetime()
    volume = float(payload.get("volume") or payload.get("vtt") or 0.0)
    return Tick(symbol=symbol, exchange=exchange, ltp=ltp, timestamp=timestamp, volume=volume, raw=payload)


class TickBarAggregator:
    """Aggregate ticks into OHLCV bars for paper trading."""

    def __init__(self, timeframe: str = "1m") -> None:
        self.timeframe = timeframe
        self._minutes = _timeframe_minutes(timeframe)
        self._current_bucket: datetime | None = None
        self._current: dict[str, Any] | None = None

    def update(self, tick: Tick | dict[str, Any]) -> dict[str, Any] | None:
        """Update with a tick; return a completed bar when a new bucket starts."""
        normalized = normalize_tick(tick) if isinstance(tick, dict) else tick
        bucket = _floor_time(normalized.timestamp, self._minutes)
        if self._current is None:
            self._start_bar(normalized, bucket)
            return None
        if bucket != self._current_bucket:
            completed = self._current
            self._start_bar(normalized, bucket)
            return completed
        self._current["high"] = max(self._current["high"], normalized.ltp)
        self._current["low"] = min(self._current["low"], normalized.ltp)
        self._current["close"] = normalized.ltp
        self._current["volume"] += normalized.volume
        return None

    def flush(self) -> dict[str, Any] | None:
        """Return the in-progress bar, if any."""
        return self._current

    def _start_bar(self, tick: Tick, bucket: datetime) -> None:
        self._current_bucket = bucket
        self._current = {
            "timestamp": bucket,
            "symbol": tick.symbol,
            "exchange": tick.exchange,
            "open": tick.ltp,
            "high": tick.ltp,
            "low": tick.ltp,
            "close": tick.ltp,
            "volume": tick.volume,
        }


def subscribe_ltp(
    client: NiftyOpenAlgoClient | Any,
    instruments: list[dict[str, str]],
    callback: Callable[[dict[str, Any]], None],
) -> Any:
    """Subscribe to LTP ticks using an OpenAlgo SDK-like client."""
    if hasattr(client, "subscribe_ltp"):
        return client.subscribe_ltp(instruments, callback)
    if hasattr(client, "_sdk") and hasattr(client._sdk, "subscribe_ltp"):
        return client._sdk.subscribe_ltp(instruments, callback)
    raise StreamingNotImplementedError("client does not expose subscribe_ltp")


def subscribe_depth(
    client: NiftyOpenAlgoClient | Any,
    instruments: list[dict[str, str]],
    callback: Callable[[dict[str, Any]], None],
) -> Any:
    """Subscribe to L2 depth updates using an OpenAlgo SDK-like client."""
    if hasattr(client, "subscribe_depth"):
        return client.subscribe_depth(instruments, callback)
    if hasattr(client, "_sdk") and hasattr(client._sdk, "subscribe_depth"):
        return client._sdk.subscribe_depth(instruments, callback)
    raise StreamingNotImplementedError("client does not expose subscribe_depth")


def _timeframe_minutes(timeframe: str) -> int:
    lower = timeframe.lower().strip()
    if not lower.endswith("m"):
        raise ValueError(f"only minute timeframes are supported for live aggregation: {timeframe}")
    minutes = int(lower[:-1])
    if minutes <= 0:
        raise ValueError("timeframe must be positive")
    return minutes


def _floor_time(ts: datetime, minutes: int) -> datetime:
    floored_minute = (ts.minute // minutes) * minutes
    return ts.replace(minute=floored_minute, second=0, microsecond=0)
