from __future__ import annotations

from datetime import datetime

from nifty_ai.engine.portfolio import Fill, Portfolio
from nifty_ai.strategy import OrderSide


def test_portfolio_applies_long_round_trip():
    portfolio = Portfolio(100_000)
    portfolio.apply_fill(Fill("RELIANCE", OrderSide.BUY, 10, 100.0, datetime(2026, 5, 27, 9, 15)))
    portfolio.mark_to_market("RELIANCE", 110.0)

    assert portfolio.cash == 99_000
    assert portfolio.equity() == 100_100
    assert portfolio.unrealized_pnl() == 100

    portfolio.apply_fill(Fill("RELIANCE", OrderSide.SELL, 10, 110.0, datetime(2026, 5, 27, 9, 16)))

    assert portfolio.get_position("RELIANCE").quantity == 0
    assert portfolio.realized_pnl == 100
    assert portfolio.equity() == 100_100
