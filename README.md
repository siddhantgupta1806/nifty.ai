# Nifty.AI

Nifty.AI is an educational Indian-market trading research stack that combines TradingAgents, OpenAlgo, and a backtesting engine.

It includes:

- OpenAlgo REST, symbols, calendar, streaming, and Analyzer Mode helpers
- TradingAgents data-tool adaptation for NSE/BSE/NFO workflows
- Human Python, pure-agent, and hybrid strategy contracts
- Bar-by-bar backtesting with fills, costs, lot-size checks, and MIS square-off
- Paper trading through OpenAlgo Analyzer Mode
- DuckDB persistence and HTML/CLI reports
- CLI, local FastAPI web dashboard, and MCP server

## Important Safety Notice

This project is for education, research, and simulation only. It is not financial advice and is not a production live-trading system. Do not use it to place live trades. LLM-generated outputs can be wrong, stale, incomplete, or unsafe. Use offline backtests and OpenAlgo Analyzer Mode while developing.

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy .env.example .env
```

Set at least `OPENALGO_API_KEY` in `.env` when using OpenAlgo-backed features.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run the web app:

```powershell
.\.venv\Scripts\nifty.exe web --port 8766
```

Open http://127.0.0.1:8766.

Run the example backtest:

```powershell
.\.venv\Scripts\nifty.exe backtest `
  --strategy examples/strategies/ema_cross.py `
  --candles examples/data/reliance_1m.csv `
  --symbol RELIANCE `
  --capital 1000000 `
  --persist-db .nifty_ai/nifty.duckdb
```

Generate a report:

```powershell
.\.venv\Scripts\nifty.exe report --run-id <run_id> --db .nifty_ai/nifty.duckdb --out reports/report.html
```

Run the MCP server:

```powershell
.\.venv\Scripts\nifty-mcp.exe
```

## Architecture

```text
User / AI / Hybrid Strategy
          |
          v
TradingAgents graph with OpenAlgo-backed data tools
          |
          v
Backtest engine or OpenAlgo Analyzer paper runner
          |
          v
DuckDB ledger, reports, CLI, web UI, MCP tools
```

See [docs/architecture.md](docs/architecture.md), [docs/agents.md](docs/agents.md), and [docs/ai_workflow.md](docs/ai_workflow.md).

## Local Interfaces

- CLI: `nifty --help`
- Web: `nifty web --port 8766`
- MCP: `nifty-mcp`
- Docker: `docker compose up --build`

## Documentation

- [Safety](docs/safety.md)
- [Architecture](docs/architecture.md)
- [AI workflow](docs/ai_workflow.md)
- [OpenAlgo setup](docs/openalgo_setup.md)
- [Strategies](docs/strategies.md)
- [Web app](docs/web_app.md)
- [MCP setup](docs/mcp_setup.md)
- [Local deploy](docs/local_deploy.md)

## Project Status

This repository is pre-1.0 and under active development. The current codebase is packaged for local research use and GitHub collaboration.

## License

MIT. See [LICENSE](LICENSE).
