"""Simple EMA crossover strategy for examples and smoke tests."""

from __future__ import annotations

from nifty_ai.strategy import BaseStrategy, OrderSide


class EMACrossStrategy(BaseStrategy):
    """Buy once when fast EMA crosses above slow EMA."""

    name = "ema_cross"
    timeframe = "1m"

    def should_long(self) -> bool:
        if self.position.is_open or len(self.candles) < 8:
            return False
        close = self.candles["close"]
        fast = close.ewm(span=3).mean()
        slow = close.ewm(span=8).mean()
        return bool(fast.iloc[-2] <= slow.iloc[-2] and fast.iloc[-1] > slow.iloc[-1])

    def should_short(self) -> bool:
        return False

    def go_long(self):
        quantity = self.quantity_for_fraction(0.25)
        return self.market_order(OrderSide.BUY, quantity, tag="ema-cross") if quantity else None

    def go_short(self):
        return None
