"""Model Context Protocol server for Nifty.AI local tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from nifty_ai import __version__
from nifty_ai.openalgo.client import NiftyOpenAlgoClient
from nifty_ai.reporting import generate_report
from nifty_ai.services.backtests import run_backtest_from_paths
from nifty_ai.settings import get_settings


mcp = FastMCP("nifty-ai")


@mcp.tool()
def nifty_status() -> dict[str, Any]:
    """Return local Nifty.AI runtime configuration."""
    settings = get_settings()
    return {
        "version": __version__,
        "openalgo_host": settings.openalgo_host,
        "db_path": str(settings.db_path),
        "results_dir": str(settings.results_dir),
    }


@mcp.tool()
def run_csv_backtest(
    strategy_path: str,
    candles_path: str,
    symbol: str,
    exchange: str = "NSE",
    capital: float = 1_000_000,
    commission_bps: float = 3.0,
    slippage_bps: float = 0.0,
    persist_db: str | None = None,
) -> dict[str, Any]:
    """Run a CSV-backed backtest and optionally persist it to DuckDB."""
    result = run_backtest_from_paths(
        strategy_path=strategy_path,
        candles_path=candles_path,
        symbol=symbol,
        exchange=exchange,
        capital=capital,
        commission_bps=commission_bps,
        slippage_bps=slippage_bps,
        persist_db=persist_db,
    )
    return {
        "run_id": result.run_id,
        "symbol": result.symbol,
        "exchange": result.exchange,
        "final_equity": result.final_equity,
        "net_pnl": result.net_pnl,
        "return_pct": result.return_pct,
        "fills": len(result.fills),
    }


@mcp.tool()
def create_html_report(db_path: str, run_id: str, output_html: str) -> dict[str, str]:
    """Generate a local HTML report for a persisted run."""
    output = generate_report(Path(db_path), run_id, Path(output_html))
    return {"output_html": str(output)}


@mcp.tool()
def openalgo_analyzer_status() -> dict[str, Any]:
    """Return OpenAlgo Analyzer Mode status using local credentials."""
    with NiftyOpenAlgoClient() as client:
        return client._post("/analyzerstatus", {})


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
