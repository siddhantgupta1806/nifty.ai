from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from typer.testing import CliRunner

from nifty_ai.cli.main import app
from nifty_ai.db import get_db


runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "Nifty.AI v" in result.output


def test_backtest_command_from_strategy_and_csv(tmp_path):
    strategy_file = tmp_path / "strategy.py"
    strategy_file.write_text(
        "from nifty_ai.strategy import BaseStrategy, OrderSide\n"
        "class DemoStrategy(BaseStrategy):\n"
        "    def __init__(self):\n"
        "        super().__init__(); self.done = False\n"
        "    def should_long(self): return not self.done\n"
        "    def should_short(self): return False\n"
        "    def go_long(self):\n"
        "        self.done = True; return self.market_order(OrderSide.BUY, 10)\n"
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

    result = runner.invoke(
        app,
        [
            "backtest",
            "--strategy",
            str(strategy_file),
            "--candles",
            str(csv_path),
            "--symbol",
            "RELIANCE",
            "--capital",
            "100000",
            "--commission-bps",
            "0",
            "--slippage-bps",
            "0",
            "--persist-db",
            str(db_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "final_equity=100020.00" in result.output
    with get_db(db_path) as conn:
        assert conn.execute("SELECT count(*) FROM trade_ledger").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM daily_equity_curve").fetchone()[0] == 3


def test_report_command(tmp_path):
    db_path = tmp_path / "runs.duckdb"
    with get_db(db_path) as conn:
        conn.execute(
            "INSERT INTO daily_equity_curve (run_id, timestamp, equity, cash, realized_pnl, unrealized_pnl) VALUES (?, ?, ?, ?, ?, ?)",
            ["run-1", datetime(2026, 5, 27, 15, 30), 100_000, 100_000, 0, 0],
        )
        conn.execute(
            "INSERT INTO daily_equity_curve (run_id, timestamp, equity, cash, realized_pnl, unrealized_pnl) VALUES (?, ?, ?, ?, ?, ?)",
            ["run-1", datetime(2026, 5, 28, 15, 30), 101_000, 101_000, 1_000, 0],
        )
    out = tmp_path / "report.html"

    result = runner.invoke(app, ["report", "--run-id", "run-1", "--db", str(db_path), "--out", str(out)])

    assert result.exit_code == 0, result.output
    assert out.exists()