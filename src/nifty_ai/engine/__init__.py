"""Backtest engine (Phase 5)."""

from nifty_ai.engine.broker_sim import Bar, BrokerConfig, SimulatedBroker
from nifty_ai.engine.candle_store import CandleStore, normalize_candles, resample_ohlcv
from nifty_ai.engine.event_loop import BacktestEventLoop, EventLoopResult
from nifty_ai.engine.portfolio import EquitySnapshot, Fill, Portfolio
from nifty_ai.engine.runner import BacktestResult, BacktestRunner

__all__ = [
    "BacktestEventLoop",
    "BacktestResult",
    "BacktestRunner",
    "Bar",
    "BrokerConfig",
    "CandleStore",
    "EquitySnapshot",
    "EventLoopResult",
    "Fill",
    "Portfolio",
    "SimulatedBroker",
    "normalize_candles",
    "resample_ohlcv",
]