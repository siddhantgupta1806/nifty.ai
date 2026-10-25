from __future__ import annotations

from datetime import datetime

from nifty_ai.db import get_db
from nifty_ai.reporting import generate_report, render_summary_table, summarize_run


def test_summarize_run_and_basic_html_report(tmp_path):
    db_path = tmp_path / "nifty.duckdb"
    with get_db(db_path) as conn:
        conn.execute(
            "INSERT INTO daily_equity_curve (run_id, timestamp, equity, cash, realized_pnl, unrealized_pnl) VALUES (?, ?, ?, ?, ?, ?)",
            ["run-1", datetime(2026, 5, 27, 15, 30), 100_000, 100_000, 0, 0],
        )
        conn.execute(
            "INSERT INTO daily_equity_curve (run_id, timestamp, equity, cash, realized_pnl, unrealized_pnl) VALUES (?, ?, ?, ?, ?, ?)",
            ["run-1", datetime(2026, 5, 28, 15, 30), 102_000, 102_000, 2_000, 0],
        )
        conn.execute(
            "INSERT INTO trade_ledger (run_id, timestamp, strategy_name, symbol, exchange, side, quantity, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ["run-1", datetime(2026, 5, 28, 9, 15), "test", "RELIANCE", "NSE", "BUY", 10, 100],
        )
        stats = summarize_run(conn, "run-1")

    assert stats.net_pnl == 2_000
    assert stats.return_pct == 2.0
    assert stats.total_trades == 1
    assert render_summary_table(stats).row_count == 5
    out = generate_report(db_path, "run-1", tmp_path / "report.html")
    assert "<html" in out.read_text(encoding="utf-8").lower()