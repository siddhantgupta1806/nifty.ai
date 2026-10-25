"""Paper-trading runner over OpenAlgo Analyzer Mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd

from nifty_ai.openalgo import analyzer
from nifty_ai.openalgo.client import NiftyOpenAlgoClient
from nifty_ai.strategy.base import BaseStrategy, OrderIntent, OrderSide, Position, StrategyContext


class PaperPreflightError(RuntimeError):
    """Raised when paper trading cannot start safely."""


@dataclass(slots=True)
class PaperConfig:
    """Runtime options for paper trading."""

    strategy_name: str = "nifty-ai-paper"
    auto_enable_analyzer: bool = True
    auto_disable_analyzer: bool = False
    min_cash: float = 0.0


class PaperRunner:
    """Run a strategy against OpenAlgo Analyzer Mode."""

    def __init__(
        self,
        strategy: BaseStrategy,
        client: NiftyOpenAlgoClient,
        *,
        symbol: str,
        exchange: str = "NSE",
        config: PaperConfig | None = None,
    ) -> None:
        self.strategy = strategy
        self.client = client
        self.symbol = symbol
        self.exchange = exchange
        self.config = config or PaperConfig()
        self._candles = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    def start(self) -> None:
        """Enable/check Analyzer Mode and account state."""
        if self.config.auto_enable_analyzer:
            analyzer.enable_analyzer(self.client)
        if not analyzer.is_analyzer_on(self.client):
            raise PaperPreflightError("OpenAlgo Analyzer Mode is not enabled")
        funds = self.client.funds() or {}
        available = float(funds.get("availablecash") or funds.get("available_cash") or funds.get("cash") or 0.0)
        if available < self.config.min_cash:
            raise PaperPreflightError(f"available Analyzer cash {available} is below {self.config.min_cash}")

    def stop(self) -> None:
        """Optionally disable Analyzer Mode on shutdown."""
        if self.config.auto_disable_analyzer:
            analyzer.disable_analyzer(self.client)

    def process_bar(self, bar: dict[str, Any] | pd.Series) -> list[dict[str, Any]]:
        """Evaluate strategy on one completed paper-trading bar and submit orders."""
        row = dict(bar)
        row["timestamp"] = pd.Timestamp(row.get("timestamp") or row.get("ts")).to_pydatetime()
        self._candles = pd.concat([self._candles, pd.DataFrame([row])], ignore_index=True)
        close = float(row["close"])
        position = self._position_snapshot(close)
        funds = self.client.funds() or {}
        balance = float(funds.get("availablecash") or funds.get("available_cash") or funds.get("cash") or 0.0)
        context = StrategyContext(
            symbol=self.symbol,
            exchange=self.exchange,
            timestamp=row["timestamp"],
            candles=self._candles.copy(),
            position=position,
            balance=balance,
            portfolio_value=balance + position.market_value,
            mode="paper",
        )
        self.strategy.set_context(context)
        self.strategy.before()
        responses = [self.submit_order(intent) for intent in self._collect_intents() if intent.is_actionable()]
        self.strategy.update_position()
        self.strategy.after()
        return responses

    def run_bars(self, bars: Iterable[dict[str, Any] | pd.Series]) -> list[dict[str, Any]]:
        """Run deterministic bar input through the paper runner."""
        self.start()
        responses: list[dict[str, Any]] = []
        try:
            for bar in bars:
                responses.extend(self.process_bar(bar))
        finally:
            self.stop()
        return responses

    def submit_order(self, intent: OrderIntent) -> dict[str, Any]:
        """Submit an `OrderIntent` to OpenAlgo Analyzer Mode."""
        return self.client.placeorder(
            strategy=self.config.strategy_name,
            symbol=intent.symbol,
            exchange=self.exchange,
            action="BUY" if intent.side == OrderSide.BUY else "SELL",
            quantity=intent.quantity,
            pricetype=intent.order_type.value,
            price=float(intent.price or 0.0),
            trigger_price=float(intent.trigger_price or 0.0),
            product=intent.product.value,
        )

    def _collect_intents(self) -> list[OrderIntent]:
        intents: list[OrderIntent] = []
        if self.strategy.should_long():
            intents.extend(_as_list(self.strategy.go_long()))
        if self.strategy.should_short():
            intents.extend(_as_list(self.strategy.go_short()))
        return intents

    def _position_snapshot(self, last_price: float) -> Position:
        for item in self.client.positionbook() or []:
            if str(item.get("symbol") or "").upper() != self.symbol.upper():
                continue
            qty = int(float(item.get("quantity") or item.get("netqty") or 0))
            avg = float(item.get("average_price") or item.get("avgprice") or 0.0)
            return Position(symbol=self.symbol, quantity=qty, average_price=avg, last_price=last_price)
        return Position(symbol=self.symbol, last_price=last_price)


def _as_list(value: OrderIntent | list[OrderIntent] | tuple[OrderIntent, ...] | None) -> list[OrderIntent]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
