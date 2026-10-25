"""High-level backtest runner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
import pandas as pd

from nifty_ai.engine.broker_sim import BrokerConfig, SimulatedBroker
from nifty_ai.engine.candle_store import normalize_candles
from nifty_ai.engine.event_loop import BacktestEventLoop
from nifty_ai.engine.portfolio import Fill, Portfolio
from nifty_ai.strategy.base import BaseStrategy


@dataclass(slots=True)
class BacktestResult:
    """Completed backtest result."""

    run_id: str
    symbol: str
    exchange: str
    start: datetime
    end: datetime
    initial_cash: float
    final_equity: float
    fills: list[Fill]
    equity_curve: pd.DataFrame

    @property
    def net_pnl(self) -> float:
        """Return final equity less starting capital."""
        return self.final_equity - self.initial_cash

    @property
    def return_pct(self) -> float:
        """Return percentage gain/loss."""
        return (self.net_pnl / self.initial_cash) * 100


class BacktestRunner:
    """Convenience wrapper around broker, portfolio, and event loop."""

    def __init__(
        self,
        strategy: BaseStrategy,
        *,
        symbol: str,
        exchange: str = "NSE",
        capital: float = 1_000_000,
        broker_config: BrokerConfig | None = None,
    ) -> None:
        self.strategy = strategy
        self.symbol = symbol
        self.exchange = exchange
        self.capital = capital
        self.broker_config = broker_config or BrokerConfig()

    def run(self, candles: pd.DataFrame) -> BacktestResult:
        """Run a single-symbol backtest over a candle DataFrame."""
        normalized = normalize_candles(candles)
        if normalized.empty:
            raise ValueError("candles must not be empty")
        portfolio = Portfolio(self.capital)
        broker = SimulatedBroker(self.broker_config)
        loop = BacktestEventLoop(self.strategy, broker, portfolio)
        result = loop.run(self.symbol, normalized, exchange=self.exchange)
        timestamps = pd.to_datetime(normalized["timestamp"])
        return BacktestResult(
            run_id=str(uuid4()),
            symbol=self.symbol,
            exchange=self.exchange,
            start=timestamps.min().to_pydatetime(),
            end=timestamps.max().to_pydatetime(),
            initial_cash=self.capital,
            final_equity=result.final_equity,
            fills=result.fills,
            equity_curve=result.equity_curve,
        )