# Architecture

Nifty.AI is a local-first research system for Indian-market strategy development. It combines a multi-agent reasoning layer, an OpenAlgo market/broker bridge, a deterministic backtest engine, paper trading via Analyzer Mode, and several user interfaces.

## System Goals

- Adapt TradingAgents to Indian market symbols, exchanges, and data access.
- Keep execution and market connectivity behind OpenAlgo.
- Provide a Jesse-style strategy contract that works in backtest and paper modes.
- Store repeatable runs in DuckDB.
- Expose the same core services through CLI, web, and MCP.
- Keep live trading out of the default path.

## Package Layers

```text
nifty_ai.openalgo      OpenAlgo REST, Analyzer, symbols, calendar, streaming
nifty_ai.agents        TradingAgents patching + OpenAlgo data tools
nifty_ai.strategy      BaseStrategy, AgentStrategy, HybridStrategy, registry
nifty_ai.engine        CandleStore, Portfolio, SimulatedBroker, BacktestRunner
nifty_ai.paper         Analyzer Mode paper runner
nifty_ai.db            DuckDB schema and migrations
nifty_ai.reporting     Rich summaries and HTML reports
nifty_ai.services      Shared orchestration used by interfaces
nifty_ai.cli           Typer CLI
nifty_ai.web           FastAPI dashboard and JSON API
nifty_ai.mcp           stdio MCP server
```

## Dependency Direction

Interfaces call `services/`. Services call strategy, engine, db, and reporting modules. Core modules do not import CLI, web, or MCP. This prevents entrypoint behavior from leaking into reusable domain logic.

## Backtest Flow

1. CSV or cached candles are normalized to 1-minute OHLCV.
2. `BacktestRunner` creates a `Portfolio`, `SimulatedBroker`, and event loop.
3. Each bar injects `StrategyContext` into the strategy.
4. Strategy hooks produce `OrderIntent`s.
5. `SimulatedBroker` applies fill rules, slippage, commission, and lot-size checks.
6. `Portfolio` records fills, cash, positions, realized P&L, and equity snapshots.
7. Optional persistence writes `trade_ledger` and `daily_equity_curve` rows.

## Paper Flow

1. `PaperRunner.start()` enables or verifies OpenAlgo Analyzer Mode.
2. Ticks can be aggregated into bars via `TickBarAggregator`.
3. Completed bars inject the same `StrategyContext` used in backtests.
4. Orders are submitted through `NiftyOpenAlgoClient.placeorder` with Analyzer Mode active.

## Agent Flow

TradingAgents is used as a dependency, not forked. Nifty.AI patches its analyst tool registry before graph construction so market data comes from OpenAlgo. Tools that are not yet available for Indian markets return explicit `[NO_DATA]` responses.

## Persistence

DuckDB tables include:

- `trade_ledger`
- `daily_equity_curve`
- `agent_decisions`
- `agent_transcripts`
- `candle_cache`

The schema lives in `src/nifty_ai/db/schema.sql` and is applied by `get_db()`.

## Interfaces

- CLI: operational automation and scripts.
- Web: local dashboard for manual use.
- MCP: AI assistant access to local tools.
- Docker: repeatable local deployment when Docker is installed.
