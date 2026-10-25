# Local Deploy and Run

## Python Path

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy .env.example .env
.\.venv\Scripts\nifty.exe web --host 127.0.0.1 --port 8766
```

Open http://127.0.0.1:8766.

## Docker Path

```powershell
docker compose up --build
```

Docker was not available in the current development environment, so validate this on a machine with Docker installed before relying on it.

## Sample Backtest

```powershell
.\.venv\Scripts\nifty.exe backtest --strategy examples/strategies/ema_cross.py --candles examples/data/reliance_1m.csv --symbol RELIANCE --capital 1000000 --persist-db .nifty_ai/nifty.duckdb
```

## Report

```powershell
.\.venv\Scripts\nifty.exe report --run-id <run_id> --db .nifty_ai/nifty.duckdb --out reports/report.html
```

## MCP

```powershell
.\.venv\Scripts\nifty-mcp.exe
```
