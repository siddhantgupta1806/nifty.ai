from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from fastapi.testclient import TestClient

from nifty_ai.web.app import create_app


def test_web_status_and_index():
    client = TestClient(create_app())

    index = client.get("/")
    status = client.get("/api/status")

    assert index.status_code == 200
    assert "Nifty.AI" in index.text
    assert status.status_code == 200
    assert "version" in status.json()


def test_web_backtest_and_runs(tmp_path):
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
    db_path = tmp_path / "runs.duckdb"
    client = TestClient(create_app())

    response = client.post(
        "/api/backtests",
        json={
            "strategy_path": str(strategy_file),
            "candles_path": str(csv_path),
            "symbol": "RELIANCE",
            "capital": 100_000,
            "commission_bps": 0,
            "slippage_bps": 0,
            "db_path": str(db_path),
        },
    )
    runs = client.get("/api/runs", params={"db_path": str(db_path)})

    assert response.status_code == 200, response.text
    assert response.json()["final_equity"] == 100_020
    assert runs.status_code == 200
    assert len(runs.json()) == 1