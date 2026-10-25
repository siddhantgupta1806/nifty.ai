# OpenAlgo Setup

OpenAlgo is the local bridge between Nifty.AI and Indian brokers/market data.

## Requirements

- OpenAlgo running locally.
- API reachable at `http://127.0.0.1:5000`.
- API key generated in OpenAlgo.
- Analyzer Mode enabled for paper trading.

## Environment

Copy `.env.example` to `.env` and set:

```text
OPENALGO_API_KEY=...
OPENALGO_HOST=http://127.0.0.1:5000
OPENALGO_WS=ws://127.0.0.1:8765
```

## Verified Endpoint Corrections

- OpenAlgo REST defaults to port `5000`.
- `/api/v1/history` is a POST endpoint.
- Analyzer Mode is toggled with `/api/v1/analyzertoggle`.

## Smoke Checks

```powershell
.\.venv\Scripts\nifty.exe analyzer status
.\.venv\Scripts\nifty.exe analyzer on
```

Keep Analyzer Mode on while testing paper workflows.

## Safety Notes

Do not use live broker mode while developing. Confirm product type, exchange, quantity, and symbol before any manual broker test.
