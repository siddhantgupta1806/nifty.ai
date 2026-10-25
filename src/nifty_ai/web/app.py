"""FastAPI web dashboard for local Nifty.AI workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from nifty_ai import __version__
from nifty_ai.db import get_db
from nifty_ai.services.backtests import run_backtest_from_paths
from nifty_ai.settings import get_settings


class BacktestRequest(BaseModel):
    """JSON request for a local CSV-backed backtest."""

    strategy_path: str = Field(..., min_length=1)
    candles_path: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    exchange: str = "NSE"
    capital: float = 1_000_000
    commission_bps: float = 3.0
    slippage_bps: float = 0.0
    persist: bool = True
    db_path: str | None = None


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    web = FastAPI(title="Nifty.AI", version=__version__)

    @web.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _index_html()

    @web.get("/api/status")
    def status() -> dict[str, Any]:
        settings = get_settings()
        return {
            "version": __version__,
            "openalgo_host": settings.openalgo_host,
            "db_path": str(settings.db_path),
            "results_dir": str(settings.results_dir),
        }

    @web.get("/api/runs")
    def runs(db_path: str | None = Query(default=None)) -> list[dict[str, Any]]:
        db = Path(db_path) if db_path else get_settings().db_path
        with get_db(db) as conn:
            rows = conn.execute(
                """
                SELECT run_id, min(timestamp) AS started_at, max(timestamp) AS ended_at,
                       first(equity ORDER BY timestamp) AS initial_equity,
                       last(equity ORDER BY timestamp) AS final_equity
                FROM daily_equity_curve
                GROUP BY run_id
                ORDER BY ended_at DESC
                LIMIT 25
                """
            ).fetchdf()
        return rows.to_dict(orient="records")

    @web.post("/api/backtests")
    def backtests(request: BacktestRequest) -> dict[str, Any]:
        db_path = request.db_path or str(get_settings().db_path)
        persist_db = db_path if request.persist else None
        try:
            result = run_backtest_from_paths(
                strategy_path=request.strategy_path,
                candles_path=request.candles_path,
                symbol=request.symbol,
                exchange=request.exchange,
                capital=request.capital,
                commission_bps=request.commission_bps,
                slippage_bps=request.slippage_bps,
                persist_db=persist_db,
            )
        except Exception as exc:  # noqa: BLE001 - API should surface structured errors
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "run_id": result.run_id,
            "symbol": result.symbol,
            "exchange": result.exchange,
            "final_equity": result.final_equity,
            "net_pnl": result.net_pnl,
            "return_pct": result.return_pct,
            "fills": len(result.fills),
            "db_path": db_path if request.persist else None,
        }

    return web


def _index_html() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nifty.AI</title>
  <style>
    :root { color-scheme: light; --ink:#17202a; --muted:#5c6773; --line:#d9e0e7; --bg:#f7f9fb; --panel:#ffffff; --accent:#1565c0; --good:#1b7f4b; --bad:#b42318; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Inter, Segoe UI, Arial, sans-serif; background:var(--bg); color:var(--ink); letter-spacing:0; }
    header { display:flex; align-items:center; justify-content:space-between; padding:14px 22px; border-bottom:1px solid var(--line); background:var(--panel); }
    h1 { margin:0; font-size:20px; font-weight:650; }
    main { display:grid; grid-template-columns: 360px 1fr; gap:16px; padding:16px; }
    section { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; }
    h2 { margin:0 0 12px; font-size:15px; }
    label { display:block; margin:10px 0 4px; font-size:12px; color:var(--muted); }
    input { width:100%; height:34px; border:1px solid var(--line); border-radius:6px; padding:0 9px; font:inherit; }
    button { height:36px; border:0; border-radius:6px; background:var(--accent); color:white; font-weight:650; padding:0 12px; cursor:pointer; margin-top:12px; }
    button.secondary { background:#405261; }
    .grid { display:grid; grid-template-columns:repeat(4,minmax(120px,1fr)); gap:10px; }
    .metric { border:1px solid var(--line); border-radius:8px; padding:10px; min-height:64px; }
    .metric span { display:block; font-size:12px; color:var(--muted); }
    .metric strong { display:block; margin-top:6px; font-size:18px; }
    table { width:100%; border-collapse:collapse; margin-top:12px; font-size:13px; }
    th,td { text-align:left; border-bottom:1px solid var(--line); padding:8px; }
    th { color:var(--muted); font-weight:600; }
    pre { margin:12px 0 0; white-space:pre-wrap; background:#0f1720; color:#dbeafe; padding:10px; border-radius:8px; min-height:70px; }
    .status { color:var(--muted); font-size:13px; }
    @media (max-width: 860px) { main { grid-template-columns:1fr; } .grid { grid-template-columns:1fr 1fr; } }
  </style>
</head>
<body>
  <header><h1>Nifty.AI</h1><div class="status" id="status">loading</div></header>
  <main>
    <section>
      <h2>Backtest</h2>
      <label>Strategy path</label><input id="strategy" value="examples/strategies/ema_cross.py">
      <label>Candles CSV path</label><input id="candles" value="examples/data/reliance_1m.csv">
      <label>Symbol</label><input id="symbol" value="RELIANCE">
      <label>Exchange</label><input id="exchange" value="NSE">
      <label>Capital</label><input id="capital" value="1000000">
      <button onclick="runBacktest()">Run Backtest</button>
      <button class="secondary" onclick="loadRuns()">Refresh Runs</button>
      <pre id="output"></pre>
    </section>
    <section>
      <h2>Runs</h2>
      <div class="grid">
        <div class="metric"><span>Version</span><strong id="version">-</strong></div>
        <div class="metric"><span>OpenAlgo</span><strong id="openalgo">-</strong></div>
        <div class="metric"><span>Database</span><strong id="db">-</strong></div>
        <div class="metric"><span>Latest P&L</span><strong id="pnl">-</strong></div>
      </div>
      <table><thead><tr><th>Run</th><th>Start</th><th>End</th><th>Final Equity</th></tr></thead><tbody id="runs"></tbody></table>
    </section>
  </main>
  <script>
    async function boot(){ const s = await fetch('/api/status').then(r=>r.json()); version.textContent=s.version; openalgo.textContent=s.openalgo_host.replace('http://',''); db.textContent=s.db_path; status.textContent='ready'; loadRuns(); }
    async function loadRuns(){ const rows = await fetch('/api/runs').then(r=>r.json()); runs.innerHTML = rows.map(r=>`<tr><td>${r.run_id}</td><td>${r.started_at}</td><td>${r.ended_at}</td><td>${Number(r.final_equity).toFixed(2)}</td></tr>`).join(''); if(rows[0]) pnl.textContent=(Number(rows[0].final_equity)-Number(rows[0].initial_equity)).toFixed(2); }
    async function runBacktest(){ output.textContent='running'; const payload={strategy_path:strategy.value,candles_path:candles.value,symbol:symbol.value,exchange:exchange.value,capital:Number(capital.value),persist:true}; const r=await fetch('/api/backtests',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}); const data=await r.json(); output.textContent=JSON.stringify(data,null,2); if(r.ok) loadRuns(); }
    boot();
  </script>
</body>
</html>
"""


app = create_app()