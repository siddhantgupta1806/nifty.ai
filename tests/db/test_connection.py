from __future__ import annotations

from nifty_ai.db import get_db, table_names


def test_get_db_creates_expected_tables(tmp_path):
    with get_db(tmp_path / "nifty.duckdb") as conn:
        names = table_names(conn)

    assert "trade_ledger" in names
    assert "daily_equity_curve" in names
    assert "agent_decisions" in names
    assert "agent_transcripts" in names
    assert "candle_cache" in names
