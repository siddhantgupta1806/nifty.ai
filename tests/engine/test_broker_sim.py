from __future__ import annotations

from datetime import datetime

import pytest

from nifty_ai.engine.broker_sim import Bar, BrokerConfig, SimulatedBroker
from nifty_ai.engine.portfolio import Fill, Portfolio
from nifty_ai.strategy import OrderIntent, OrderSide, OrderType


def _bar(hour: int = 9, minute: int = 15) -> Bar:
    return Bar(datetime(2026, 5, 27, hour, minute), open=100, high=110, low=95, close=105)


def test_market_order_fills_at_close_with_slippage():
    broker = SimulatedBroker(BrokerConfig(commission_bps=0, slippage_bps=10))
    fill = broker.simulate_order(OrderIntent(OrderSide.BUY, "RELIANCE", 10), _bar())

    assert fill is not None
    assert fill.price == pytest.approx(105.105)
    assert fill.slippage == pytest.approx(1.05)


def test_limit_order_requires_bar_touch():
    broker = SimulatedBroker(BrokerConfig(commission_bps=0))
    fill = broker.simulate_order(
        OrderIntent(OrderSide.BUY, "RELIANCE", 10, order_type=OrderType.LIMIT, price=98),
        _bar(),
    )
    miss = broker.simulate_order(
        OrderIntent(OrderSide.BUY, "RELIANCE", 10, order_type=OrderType.LIMIT, price=90),
        _bar(),
    )

    assert fill is not None
    assert fill.price == 98
    assert miss is None


def test_lot_size_enforced_for_options():
    broker = SimulatedBroker(BrokerConfig(enforce_lot_sizes=True))

    with pytest.raises(ValueError, match="lot size 75"):
        broker.simulate_order(OrderIntent(OrderSide.BUY, "NIFTY25MAY2525000CE", 10), _bar())


def test_square_off_flattens_open_position_after_mis_time():
    broker = SimulatedBroker(BrokerConfig(commission_bps=0))
    portfolio = Portfolio(100_000)
    portfolio.apply_fill(Fill("RELIANCE", OrderSide.BUY, 10, 100, datetime(2026, 5, 27, 9, 15)))

    fills = broker.square_off_fills(portfolio, _bar(15, 20))

    assert len(fills) == 1
    assert fills[0].side == OrderSide.SELL
    assert fills[0].tag == "mis-square-off"
