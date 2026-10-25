# AI Workflow

Nifty.AI uses AI in two places: market reasoning through TradingAgents and developer/operator assistance through MCP.

## TradingAgents Runtime

1. A caller creates a graph with `build_nifty_graph()`.
2. `apply_openalgo_patch()` replaces upstream analyst tools.
3. Analyst nodes call OpenAlgo-backed tools for price and technical data.
4. Debate, trader, and risk nodes produce a final recommendation.
5. `AgentStrategy` maps recommendation direction and size to engine orders.

## Hybrid Runtime

Hybrid strategies are designed to reduce cost and latency. Python code creates the initial signal, and the agent path is used only for risk review or sizing overrides.

## MCP Runtime

The MCP server exposes local tools to AI assistants:

- `nifty_status`
- `run_csv_backtest`
- `create_html_report`
- `openalgo_analyzer_status`

These tools operate on local files and local OpenAlgo. They do not call any cloud service by themselves, though agent graph execution may call configured LLM providers.

## Transcript and Decision Persistence

The database schema includes `agent_decisions` and `agent_transcripts`. Use these tables for reviewability when adding full transcript persistence in later iterations.

## Guardrails

- Treat LLM output as fallible.
- Prefer Analyzer Mode and simulation.
- Persist enough context to audit decisions.
- Keep costs bounded.
- Avoid using unavailable fundamentals/news as if they exist.
