"""DuckDB-backed one-minute candle cache."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import duckdb
import pandas as pd


OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class CandleStore:
    """Persist and retrieve 1-minute OHLCV candles by exchange/symbol."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(self.db_path))
        self._init_schema()

    def close(self) -> None:
        """Close the DuckDB connection."""
        self._conn.close()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candle_cache (
                exchange VARCHAR NOT NULL,
                symbol VARCHAR NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                open DOUBLE NOT NULL,
                high DOUBLE NOT NULL,
                low DOUBLE NOT NULL,
                close DOUBLE NOT NULL,
                volume DOUBLE NOT NULL,
                PRIMARY KEY (exchange, symbol, timestamp)
            )
            """
        )

    def put_candles(self, exchange: str, symbol: str, candles: pd.DataFrame) -> int:
        """Upsert normalized 1-minute candles, returning row count."""
        normalized = normalize_candles(candles)
        if normalized.empty:
            return 0
        payload = normalized.copy()
        payload.insert(0, "symbol", symbol.upper())
        payload.insert(0, "exchange", exchange.upper())
        self._conn.register("incoming_candles", payload)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO candle_cache
            SELECT exchange, symbol, timestamp, open, high, low, close, volume
            FROM incoming_candles
            """
        )
        self._conn.unregister("incoming_candles")
        return len(payload)

    def get_candles(
        self,
        exchange: str,
        symbol: str,
        start: datetime | str,
        end: datetime | str,
        *,
        timeframe: str = "1m",
    ) -> pd.DataFrame:
        """Return cached candles, resampled from 1m when requested."""
        frame = self._conn.execute(
            """
            SELECT timestamp, open, high, low, close, volume
            FROM candle_cache
            WHERE exchange = ? AND symbol = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
            """,
            [exchange.upper(), symbol.upper(), pd.Timestamp(start), pd.Timestamp(end)],
        ).fetchdf()
        if frame.empty or timeframe == "1m":
            return frame
        return resample_ohlcv(frame, timeframe)


def normalize_candles(candles: pd.DataFrame) -> pd.DataFrame:
    """Return a canonical timestamp/open/high/low/close/volume candle frame."""
    if candles.empty:
        return pd.DataFrame(columns=OHLCV_COLUMNS)
    frame = candles.copy()
    frame = frame.rename(columns={column: column.lower() for column in frame.columns})
    if "date" in frame.columns and "timestamp" not in frame.columns:
        frame = frame.rename(columns={"date": "timestamp"})
    if "ts" in frame.columns and "timestamp" not in frame.columns:
        frame = frame.rename(columns={"ts": "timestamp"})
    if "timestamp" not in frame.columns:
        if frame.index.name is not None:
            frame = frame.reset_index().rename(columns={frame.index.name: "timestamp"})
        else:
            frame = frame.reset_index().rename(columns={"index": "timestamp"})
    for column in OHLCV_COLUMNS:
        if column not in frame.columns:
            frame[column] = 0.0 if column == "volume" else pd.NA
    frame = frame[OHLCV_COLUMNS]
    frame["timestamp"] = pd.to_datetime(frame["timestamp"]).dt.tz_localize(None)
    numeric_columns = ["open", "high", "low", "close", "volume"]
    frame[numeric_columns] = frame[numeric_columns].astype(float)
    return frame.dropna(subset=["open", "high", "low", "close"]).sort_values("timestamp")


def resample_ohlcv(candles: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample 1-minute candles to a larger pandas timeframe such as `5m`."""
    frame = normalize_candles(candles)
    if frame.empty:
        return frame
    if not timeframe.endswith("m"):
        raise ValueError(f"unsupported timeframe: {timeframe!r}")
    rule = timeframe.replace("m", "min")
    return (
        frame.set_index("timestamp")
        .resample(rule, label="right", closed="right")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
