"""Rich-formatted backtest summaries."""

from __future__ import annotations

from dataclasses import dataclass
import duckdb
import pandas as pd
from rich.table import Table


@dataclass(slots=True)
class SummaryStats:
    """Core performance stats shown in the CLI."""

    run_id: str
    net_pnl: float
    return_pct: float
    max_drawdown_pct: float
    total_trades: int
    agent_invocations: int


def summarize_run(conn: duckdb.DuckDBPyConnection, run_id: str) -> SummaryStats:
    """Compute summary stats from persisted tables."""
    equity = conn.execute(
        "SELECT timestamp, equity FROM daily_equity_curve WHERE run_id = ? ORDER BY timestamp",
        [run_id],
    ).fetchdf()
    if equity.empty:
        raise ValueError(f"no equity curve rows for run_id={run_id}")
    trades = conn.execute("SELECT count(*) FROM trade_ledger WHERE run_id = ?", [run_id]).fetchone()[0]
    agents = conn.execute("SELECT count(*) FROM agent_decisions WHERE run_id = ?", [run_id]).fetchone()[0]
    start_equity = float(equity.iloc[0]["equity"])
    end_equity = float(equity.iloc[-1]["equity"])
    net_pnl = end_equity - start_equity
    return_pct = (net_pnl / start_equity) * 100 if start_equity else 0.0
    return SummaryStats(
        run_id=run_id,
        net_pnl=net_pnl,
        return_pct=return_pct,
        max_drawdown_pct=_max_drawdown_pct(equity["equity"]),
        total_trades=int(trades),
        agent_invocations=int(agents),
    )


def render_summary_table(stats: SummaryStats) -> Table:
    """Build a Rich table for CLI display."""
    table = Table(title=f"Nifty.AI Backtest {stats.run_id}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Net P&L", f"{stats.net_pnl:,.2f}")
    table.add_row("Return", f"{stats.return_pct:.2f}%")
    table.add_row("Max Drawdown", f"{stats.max_drawdown_pct:.2f}%")
    table.add_row("Trades", str(stats.total_trades))
    table.add_row("Agent Invocations", str(stats.agent_invocations))
    return table


def _max_drawdown_pct(equity: pd.Series) -> float:
    curve = equity.astype(float)
    running_max = curve.cummax()
    drawdowns = (curve / running_max - 1.0) * 100
    return float(drawdowns.min())
