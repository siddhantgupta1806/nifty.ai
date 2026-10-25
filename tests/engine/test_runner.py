from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from nifty_ai.engine import BacktestRunner, BrokerConfig
from nifty_ai.strategy import BaseStrategy, OrderSide


class BuyAndHoldOnce(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.done = False

    def should_long(self) -> bool:
        return not self.done

    def should_short(self) -> bool:
        return False

    def go_long(self):
        self.done = True
        return self.market_order(OrderSide.BUY, 10)

    def go_short(self):
        return None


def test_backtest_runner_executes_single_symbol_strategy():
    start = datetime(2026, 5, 27, 9, 15)
    candles = pd.DataFrame(
        [
            {
                "timestamp": start + timedelta(minutes=i),
                "open": 100 + i,
                "high": 101 + i,
                "low": 99 + i,
                "close": 100 + i,
                "volume": 1000,
            }
            for i in range(3)
        ]
    )
    runner = BacktestRunner(
        BuyAndHoldOnce(),
        symbol="RELIANCE",
        capital=100_000,
        broker_config=BrokerConfig(commission_bps=0, slippage_bps=0, auto_square_off_mis=False),
    )

    result = runner.run(candles)

    assert len(result.fills) == 1
    assert result.final_equity == 100_020
    assert result.net_pnl == 20
    assert len(result.equity_curve) == 3