---
type: architecture-notes
name: nifty-ai-module-map
---

# Architecture Notes

## Package Map

- `nifty_ai.openalgo`: typed OpenAlgo REST client, symbol utilities, calendar, Analyzer helpers, streaming/tick aggregation.
- `nifty_ai.agents`: TradingAgents OpenAlgo tool adapters, vendor patching, graph factory.
- `nifty_ai.strategy`: `BaseStrategy`, `AgentStrategy`, `HybridStrategy`, and dynamic user strategy discovery.
- `nifty_ai.engine`: candle cache, broker simulator, portfolio accounting, event loop, backtest runner.
- `nifty_ai.paper`: Analyzer Mode paper runner using the same strategy contract.
- `nifty_ai.db`: DuckDB schema and migration helpers.
- `nifty_ai.reporting`: Rich summary and QuantStats/fallback HTML reporting.
- `nifty_ai.services`: shared orchestration used by CLI/web/MCP.
- `nifty_ai.cli`: Typer commands.
- `nifty_ai.web`: FastAPI app and local dashboard.
- `nifty_ai.mcp`: FastMCP stdio server.

## Dependency Direction

Interfaces should call services. Services call engine/reporting/db/strategy. Core modules must not import CLI/web/MCP. This keeps tests fast and prevents entrypoint-specific behavior from leaking into domain logic.

## Patch Point

TradingAgents 0.7.0 resolves analyst tools through `tradingagents.agents.utils.tool_registry.ANALYST_TOOL_REGISTRY`. Nifty.AI mutates that registry in `vendor_injection.apply_openalgo_patch()` before graph construction.
