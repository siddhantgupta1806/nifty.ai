"""Backtest execution and persistence service."""

from __future__ import annotations

from pathlib import Path

from pandas import read_csv

from nifty_ai.db import get_db
from nifty_ai.engine import BacktestResult, BacktestRunner, BrokerConfig
from nifty_ai.strategy.registry import discover_strategies


def run_backtest_from_paths(
    *,
    strategy_path: str | Path,
    candles_path: str | Path,
    symbol: str,
    exchange: str = "NSE",
    capital: float = 1_000_000,
    commission_bps: float = 3.0,
    slippage_bps: float = 0.0,
    persist_db: str | Path | None = None,
) -> BacktestResult:
    """Load a strategy + CSV candles, run a backtest, optionally persist it."""
    strategies = discover_strategies(strategy_path)
    if not strategies:
        raise ValueError(f"no BaseStrategy subclasses found in {strategy_path}")
    strategy_cls = next(iter(strategies.values()))
    frame = read_csv(candles_path)
    runner = BacktestRunner(
        strategy_cls(),
        symbol=symbol,
        exchange=exchange,
        capital=capital,
        broker_config=BrokerConfig(commission_bps=commission_bps, slippage_bps=slippage_bps),
    )
    result = runner.run(frame)
    if persist_db is not None:
        persist_backtest_result(persist_db, strategy_cls.__name__, result)
    return result


def persist_backtest_result(db_path: str | Path, strategy_name: str, result: BacktestResult) -> None:
    """Persist fills and equity curve rows for a completed backtest."""
    with get_db(db_path) as conn:
        for fill in result.fills:
            conn.execute(
                """
                INSERT INTO trade_ledger
                (run_id, timestamp, strategy_name, symbol, exchange, side, quantity, price, commission, slippage, product, pricetype, order_tag)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    result.run_id,
                    fill.timestamp,
                    strategy_name,
                    fill.symbol,
                    result.exchange,
                    fill.side.value,
                    fill.quantity,
                    fill.price,
                    fill.commission,
                    fill.slippage,
                    fill.metadata.get("product", "MIS"),
                    "MARKET",
                    fill.tag,
                ],
            )
        for row in result.equity_curve.itertuples(index=False):
            conn.execute(
                """
                INSERT INTO daily_equity_curve
                (run_id, timestamp, equity, cash, realized_pnl, unrealized_pnl)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [result.run_id, row.timestamp, row.equity, row.cash, row.realized_pnl, row.unrealized_pnl],
            )