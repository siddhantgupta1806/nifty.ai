"""HTML reporting for persisted backtests."""

from __future__ import annotations

from pathlib import Path

from nifty_ai.db import get_db


def generate_report(db_path: str | Path, run_id: str, output_html: str | Path) -> Path:
    """Generate an HTML report for a persisted run.

    QuantStats is used when available and functional. If plotting backends are
    unavailable in a local/headless environment, a compact built-in report is
    written instead.
    """
    output = Path(output_html)
    output.parent.mkdir(parents=True, exist_ok=True)
    with get_db(db_path) as conn:
        equity = conn.execute(
            "SELECT timestamp, equity FROM daily_equity_curve WHERE run_id = ? ORDER BY timestamp",
            [run_id],
        ).fetchdf()
    if equity.empty:
        raise ValueError(f"no equity curve rows for run_id={run_id}")
    returns = equity.set_index("timestamp")["equity"].pct_change().dropna()
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import quantstats as qs  # type: ignore

        qs.reports.html(returns, output=str(output), title=f"Nifty.AI Backtest {run_id}")
    except Exception:
        _write_basic_html(output, run_id, equity)
    return output


def _write_basic_html(output: Path, run_id: str, equity) -> None:
    start = float(equity.iloc[0]["equity"])
    end = float(equity.iloc[-1]["equity"])
    net = end - start
    ret = (net / start) * 100 if start else 0.0
    output.write_text(
        "\n".join(
            [
                "<!doctype html>",
                "<html><head><meta charset='utf-8'><title>Nifty.AI Report</title></head><body>",
                f"<h1>Nifty.AI Backtest {run_id}</h1>",
                f"<p>Start equity: {start:,.2f}</p>",
                f"<p>Final equity: {end:,.2f}</p>",
                f"<p>Net P&amp;L: {net:,.2f}</p>",
                f"<p>Return: {ret:.2f}%</p>",
                "</body></html>",
            ]
        ),
        encoding="utf-8",
    )
