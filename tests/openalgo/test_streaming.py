from __future__ import annotations

from datetime import datetime

from nifty_ai.openalgo.streaming import TickBarAggregator, normalize_tick, subscribe_ltp


class FakeSdk:
    def __init__(self) -> None:
        self.called = None

    def subscribe_ltp(self, instruments, callback):
        self.called = (instruments, callback)
        return "ok"


def test_normalize_tick_and_aggregate_to_bars():
    agg = TickBarAggregator("1m")
    first = normalize_tick({"symbol": "reliance", "exchange": "nse", "ltp": 100, "timestamp": datetime(2026, 5, 27, 9, 15), "volume": 2})
    assert first.symbol == "RELIANCE"
    assert agg.update(first) is None
    assert agg.update({"symbol": "RELIANCE", "ltp": 102, "timestamp": datetime(2026, 5, 27, 9, 15, 30), "volume": 3}) is None
    completed = agg.update({"symbol": "RELIANCE", "ltp": 103, "timestamp": datetime(2026, 5, 27, 9, 16), "volume": 1})

    assert completed is not None
    assert completed["open"] == 100
    assert completed["high"] == 102
    assert completed["low"] == 100
    assert completed["close"] == 102
    assert completed["volume"] == 5


def test_subscribe_ltp_delegates_to_sdk_like_client():
    sdk = FakeSdk()
    result = subscribe_ltp(sdk, [{"symbol": "RELIANCE", "exchange": "NSE"}], lambda tick: None)

    assert result == "ok"
    assert sdk.called is not None