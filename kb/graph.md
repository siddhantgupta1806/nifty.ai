---
type: knowledge-graph
name: nifty-ai-change-graph
---

# Knowledge Graph

## Runtime Flow

`OpenAlgo -> openalgo.client -> agents.tools_openalgo -> TradingAgents graph -> strategy -> engine/paper -> db -> reporting -> CLI/web/MCP`

## Change Paths

- New OpenAlgo endpoint: update `openalgo.client`, add mocked tests, optionally expose via MCP/web/CLI only through a service.
- Strategy API change: update `strategy.base`, engine context creation, paper context creation, examples, and strategy tests.
- Backtest accounting change: update `engine.portfolio`, `engine.broker_sim`, runner tests, reporting summaries, and docs.
- Agent tool change: update `agents.tools_openalgo`, vendor registry tests, and AI workflow docs.
- Report schema change: update `db/schema.sql`, migration helper tests, report generation, CLI/web/MCP consumers.

## Fragile Areas

- TradingAgents import path is heavy and can take 30-60 seconds on cold import.
- QuantStats can require a headless Matplotlib backend; keep `Agg` forced.
- OpenAlgo live availability is not assumed in unit tests; use mocks.
- `mcp.server.fastmcp.FastMCP` should stay contained to the MCP module.
