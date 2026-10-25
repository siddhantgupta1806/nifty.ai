"""Bar-by-bar backtest event loop."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
import pandas as pd

from nifty_ai.engine.broker_sim import Bar, SimulatedBroker
from nifty_ai.engine.candle_store import normalize_candles, resample_ohlcv
from nifty_ai.engine.portfolio import Fill, Portfolio
from nifty_ai.openalgo.calendar import EQUITY_CLOSE, EQUITY_OPEN
from nifty_ai.strategy.base import BaseStrategy, OrderIntent, StrategyContext


@dataclass(slots=True)
class EventLoopResult:
    """Raw event-loop output."""

    fills: list[Fill]
    equity_curve: pd.DataFrame
    final_equity: float


class BacktestEventLoop:
    """Drive a strategy through historical candles."""

    def __init__(self, strategy: BaseStrategy, broker: SimulatedBroker, portfolio: Portfolio) -> None:
        self.strategy = strategy
        self.broker = broker
        self.portfolio = portfolio

    def run(self, symbol: str, candles: pd.DataFrame, *, exchange: str = "NSE") -> EventLoopResult:
        """Replay candles and return fills/equity curve."""
        one_minute = normalize_candles(candles)
        all_fills: list[Fill] = []
        for _, row in one_minute.iterrows():
            bar = Bar.from_series(row)
            if not _is_regular_equity_bar(bar.timestamp):
                continue
            self.portfolio.mark_to_market(symbol, bar.close)
            visible = _visible_candles(one_minute, bar.timestamp, self.strategy.timeframe)
            context = StrategyContext(
                symbol=symbol,
                exchange=exchange,
                timestamp=bar.timestamp,
                candles=visible,
                position=self.portfolio.get_position(symbol),
                balance=self.portfolio.cash,
                portfolio_value=self.portfolio.equity(),
                mode="backtest",
            )
            self.strategy.set_context(context)
            self.strategy.before()
            fills = self._execute_intents(self._strategy_intents(), bar)
            square_off = self.broker.square_off_fills(self.portfolio, bar)
            for fill in [*fills, *square_off]:
                self.portfolio.apply_fill(fill)
                all_fills.append(fill)
            self.strategy.update_position()
            self.strategy.after()
            self.portfolio.snapshot(bar.timestamp)
        return EventLoopResult(
            fills=all_fills,
            equity_curve=self.portfolio.equity_curve(),
            final_equity=self.portfolio.equity(),
        )

    def _strategy_intents(self) -> list[OrderIntent]:
        intents: list[OrderIntent] = []
        if self.strategy.should_long():
            intents.extend(_as_list(self.strategy.go_long()))
        if self.strategy.should_short():
            intents.extend(_as_list(self.strategy.go_short()))
        return intents

    def _execute_intents(self, intents: Iterable[OrderIntent], bar: Bar) -> list[Fill]:
        fills: list[Fill] = []
        for intent in intents:
            if not intent.is_actionable():
                continue
            fill = self.broker.simulate_order(intent, bar)
            if fill is not None:
                fills.append(fill)
        return fills


def _as_list(value: OrderIntent | list[OrderIntent] | tuple[OrderIntent, ...] | None) -> list[OrderIntent]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _visible_candles(candles: pd.DataFrame, timestamp: datetime, timeframe: str) -> pd.DataFrame:
    visible = candles[candles["timestamp"] <= pd.Timestamp(timestamp)]
    if timeframe == "1m":
        return visible
    return resample_ohlcv(visible, timeframe)


def _is_regular_equity_bar(timestamp: datetime) -> bool:
    t = timestamp.time()
    return EQUITY_OPEN <= t <= EQUITY_CLOSE
