"""Pure-agent strategy adapter."""

from __future__ import annotations

from typing import Any

from nifty_ai.agents.graph_factory import build_nifty_graph
from nifty_ai.strategy.base import BaseStrategy, OrderIntent, OrderSide


class AgentStrategy(BaseStrategy):
    """Run the full TradingAgents debate and translate the recommendation."""

    name = "agent"
    cadence = "daily"
    default_size_fraction = 0.25

    def __init__(self, graph: Any | None = None, *, selected_analysts: list[str] | None = None) -> None:
        super().__init__()
        self._graph = graph
        self._selected_analysts = selected_analysts
        self._decision_cache: dict[tuple[str, str], Any] = {}

    @property
    def graph(self) -> Any:
        """Build the graph lazily so tests and human strategies stay light."""
        if self._graph is None:
            self._graph = build_nifty_graph(selected_analysts=self._selected_analysts)
        return self._graph

    def recommendation(self) -> Any:
        """Return the cached TradingAgents recommendation for current symbol/date."""
        trade_date = self.timestamp.strftime("%Y-%m-%d")
        key = (self.symbol, trade_date)
        if key not in self._decision_cache:
            _, recommendation = self.graph.propagate(self.symbol, trade_date)
            self._decision_cache[key] = recommendation
        return self._decision_cache[key]

    def should_long(self) -> bool:
        """Return true when the agent recommends BUY."""
        return str(getattr(self.recommendation(), "signal", "HOLD")).upper() == "BUY"

    def should_short(self) -> bool:
        """Return true when the agent recommends SELL."""
        return str(getattr(self.recommendation(), "signal", "HOLD")).upper() == "SELL"

    def _size_fraction(self) -> float:
        value = getattr(self.recommendation(), "size_fraction", self.default_size_fraction)
        try:
            return float(value)
        except (TypeError, ValueError):
            return self.default_size_fraction

    def go_long(self) -> OrderIntent | None:
        """Create a BUY order sized by the agent's recommendation."""
        quantity = self.quantity_for_fraction(self._size_fraction())
        if quantity <= 0:
            return None
        return self.market_order(OrderSide.BUY, quantity, tag="agent-long")

    def go_short(self) -> OrderIntent | None:
        """Create a SELL order sized by the agent's recommendation."""
        quantity = self.quantity_for_fraction(self._size_fraction())
        if quantity <= 0:
            return None
        return self.market_order(OrderSide.SELL, quantity, tag="agent-short")