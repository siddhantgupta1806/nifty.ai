from __future__ import annotations

from datetime import datetime

import pandas as pd

from nifty_ai.strategy import BaseStrategy, OrderSide, Position, StrategyContext


class BuyDipStrategy(BaseStrategy):
    name = "buy_dip"

    def should_long(self) -> bool:
        return self.price < 100

    def should_short(self) -> bool:
        return False

    def go_long(self):
        return self.market_order(OrderSide.BUY, self.quantity_for_fraction(0.5))

    def go_short(self):
        return None


def test_base_strategy_context_properties_and_order_sizing():
    candles = pd.DataFrame([{"close": 95.0}])
    strategy = BuyDipStrategy()
    strategy.set_context(
        StrategyContext(
            symbol="RELIANCE",
            timestamp=datetime(2026, 5, 27, 9, 15),
            candles=candles,
            position=Position("RELIANCE"),
            balance=100_000,
            portfolio_value=100_000,
        )
    )

    assert strategy.is_backtesting
    assert strategy.should_long()
    order = strategy.go_long()
    assert order is not None
    assert order.side == OrderSide.BUY
    assert order.symbol == "RELIANCE"
    assert order.quantity == 526