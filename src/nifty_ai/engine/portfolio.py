"""Portfolio accounting for simulated backtests."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from nifty_ai.strategy.base import OrderSide, Position


@dataclass(slots=True)
class Fill:
    """Executed order fill."""

    symbol: str
    side: OrderSide
    quantity: int
    price: float
    timestamp: datetime
    commission: float = 0.0
    slippage: float = 0.0
    tag: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def gross_value(self) -> float:
        """Return fill notional before costs."""
        return self.quantity * self.price


@dataclass(slots=True)
class EquitySnapshot:
    """Point-in-time portfolio equity row."""

    timestamp: datetime
    cash: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float


class Portfolio:
    """Cash, position, and equity accounting for a backtest run."""

    def __init__(self, initial_cash: float) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.positions: dict[str, Position] = {}
        self.realized_pnl = 0.0
        self.fills: list[Fill] = []
        self.snapshots: list[EquitySnapshot] = []

    def get_position(self, symbol: str) -> Position:
        """Return a mutable position snapshot for `symbol`."""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def mark_to_market(self, symbol: str, price: float) -> None:
        """Update the latest price for a symbol."""
        self.get_position(symbol).last_price = float(price)

    def apply_fill(self, fill: Fill) -> None:
        """Apply a fill to cash and position state."""
        if fill.quantity <= 0:
            raise ValueError("fill quantity must be positive")
        pos = self.get_position(fill.symbol)
        signed_qty = fill.quantity if fill.side == OrderSide.BUY else -fill.quantity
        old_qty = pos.quantity
        old_avg = pos.average_price

        if fill.side == OrderSide.BUY:
            self.cash -= fill.gross_value + fill.commission
        else:
            self.cash += fill.gross_value - fill.commission

        self._update_position_average(pos, old_qty, old_avg, signed_qty, fill.price)
        pos.last_price = fill.price
        self.fills.append(fill)

    def _update_position_average(
        self,
        pos: Position,
        old_qty: int,
        old_avg: float,
        signed_fill_qty: int,
        fill_price: float,
    ) -> None:
        """Update average price and realized P&L for long/short transitions."""
        new_qty = old_qty + signed_fill_qty

        if old_qty == 0 or (old_qty > 0 and signed_fill_qty > 0) or (old_qty < 0 and signed_fill_qty < 0):
            total_abs_qty = abs(old_qty) + abs(signed_fill_qty)
            pos.average_price = (
                ((abs(old_qty) * old_avg) + (abs(signed_fill_qty) * fill_price)) / total_abs_qty
                if total_abs_qty
                else 0.0
            )
            pos.quantity = new_qty
            return

        closing_qty = min(abs(old_qty), abs(signed_fill_qty))
        if old_qty > 0:
            self.realized_pnl += (fill_price - old_avg) * closing_qty
        else:
            self.realized_pnl += (old_avg - fill_price) * closing_qty

        pos.quantity = new_qty
        if new_qty == 0:
            pos.average_price = 0.0
        elif (old_qty > 0 > new_qty) or (old_qty < 0 < new_qty):
            pos.average_price = fill_price
        else:
            pos.average_price = old_avg

    def unrealized_pnl(self) -> float:
        """Return total unrealized P&L across open positions."""
        total = 0.0
        for pos in self.positions.values():
            if pos.quantity > 0:
                total += (pos.last_price - pos.average_price) * pos.quantity
            elif pos.quantity < 0:
                total += (pos.average_price - pos.last_price) * abs(pos.quantity)
        return total

    def equity(self) -> float:
        """Return current marked portfolio equity."""
        return self.cash + sum(pos.quantity * pos.last_price for pos in self.positions.values())

    def snapshot(self, timestamp: datetime) -> EquitySnapshot:
        """Record and return an equity snapshot."""
        row = EquitySnapshot(
            timestamp=timestamp,
            cash=self.cash,
            equity=self.equity(),
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl(),
        )
        self.snapshots.append(row)
        return row

    def equity_curve(self) -> pd.DataFrame:
        """Return snapshots as a DataFrame."""
        return pd.DataFrame([asdict(snapshot) for snapshot in self.snapshots])
