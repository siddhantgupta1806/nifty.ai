"""Nifty.AI CLI entrypoint."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer
from rich.console import Console

from nifty_ai import __version__
from nifty_ai.engine import CandleStore
from nifty_ai.openalgo import analyzer as analyzer_mod
from nifty_ai.openalgo.client import NiftyOpenAlgoClient
from nifty_ai.reporting import generate_report
from nifty_ai.services.backtests import run_backtest_from_paths


app = typer.Typer(
    name="nifty",
    help="Nifty.AI - multi-agent trading + backtesting for Indian markets.",
    no_args_is_help=True,
)
analyzer_app = typer.Typer(help="Toggle / inspect OpenAlgo Analyzer Mode.")
agents_app = typer.Typer(help="Run TradingAgents debates.")
candles_app = typer.Typer(help="Warm/read candle cache.")

app.add_typer(analyzer_app, name="analyzer")
app.add_typer(agents_app, name="agents")
app.add_typer(candles_app, name="candles")

console = Console()


@app.command()
def version() -> None:
    """Print the installed Nifty.AI version."""
    console.print(f"Nifty.AI v{__version__}")


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8766, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Run the local web dashboard."""
    import uvicorn

    uvicorn.run("nifty_ai.web.app:app", host=host, port=port, reload=reload)


@app.command()
def backtest(
    strategy: Path = typer.Option(..., "--strategy", exists=True, file_okay=True, dir_okay=False),
    candles: Path = typer.Option(..., "--candles", exists=True, file_okay=True, dir_okay=False),
    symbol: str = typer.Option(..., "--symbol"),
    exchange: str = typer.Option("NSE", "--exchange"),
    capital: float = typer.Option(1_000_000, "--capital"),
    commission_bps: float = typer.Option(3.0, "--commission-bps"),
    slippage_bps: float = typer.Option(0.0, "--slippage-bps"),
    persist_db: Path | None = typer.Option(None, "--persist-db"),
) -> None:
    """Run a CSV-backed single-symbol backtest."""
    try:
        result = run_backtest_from_paths(
            strategy_path=strategy,
            candles_path=candles,
            symbol=symbol,
            exchange=exchange,
            capital=capital,
            commission_bps=commission_bps,
            slippage_bps=slippage_bps,
            persist_db=persist_db,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"run_id={result.run_id}")
    console.print(f"final_equity={result.final_equity:.2f}")
    console.print(f"net_pnl={result.net_pnl:.2f}")
    console.print(f"return_pct={result.return_pct:.2f}")


@app.command()
def report(
    run_id: str = typer.Option(..., "--run-id"),
    db: Path = typer.Option(..., "--db", exists=True, file_okay=True, dir_okay=False),
    out: Path = typer.Option(Path("report.html"), "--out"),
) -> None:
    """Generate an HTML report for a persisted run."""
    output = generate_report(db, run_id, out)
    console.print(str(output))


@agents_app.command("debate")
def agents_debate(
    symbol: str = typer.Option(..., "--symbol"),
    date: str = typer.Option(..., "--date"),
) -> None:
    """Run one full TradingAgents debate for a symbol/date."""
    from nifty_ai.agents import build_nifty_graph

    graph = build_nifty_graph()
    _, recommendation = graph.propagate(symbol, date)
    console.print(recommendation)


@candles_app.command("fetch")
def candles_fetch(
    symbol: str = typer.Option(..., "--symbol"),
    exchange: str = typer.Option("NSE", "--exchange"),
    start: str = typer.Option(..., "--start"),
    end: str = typer.Option(..., "--end"),
    db: Path = typer.Option(Path(".nifty_ai/nifty.duckdb"), "--db"),
) -> None:
    """Fetch 1-minute candles from OpenAlgo and store them in DuckDB."""
    with NiftyOpenAlgoClient() as client:
        payload = client.history(symbol=symbol, exchange=exchange, interval="1m", start_date=start, end_date=end)
    frame = pd.DataFrame(payload)
    store = CandleStore(db)
    try:
        count = store.put_candles(exchange, symbol, frame)
    finally:
        store.close()
    console.print(f"stored={count}")


@analyzer_app.command("status")
def analyzer_status_cmd() -> None:
    """Show the current Analyzer Mode state and virtual balance."""
    with NiftyOpenAlgoClient() as client:
        data = analyzer_mod.analyzer_status(client)
    console.print(data)


@analyzer_app.command("on")
def analyzer_on_cmd() -> None:
    """Enable Analyzer Mode."""
    with NiftyOpenAlgoClient() as client:
        data = analyzer_mod.enable_analyzer(client)
    console.print(data)


@analyzer_app.command("off")
def analyzer_off_cmd() -> None:
    """Disable Analyzer Mode."""
    with NiftyOpenAlgoClient() as client:
        data = analyzer_mod.disable_analyzer(client)
    console.print(data)


if __name__ == "__main__":  # pragma: no cover
    app()