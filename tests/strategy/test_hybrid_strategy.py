from __future__ import annotations

from datetime import datetime

import pandas as pd

from nifty_ai.strategy import HybridStrategy, OrderSide, Position, StrategyContext


class BreakoutStrategy(HybridStrategy):
    def python_should_long(self) -> bool:
        return self.price > 105


def _context(price: float) -> StrategyContext:
    return StrategyContext(
        symbol="NIFTY",
        timestamp=datetime(2026, 5, 27, 9, 15),
        candles=pd.DataFrame([{"close": price}]),
        position=Position("NIFTY"),
        balance=100_000,
        portfolio_value=100_000,
    )


def test_hybrid_strategy_uses_python_signal_and_risk_overlay():
    rejected = BreakoutStrategy(risk_overlay=lambda strategy, side: False)
    rejected.set_context(_context(110))
    assert not rejected.should_long()

    accepted = BreakoutStrategy(risk_overlay=lambda strategy, side: side == OrderSide.BUY)
    accepted.set_context(_context(110))
    assert accepted.should_long()
    order = accepted.go_long()
    assert order is not None
    assert order.quantity == 181