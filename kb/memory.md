---
type: durable-memory
name: nifty-ai-verified-facts
---

# Memory

- OpenAlgo REST defaults to `http://127.0.0.1:5000`.
- OpenAlgo history is POST `/api/v1/history`.
- OpenAlgo paper mode is Analyzer Mode, toggled with `/api/v1/analyzertoggle`.
- TradingAgents version pinned and verified: `0.7.0`.
- TradingAgents patch point: `ANALYST_TOOL_REGISTRY`.
- The current full suite passed with 59 tests after installing all runtime dependencies.
- Docker was not locally validated because Docker is unavailable on this machine.
- Web dashboard is unauthenticated and should bind to `127.0.0.1` by default.
- QuantStats reporting falls back to a built-in HTML report if plotting fails.
