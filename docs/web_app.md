# Web App

The web app is a local FastAPI dashboard for running backtests and browsing persisted runs.

## Run

```powershell
.\.venv\Scripts\nifty.exe web --host 127.0.0.1 --port 8766
```

Open http://127.0.0.1:8766.

## API

- `GET /api/status`
- `GET /api/runs`
- `POST /api/backtests`

## Behavior

The web app calls the same `services.backtests` path used by CLI and MCP. Backtests are local and CSV-backed. Persisted runs are stored in DuckDB.

## Security

The web app does not include authentication. Bind to `127.0.0.1` for local use. Add authentication and TLS before any network exposure.
