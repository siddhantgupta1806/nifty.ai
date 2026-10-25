from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from nifty_ai.mcp.server import nifty_status, run_csv_backtest


def test_nifty_status_tool_returns_runtime_shape():
    status = nifty_status()

    assert "version" in status
    assert "openalgo_host" in status


def test_run_csv_backtest_tool(tmp_path):
    strategy_file = tmp_path / "strategy.py"
    strategy_file.write_text(
        "from nifty_ai.strategy import BaseStrategy, OrderSide\n"
        "class DemoStrategy(BaseStrategy):\n"
        "    def __init__(self): super().__init__(); self.done = False\n"
        "    def should_long(self): return not self.done\n"
        "    def should_short(self): return False\n"
        "    def go_long(self): self.done = True; return self.market_order(OrderSide.BUY, 10)\n"
        "    def go_short(self): return None\n",
        encoding="utf-8",
    )
    start = datetime(2026, 5, 27, 9, 15)
    candles = pd.DataFrame(
        [
            {"timestamp": start + timedelta(minutes=i), "open": 100 + i, "high": 101 + i, "low": 99 + i, "close": 100 + i, "volume": 1000}
            for i in range(3)
        ]
    )
    csv_path = tmp_path / "candles.csv"
    candles.to_csv(csv_path, index=False)

    result = run_csv_backtest(
        str(strategy_file),
        str(csv_path),
        "RELIANCE",
        capital=100_000,
        commission_bps=0,
        slippage_bps=0,
    )

    assert result["final_equity"] == 100_020
    assert result["fills"] == 1