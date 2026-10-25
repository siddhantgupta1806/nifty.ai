# Agents

Nifty.AI adapts TradingAgents for Indian markets by replacing default market-data tools with OpenAlgo-backed tools.

## Upstream Integration

TradingAgents 0.7.0 exposes analyst tools through `ANALYST_TOOL_REGISTRY`. Nifty.AI mutates that registry in `nifty_ai.agents.vendor_injection.apply_openalgo_patch()` before building a graph.

This keeps Nifty.AI as a thin wrapper around upstream TradingAgents rather than a fork.

## Tool Mapping

- `get_stock_data`: OpenAlgo `history` daily candles.
- `get_indicators`: OpenAlgo candles + `stockstats` indicators.
- `get_option_chain`: OpenAlgo option chain endpoint.
- `get_option_greeks`: OpenAlgo option Greeks endpoint.
- News/fundamentals placeholders: explicit `[NO_DATA]` until Indian providers are integrated.

## Strategy Modes

- `AgentStrategy`: runs full TradingAgents debate and converts the final recommendation into long/short/hold behavior.
- `HybridStrategy`: runs deterministic Python signal first, then an agent/risk overlay can approve or veto.
- Human strategy: no LLM calls; pure Python hooks.

## Cost and Latency

Agent-heavy backtests can become expensive. A daily pure-agent backtest over a year may invoke hundreds of graph runs. Keep `NIFTY_AI_MAX_LLM_CALLS_PER_RUN` configured and prefer signal-gated hybrid strategies for iteration.

## Failure Behavior

Tool failures should degrade to explicit messages, not hallucinated data. Missing Indian-market fundamentals should stay visible to the analyst graph as unavailable information.
