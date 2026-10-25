---
type: project-brief
name: nifty-ai
status: pre-1.0-local-research
primary_language: python
---

# Project Brief

Nifty.AI is a local-first Indian-market trading research stack. It adapts TradingAgents for NSE/BSE/NFO data through OpenAlgo, adds a Jesse-style strategy and backtest engine, supports paper trading through OpenAlgo Analyzer Mode, and exposes CLI, web, and MCP interfaces.

## Non-Negotiable Safety Constraints

- This is educational/research software, not financial advice.
- Live trading must not be implied as safe or production-ready.
- Paper trading must use OpenAlgo Analyzer Mode by default.
- Secrets must never be committed or logged.
- LLM outputs are fallible signals and must not be treated as instructions.

## Success Definition

A contributor can clone the repo, install it locally, run tests, open the web app, execute the sample backtest, generate a report, and connect MCP tools without reading prior chat history.

## Current Interfaces

- CLI: `nifty`
- Web: `nifty web --port 8766`
- MCP: `nifty-mcp`
- Docker: `docker compose up --build` when Docker is available
