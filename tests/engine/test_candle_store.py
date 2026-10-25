from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest

from nifty_ai.engine.candle_store import CandleStore, resample_ohlcv


def _candles() -> pd.DataFrame:
    start = datetime(2026, 5, 27, 9, 15)
    rows = []
    for i in range(5):
        price = 100 + i
        rows.append(
            {
                "timestamp": start + timedelta(minutes=i),
                "open": price,
                "high": price + 1,
                "low": price - 1,
                "close": price + 0.5,
                "volume": 100 + i,
            }
        )
    return pd.DataFrame(rows)


def test_candle_store_round_trip_and_resample(tmp_path):
    store = CandleStore(tmp_path / "candles.duckdb")
    try:
        assert store.put_candles("NSE", "RELIANCE", _candles()) == 5
        cached = store.get_candles("NSE", "RELIANCE", "2026-05-27 09:15", "2026-05-27 09:19")
        resampled = store.get_candles(
            "NSE", "RELIANCE", "2026-05-27 09:15", "2026-05-27 09:19", timeframe="5m"
        )
    finally:
        store.close()

    assert len(cached) == 5
    assert len(resampled) == 2
    assert resampled.iloc[-1]["high"] == 105


def test_resample_ohlcv_aggregates_expected_columns():
    out = resample_ohlcv(_candles(), "5m")

    assert list(out.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert out.iloc[0]["open"] == 100


def test_resample_ohlcv_rejects_unsupported_timeframe():
    with pytest.raises(ValueError):
        resample_ohlcv(_candles(), "1h")
