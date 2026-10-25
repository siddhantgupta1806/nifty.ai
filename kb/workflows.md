---
type: workflow-guide
name: nifty-ai-workflows
---

# Workflows

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy .env.example .env
```

## Verify

```powershell
.\.venv\Scripts\pip.exe check
.\.venv\Scripts\python.exe -m pytest -q
```

## Run Web

```powershell
.\.venv\Scripts\nifty.exe web --host 127.0.0.1 --port 8766
```

## Run Sample Backtest

```powershell
.\.venv\Scripts\nifty.exe backtest --strategy examples/strategies/ema_cross.py --candles examples/data/reliance_1m.csv --symbol RELIANCE --capital 1000000 --persist-db .nifty_ai/nifty.duckdb
```

## Run MCP

```powershell
.\.venv\Scripts\nifty-mcp.exe
```

## Pre-Push Checklist

1. `pip check`
2. `pytest -q`
3. no `.env` or `.nifty_ai` tracked
4. README/manual paths still work
5. safety warning still visible in README and docs
