"""Strategy authoring primitives shared by backtest and paper trading."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

import pandas as pd


Cadence = Literal["bar", "daily", "weekly", "signal"]
RunMode = Literal["backtest", "paper", "live"]


class OrderSide(StrEnum):
    """Order direction."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    """Execution type understood by the future broker simulator."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SLM = "SL-M"


class ProductType(StrEnum):
    """OpenAlgo product codes."""

    CNC = "CNC"
    MIS = "MIS"
    NRML = "NRML"


@dataclass(slots=True)
class Position:
    """Current strategy position snapshot."""

    symbol: str
    quantity: int = 0
    average_price: float = 0.0
    last_price: float = 0.0

    @property
    def is_open(self) -> bool:
        """Return whether the position has non-zero exposure."""
        return self.quantity != 0

    @property
    def market_value(self) -> float:
        """Return mark-to-market value."""
        return self.quantity * self.last_price


@dataclass(slots=True)
class OrderIntent:
    """Strategy-side order request produced by `go_long` / `go_short`."""

    side: OrderSide
    symbol: str
    quantity: int
    order_type: OrderType = OrderType.MARKET
    product: ProductType = ProductType.MIS
    price: float | None = None
    trigger_price: float | None = None
    tag: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_actionable(self) -> bool:
        """Return whether this intent has a positive quantity."""
        return self.quantity > 0


@dataclass(slots=True)
class StrategyContext:
    """Mutable runtime context injected by an engine before each bar."""

    symbol: str
    timestamp: datetime
    candles: pd.DataFrame
    position: Position
    balance: float
    portfolio_value: float
    mode: RunMode = "backtest"
    exchange: str = "NSE"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def price(self) -> float:
        """Return the latest close price from `candles`."""
        if self.candles.empty:
            return 0.0
        row = self.candles.iloc[-1]
        for column in ("close", "Close", "ltp", "LTP"):
            if column in row:
                return float(row[column])
        return 0.0


class BaseStrategy(ABC):
    """Jesse-style strategy base class.

    Engines call hooks in this order: `before`, signal checks, order creation,
    broker simulation/submission, `update_position`, `after`.
    """

    name: str = "base"
    timeframe: str = "1m"
    cadence: Cadence = "bar"
    exchange: str = "NSE"
    product: ProductType = ProductType.MIS

    def __init__(self) -> None:
        self.context: StrategyContext | None = None

    def set_context(self, context: StrategyContext) -> None:
        """Inject runtime state for the next hook invocation."""
        self.context = context

    @property
    def symbol(self) -> str:
        return self._ctx.symbol

    @property
    def timestamp(self) -> datetime:
        return self._ctx.timestamp

    @property
    def price(self) -> float:
        return self._ctx.price

    @property
    def candles(self) -> pd.DataFrame:
        return self._ctx.candles

    @property
    def position(self) -> Position:
        return self._ctx.position

    @property
    def balance(self) -> float:
        return self._ctx.balance

    @property
    def portfolio_value(self) -> float:
        return self._ctx.portfolio_value

    @property
    def is_backtesting(self) -> bool:
        return self._ctx.mode == "backtest"

    @property
    def is_papertrading(self) -> bool:
        return self._ctx.mode == "paper"

    @property
    def is_livetrading(self) -> bool:
        return self._ctx.mode == "live"

    @property
    def _ctx(self) -> StrategyContext:
        if self.context is None:
            raise RuntimeError("StrategyContext has not been set. Engine must call set_context().")
        return self.context

    def before(self) -> None:
        """Optional hook before signal evaluation."""

    def after(self) -> None:
        """Optional hook after broker simulation/submission."""

    def update_position(self) -> None:
        """Optional hook after the engine refreshes `self.position`."""

    def should_cancel_entry(self) -> bool:
        """Optional hook for pending-entry cancellation."""
        return False

    def on_open_position(self) -> None:
        """Optional hook fired when a position opens."""

    def on_close_position(self) -> None:
        """Optional hook fired when a position closes."""

    @abstractmethod
    def should_long(self) -> bool:
        """Return whether the strategy wants long exposure."""

    @abstractmethod
    def should_short(self) -> bool:
        """Return whether the strategy wants short exposure."""

    @abstractmethod
    def go_long(self) -> OrderIntent | None:
        """Return the long-side order intent."""

    @abstractmethod
    def go_short(self) -> OrderIntent | None:
        """Return the short-side order intent."""

    def quantity_for_fraction(self, fraction: float) -> int:
        """Return whole-share quantity for a portfolio fraction at current price."""
        if self.price <= 0 or fraction <= 0:
            return 0
        budget = self.portfolio_value * min(fraction, 1.0)
        return int(budget // self.price)

    def market_order(
        self,
        side: OrderSide,
        quantity: int,
        *,
        tag: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OrderIntent:
        """Build a market order for the current symbol."""
        return OrderIntent(
            side=side,
            symbol=self.symbol,
            quantity=quantity,
            product=self.product,
            tag=tag,
            metadata=metadata or {},
        )