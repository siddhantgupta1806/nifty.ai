from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from nifty_ai.strategy import AgentStrategy, OrderSide, Position, StrategyContext


@dataclass
class Recommendation:
    signal: str
    size_fraction: float


class FakeGraph:
    def __init__(self) -> None:
        self.calls = 0

    def propagate(self, symbol: str, trade_date: str):
        self.calls += 1
        return {}, Recommendation(signal="BUY", size_fraction=0.1)


def test_agent_strategy_caches_decisions_by_symbol_and_date():
    graph = FakeGraph()
    strategy = AgentStrategy(graph=graph)
    strategy.set_context(
        StrategyContext(
            symbol="TCS",
            timestamp=datetime(2026, 5, 27, 9, 15),
            candles=pd.DataFrame([{"close": 100.0}]),
            position=Position("TCS"),
            balance=100_000,
            portfolio_value=100_000,
        )
    )

    assert strategy.should_long()
    assert strategy.should_long()
    assert graph.calls == 1
    order = strategy.go_long()
    assert order is not None
    assert order.side == OrderSide.BUY
    assert order.quantity == 100