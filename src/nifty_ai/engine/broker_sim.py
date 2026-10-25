"""Deterministic simulated broker for bar-by-bar backtests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from nifty_ai.engine.portfolio import Fill, Portfolio
from nifty_ai.openalgo.calendar import MIS_SQUARE_OFF
from nifty_ai.openalgo.symbols import OpenAlgoSymbolError, get_known_lot_size, parse_option_symbol
from nifty_ai.strategy.base import OrderIntent, OrderSide, OrderType, ProductType


@dataclass(slots=True)
class BrokerConfig:
    """Execution-cost knobs for the simulated broker."""

    commission_bps: float = 3.0
    slippage_bps: float = 0.0
    enforce_lot_sizes: bool = True
    auto_square_off_mis: bool = True


@dataclass(slots=True)
class Bar:
    """One OHLCV bar visible to the broker."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @classmethod
    def from_series(cls, row: pd.Series) -> "Bar":
        """Build a bar from a pandas row with common column casing."""
        return cls(
            timestamp=pd.Timestamp(row.get("timestamp", row.name)).to_pydatetime(),
            open=float(row.get("open", row.get("Open"))),
            high=float(row.get("high", row.get("High"))),
            low=float(row.get("low", row.get("Low"))),
            close=float(row.get("close", row.get("Close"))),
            volume=float(row.get("volume", row.get("Volume", 0.0))),
        )


class SimulatedBroker:
    """Fill `OrderIntent`s against OHLC bars."""

    def __init__(self, config: BrokerConfig | None = None) -> None:
        self.config = config or BrokerConfig()

    def simulate_order(self, order: OrderIntent, bar: Bar) -> Fill | None:
        """Return a fill when `order` is executable on `bar`, else None."""
        self._validate_order(order)
        fill_price = self._fill_price(order, bar)
        if fill_price is None:
            return None
        commission = abs(fill_price * order.quantity) * self.config.commission_bps / 10_000
        slippage = abs(fill_price - bar.close) * order.quantity
        return Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=bar.timestamp,
            commission=commission,
            slippage=slippage,
            tag=order.tag,
            metadata={**order.metadata, "product": order.product.value},
        )

    def square_off_fills(self, portfolio: Portfolio, bar: Bar) -> list[Fill]:
        """Return market fills that flatten every open MIS position after square-off."""
        if not self.config.auto_square_off_mis or bar.timestamp.time() < MIS_SQUARE_OFF:
            return []
        fills: list[Fill] = []
        for pos in list(portfolio.positions.values()):
            if not pos.is_open:
                continue
            side = OrderSide.SELL if pos.quantity > 0 else OrderSide.BUY
            order = OrderIntent(
                side=side,
                symbol=pos.symbol,
                quantity=abs(pos.quantity),
                order_type=OrderType.MARKET,
                product=ProductType.MIS,
                tag="mis-square-off",
            )
            fill = self.simulate_order(order, bar)
            if fill is not None:
                fills.append(fill)
        return fills

    def _fill_price(self, order: OrderIntent, bar: Bar) -> float | None:
        if order.order_type == OrderType.MARKET:
            return self._apply_slippage(bar.close, order.side)
        if order.order_type == OrderType.LIMIT:
            if order.price is None:
                return None
            return float(order.price) if bar.low <= order.price <= bar.high else None
        if order.order_type == OrderType.SLM:
            if order.trigger_price is None or not self._triggered(order, bar):
                return None
            return self._apply_slippage(float(order.trigger_price), order.side)
        if order.order_type == OrderType.SL:
            if order.trigger_price is None or order.price is None or not self._triggered(order, bar):
                return None
            return float(order.price) if bar.low <= order.price <= bar.high else None
        return None

    def _apply_slippage(self, price: float, side: OrderSide) -> float:
        bps = self.config.slippage_bps / 10_000
        return price * (1 + bps) if side == OrderSide.BUY else price * (1 - bps)

    @staticmethod
    def _triggered(order: OrderIntent, bar: Bar) -> bool:
        if order.trigger_price is None:
            return False
        if order.side == OrderSide.BUY:
            return bar.high >= order.trigger_price
        return bar.low <= order.trigger_price

    def _validate_order(self, order: OrderIntent) -> None:
        if order.quantity <= 0:
            raise ValueError("order quantity must be positive")
        if not self.config.enforce_lot_sizes:
            return
        lot_size = _known_contract_lot(order.symbol)
        if lot_size and order.quantity % lot_size != 0:
            raise ValueError(f"{order.symbol} quantity must be a multiple of lot size {lot_size}")


def _known_contract_lot(symbol: str) -> int | None:
    """Return a known lot size for common F&O contracts."""
    upper = symbol.upper()
    try:
        parsed = parse_option_symbol(upper)
    except OpenAlgoSymbolError:
        parsed = None
    if parsed is not None:
        return get_known_lot_size(parsed.underlying)
    if upper.endswith("FUT"):
        for underlying in ("BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTY", "SENSEX", "BANKEX"):
            if upper.startswith(underlying):
                return get_known_lot_size(underlying)
    return None
