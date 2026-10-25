"""Hybrid human-signal + agent-risk strategy base."""

from __future__ import annotations

from typing import Any

from nifty_ai.strategy.base import BaseStrategy, OrderIntent, OrderSide


class HybridStrategy(BaseStrategy):
    """Run fast Python signals, then allow an agent risk overlay to veto trades.

    Subclasses override `python_should_long` / `python_should_short` for their
    deterministic signal logic. The optional `risk_overlay` callable receives
    `(strategy, side)` and returns a bool.
    """

    name = "hybrid"
    cadence = "signal"
    default_size_fraction = 0.20

    def __init__(self, risk_overlay: Any | None = None) -> None:
        super().__init__()
        self.risk_overlay = risk_overlay

    def python_should_long(self) -> bool:
        """Return the deterministic long signal; subclasses usually override."""
        return False

    def python_should_short(self) -> bool:
        """Return the deterministic short signal; subclasses usually override."""
        return False

    def risk_allows(self, side: OrderSide) -> bool:
        """Return whether the optional risk overlay approves the trade."""
        if self.risk_overlay is None:
            return True
        return bool(self.risk_overlay(self, side))

    def should_long(self) -> bool:
        """Return true when Python signal and risk overlay both allow BUY."""
        return self.python_should_long() and self.risk_allows(OrderSide.BUY)

    def should_short(self) -> bool:
        """Return true when Python signal and risk overlay both allow SELL."""
        return self.python_should_short() and self.risk_allows(OrderSide.SELL)

    def go_long(self) -> OrderIntent | None:
        """Create the default hybrid BUY order."""
        quantity = self.quantity_for_fraction(self.default_size_fraction)
        if quantity <= 0:
            return None
        return self.market_order(OrderSide.BUY, quantity, tag="hybrid-long")

    def go_short(self) -> OrderIntent | None:
        """Create the default hybrid SELL order."""
        quantity = self.quantity_for_fraction(self.default_size_fraction)
        if quantity <= 0:
            return None
        return self.market_order(OrderSide.SELL, quantity, tag="hybrid-short")