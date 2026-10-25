# Plan: Nifty.AI — TradingAgents × OpenAlgo × Jesse-style Engine

Build an Indian-market multi-agent trading + backtesting system by **thin-wrapping pip-installed TradingAgents**, **swapping its data vendor layer to OpenAlgo** (via official `openalgo` SDK + MCP tools), and **bolting on a custom Jesse-inspired bar-by-bar backtest engine** plus a paper-trading bridge that toggles OpenAlgo's Analyzer Mode. Strategy authoring supports three modes in v1: Human Python (Jesse-style hooks), Pure-agent (full debate per decision), and Hybrid (Python signal + agent risk overlay) — all with configurable agent cadence (bar / daily / weekly / signal-gated).

---

## Phase 1 — Repo Bootstrap & Dev Environment

1. Initialize Python project at repo root with `pyproject.toml`, `uv`-managed virtualenv, Python **3.11+** (required by OpenAlgo). Create `src/nifty_ai/` package layout.
2. Pin runtime deps: `tradingagents`, `openalgo`, `langgraph`, `langchain`, `duckdb`, `pandas`, `pyarrow`, `quantstats`, `pytz`, `httpx`, `pydantic>=2`, `typer` (CLI), `rich` (logs), `mcp` client.
3. Pin dev deps: `pytest`, `pytest-asyncio`, `ruff`, `mypy`, `pre-commit`, `responses` (HTTP mocking).
4. Create `.env.example` with `OPENALGO_API_KEY`, `OPENALGO_HOST`, `OPENALGO_WS`, `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY`, `NIFTY_AI_DB_PATH`, `NIFTY_AI_CACHE_DIR`.
5. Add `Makefile` / `task` runner targets: `install`, `test`, `lint`, `backtest`, `paper`.
6. Add `docs/architecture.md` skeleton referencing this plan (existing `docs/prd.md` stays as historical PRD with a note that ports/endpoints were updated during research).

*Parallel with Phase 2 once scaffolding is in place.*

---

## Phase 2 — OpenAlgo Integration Layer (`src/nifty_ai/openalgo/`)

1. **`client.py`** — Wrap `openalgo.api` with a `NiftyOpenAlgoClient` class:
   - Typed methods over `history`, `quotes`, `multiquotes`, `depth`, `placeorder`, `modifyorder`, `cancelorder`, `funds`, `positionbook`, `holdings`, `orderbook`, `tradebook`, `optionchain`, `optiongreeks`, `holidays`, `timings`.
   - Retry/backoff via `tenacity`, rate-limit guard, structured error types (`OpenAlgoError`, `OpenAlgoAuthError`, `OpenAlgoMarketClosedError`).
   - Connection target: `http://127.0.0.1:5000` default (NOT `8010` as the original PRD said — corrected during research).
2. **`analyzer.py`** — Helpers `enable_analyzer()`, `disable_analyzer()`, `analyzer_status()`, `reset_virtual_capital()` wrapping `/api/v1/analyzertoggle` and `/api/v1/analyzerstatus`.
3. **`symbols.py`** — Indian symbol formatting/validation: build option symbol `NIFTY25MAY2525000CE` from underlying/expiry/strike/type, parse OpenAlgo symbol strings, enum of exchange codes (`NSE`, `BSE`, `NFO`, `BFO`, `MCX`, `CDS`, `BCD`, `NSE_INDEX`, `BSE_INDEX`).
4. **`calendar.py`** — IST-aware utilities: `is_market_open(dt)`, `next_trading_day(dt)`, `align_to_bar(dt, interval)`, holiday lookup cached from `/api/v1/holidays`. All times `Asia/Kolkata`.
5. **`streaming.py`** — Thin wrapper over SDK WebSocket (`subscribe_ltp`, `subscribe_depth`) returning an async iterator of typed tick events for the live engine.
6. **`mcp_tools.py`** — Discover and bind OpenAlgo's MCP server tools (`get_historical_data`, `get_option_chain`, `get_option_greeks`, `place_order`, `get_funds`, etc.) as LangChain `Tool` objects for direct injection into TradingAgents analyst nodes.

*Independently testable with mocked HTTP via `responses` library + a tiny live smoke test gated by env flag.*

---

## Phase 3 — TradingAgents Adaptation (`src/nifty_ai/agents/`)

1. **`vendor_injection.py`** — TradingAgents routes data vendors through `tradingagents.dataflows.interface`. Register a new `"openalgo"` vendor by:
   - Importing the interface module and adding entries to its vendor-routing dicts, OR
   - Monkey-patching the four tool functions (`get_stock_data`, `get_indicators`, `get_news`, `get_fundamentals`) at import time so they call our OpenAlgo-backed implementations. Use the patching approach as the safe fallback if upstream routing isn't pluggable from outside.
2. **`tools_openalgo.py`** — Implement adapters:
   - `get_stock_data_in(symbol, start, end)` → OpenAlgo `history` (interval `1d` for daily, `5m` for intraday).
   - `get_indicators_in(symbol, indicator, curr_date, look_back_days)` → fetch candles via OpenAlgo, compute via `pandas_ta` / `stockstats`.
   - `get_news_in(...)` — leverage MCP / OpenAlgo news endpoints if available, else fallback to a pluggable Indian news source (deferred — log warning, return empty).
   - `get_fundamentals_in(...)` — stub for v1 (Indian fundamentals are a separate integration); return "not available" payload so agents degrade gracefully.
   - `get_option_chain_in(...)`, `get_option_greeks_in(...)` — extra tools beyond TradingAgents' default set, exposed to a new optional **Derivatives Analyst** node in Phase 8.
3. **`config.py`** — Build a `NIFTY_AI_CONFIG = DEFAULT_CONFIG | {...}` overriding `data_vendors` to `{"core_stock_apis": "openalgo", "technical_indicators": "openalgo", ...}`, plus IST output language hints and Indian-market system-prompt deltas.
4. **`graph_factory.py`** — Wrap `TradingAgentsGraph(config=NIFTY_AI_CONFIG, ...)` construction in a `build_nifty_graph(...)` helper that returns a ready-to-call `propagate(symbol, date)`-compatible object.
5. **Risk-of-coupling mitigation** — Pin `tradingagents` to a known version in `pyproject.toml`. Add a `tests/test_upstream_contract.py` that asserts the symbol of every patched function still exists in the installed `tradingagents` package (fails CI loudly on upstream breaking changes).

*Depends on Phase 2. Independently verifiable via a smoke test that runs `build_nifty_graph().propagate("RELIANCE", "2026-05-01")` and asserts an OpenAlgo HTTP call was issued.*

---

## Phase 4 — Strategy Framework (`src/nifty_ai/strategy/`)

1. **`base.py`** — `BaseStrategy` ABC mirroring Jesse hooks:
   - Required: `should_long()`, `should_short()`, `go_long()`, `go_short()`.
   - Optional: `before()`, `after()`, `update_position()`, `should_cancel_entry()`, `on_open_position()`, `on_close_position()`.
   - Strategy-side properties: `self.price`, `self.candles`, `self.position`, `self.balance`, `self.portfolio_value`, `self.is_backtesting`, `self.is_papertrading`, `self.is_livetrading`.
   - Class attribute `cadence: Literal["bar", "daily", "weekly", "signal"] = "bar"` to control agent invocation in hybrid mode.
2. **`agent_strategy.py`** — `AgentStrategy(BaseStrategy)` — adapter that runs the full TradingAgents debate inside `should_long` / `should_short` and translates the final decision (`Buy`/`Sell`/`Hold`) into engine orders. Caches decisions per `(symbol, date)` to avoid duplicate LLM calls within the same bar.
3. **`hybrid_strategy.py`** — `HybridStrategy(BaseStrategy)` — user provides fast Python signal logic in `should_long/short`; before order submission, engine calls **only the risk-debate subgraph** (Aggressive/Conservative/Neutral + Portfolio Manager) on the proposed trade for veto / sizing override.
4. **`registry.py`** — `discover_strategies(path)` to import user strategy files dynamically.
5. **`examples/`** in repo root: `examples/strategies/ema_cross.py` (Human), `examples/strategies/agent_reliance.py` (Pure-agent), `examples/strategies/hybrid_nifty.py` (Hybrid).

*Depends on Phase 3. Verifiable via `pytest` against in-memory candle fixtures.*

---

## Phase 5 — Backtest Engine (`src/nifty_ai/engine/`)

1. **`candle_store.py`** — DuckDB-backed candle cache. Store **only 1-minute candles** per `(exchange, symbol)`; resample to higher TFs on-the-fly with pandas. Lazy-fetch missing ranges from OpenAlgo `history`, persist via Parquet partitions for speed.
2. **`broker_sim.py`** — Simulated broker:
   - Fill model: MARKET fills at bar close; LIMIT fills if bar `low <= price <= high`; SL/SL-M trigger when bar crosses `trigger_price`.
   - Commission: configurable per-exchange (default 0.03% brokerage + 0.025% STT for intraday equity).
   - Slippage: configurable bps applied to MARKET fills.
   - MIS auto square-off at 15:20 IST.
   - Lot-size enforcement for F&O (rejects non-multiple-of-lot quantities).
3. **`portfolio.py`** — Cash / `Position` / equity tracking. Daily snapshot at 15:30 IST written to `daily_equity_curve` table.
4. **`event_loop.py`** — Bar-by-bar driver:
   - Iterates 1m candles from `start_date` to `end_date` for the active symbol(s), skipping holidays / outside market hours.
   - On each bar: invoke `strategy.before()`, conditionally invoke agent cadence (per Phase 4 setting), call `should_long/short`, then `go_long/short`, run `broker_sim.simulate_bar()`, call `update_position()` + `after()`.
   - Pluggable timeframe selector (strategy declares `timeframe = "5m"` → loop still uses 1m for fills but exposes resampled candles to the strategy).
5. **`runner.py`** — `BacktestRunner(strategy, symbols, start, end, capital, config).run() -> BacktestResult`.

*Depends on Phases 2 + 4. Verifiable with a deterministic synthetic-candle test and an end-to-end small NIFTY 1-week backtest.*

---

## Phase 6 — Paper-Trading Bridge (`src/nifty_ai/paper/`)

1. **`runner.py`** — `PaperRunner(strategy, symbols, config)`:
   - On start: call `analyzer.enable_analyzer()` (ensures sandbox).
   - Subscribe to LTP/depth via OpenAlgo WebSocket (Phase 2 `streaming.py`).
   - Synthesize "bar close" events from ticks at the strategy's declared timeframe (e.g., 5-minute aggregation).
   - On bar close: invoke the same Strategy + agent path used in backtest; route final orders to `client.placeorder(...)` against the Analyzer Mode.
   - On `Ctrl+C` / shutdown: flush positions log; optionally `analyzer_toggle(False)` based on config.
2. **Same `Strategy` contract** — Engine guarantees `is_papertrading` flag, but no other API changes vs. backtest, so user strategies are mode-agnostic.
3. Pre-flight: assert IST clock, market open, analyzer mode active, sufficient virtual capital.

*Depends on Phases 2, 4, 5 (reuses portfolio/position dataclasses). Manual verification via 30-minute live session against `NIFTY` index.*

---

## Phase 7 — Persistence & Reporting (`src/nifty_ai/db/`, `src/nifty_ai/reporting/`)

1. **`db/schema.sql`** — DuckDB tables:
   - `trade_ledger` (per PRD §4.1, plus columns `strategy_name`, `exchange`, `product`, `pricetype`, `agent_run_id`).
   - `daily_equity_curve` (per PRD §4.1, plus `benchmark_value` for NIFTY 50).
   - `agent_decisions` (`run_id`, `timestamp`, `symbol`, `final_rating`, `confidence`, `transcript_path`).
   - `agent_transcripts` (full JSON state log per agent run — for memory/reflection alignment).
   - `candle_cache` (`exchange`, `symbol`, `ts`, `open`, `high`, `low`, `close`, `volume`) with index on `(exchange, symbol, ts)`.
2. **`db/connection.py`** — `get_db()` context manager + migration runner.
3. **`reporting/quantstats_report.py`** — `generate_report(run_id, output_html)`: reads `daily_equity_curve`, computes daily returns, calls `quantstats.reports.html(...)` with NIFTY 50 benchmark. Adds a per-trade table and agent decision summary section.
4. **`reporting/cli_summary.py`** — Rich-formatted CLI table: net P&L, Sharpe, Sortino, max DD, win rate, profit factor, # trades, agent invocation count + LLM cost estimate.

*Depends on Phase 5 (trade ledger + equity rows produced there). Reports verifiable on any completed backtest.*

---

## Phase 8 — CLI Orchestrator & Config (`src/nifty_ai/cli/`)

1. **`main.py`** — `typer` app with commands:
   - `nifty backtest --strategy path/to/strat.py --symbol RELIANCE --exchange NSE --start 2024-01-01 --end 2024-12-31 --capital 1000000`
   - `nifty paper --strategy ... --symbol ... [--auto-square-off]`
   - `nifty report --run-id <uuid> [--out report.html]`
   - `nifty agents debate --symbol RELIANCE --date 2026-05-27` (one-shot full debate, useful for debugging)
   - `nifty analyzer {on|off|status|reset}`
   - `nifty candles fetch --symbol NIFTY --exchange NSE_INDEX --start ... --end ...` (warm cache)
2. **`config.py`** — YAML-based per-run config (`configs/run.yaml`) loaded via `pydantic-settings`, overridable by env vars and CLI flags. Keys: `llm_provider`, `deep_think_llm`, `quick_think_llm`, `max_debate_rounds`, `max_risk_discuss_rounds`, `commission_bps`, `slippage_bps`, `default_product`, `agent_cadence`.

*Depends on all prior phases. Verifiable by running each command against a sample config end-to-end.*

---

## Phase 9 — Examples, Tests & Docs

1. **`tests/`** — Unit tests per module + integration test (`test_e2e_backtest.py`) running EMA-cross strategy on cached `RELIANCE` 1-week candles asserting deterministic P&L.
2. **`tests/test_upstream_contract.py`** — Guard against upstream `tradingagents` breaking changes (per Phase 3 mitigation).
3. **`examples/notebooks/quickstart.ipynb`** — Jupyter walkthrough: cache candles → backtest EMA strategy → generate HTML report → run pure-agent debate on RELIANCE → toggle Analyzer + paper-trade for 10 minutes.
4. **`docs/architecture.md`**, **`docs/openalgo_setup.md`** (how to install/run OpenAlgo locally, get API key), **`docs/strategies.md`** (writing each strategy mode), **`docs/agents.md`** (cadence options, cost estimates, prompt customization).

---

## Relevant Files

**New (created by this plan)**
- `pyproject.toml`, `.env.example`, `Makefile` — project bootstrap.
- `src/nifty_ai/openalgo/{client,analyzer,symbols,calendar,streaming,mcp_tools}.py` — Phase 2.
- `src/nifty_ai/agents/{vendor_injection,tools_openalgo,config,graph_factory}.py` — Phase 3.
- `src/nifty_ai/strategy/{base,agent_strategy,hybrid_strategy,registry}.py` — Phase 4.
- `src/nifty_ai/engine/{candle_store,broker_sim,portfolio,event_loop,runner}.py` — Phase 5.
- `src/nifty_ai/paper/runner.py` — Phase 6.
- `src/nifty_ai/db/{schema.sql,connection.py}` — Phase 7.
- `src/nifty_ai/reporting/{quantstats_report,cli_summary}.py` — Phase 7.
- `src/nifty_ai/cli/{main,config}.py` — Phase 8.
- `examples/strategies/{ema_cross,agent_reliance,hybrid_nifty}.py`, `examples/notebooks/quickstart.ipynb` — Phase 9.
- `docs/architecture.md`, `docs/openalgo_setup.md`, `docs/strategies.md`, `docs/agents.md` — Phase 9.
- `tests/**` — per-phase tests.

**Existing (reused / referenced as upstream)**
- [docs/prd.md](docs/prd.md) — original PRD; keep as-is, add a small "Errata" note at the bottom for the port/endpoint corrections discovered during research.
- `tradingagents` (pip dep) — `TradingAgentsGraph`, `tradingagents.dataflows.interface`, `tradingagents.agents.utils.{agent_states, memory}`, `tradingagents.default_config.DEFAULT_CONFIG`.
- `openalgo` (pip dep) — `openalgo.api` (client class with `history`, `placeorder`, `subscribe_ltp`, etc.).

---

## Verification

1. **Phase 2** — `pytest tests/openalgo/` with `responses`-mocked HTTP covering every wrapped endpoint; live smoke `python -m nifty_ai.cli analyzer status` against a running OpenAlgo on `127.0.0.1:5000`.
2. **Phase 3** — `pytest tests/agents/test_vendor_injection.py` asserts `get_stock_data` returns OpenAlgo-shaped data with mocked client; `python -m nifty_ai.cli agents debate --symbol RELIANCE --date 2026-05-27` returns a non-empty rating.
3. **Phase 4** — `pytest tests/strategy/` — `EMACross` strategy emits expected signals on a synthetic uptrending series.
4. **Phase 5** — `pytest tests/engine/test_e2e_backtest.py` — EMA-cross on 1 week of cached RELIANCE 1m candles produces deterministic final equity within ±0.01% across runs.
5. **Phase 6** — Manual 10-minute paper session against NIFTY index during market hours; verify `positionbook` reflects expected positions and Analyzer balance moves accordingly.
6. **Phase 7** — `nifty report --run-id <id>` produces a valid HTML with Sharpe/Sortino/Max DD/Win Rate sections; `daily_equity_curve` row count == number of trading days in the run.
7. **Phase 8** — Every CLI subcommand runs `--help` cleanly; `nifty backtest` flow end-to-end produces a run row + report.
8. **Phase 9** — `pytest -q` green; `examples/notebooks/quickstart.ipynb` runs top-to-bottom without errors.

---

## Decisions (locked from clarification round)

- **Codebase shape**: Thin wrapper around pip-installed `tradingagents` (user-selected). Risk: upstream may not expose vendor injection cleanly from outside; mitigation = monkey-patch the four data-tool functions and add an upstream-contract test in Phase 3/9.
- **OpenAlgo integration**: Python SDK as primary client + MCP tools bound into analyst nodes for LLM-direct calls. Raw REST not used.
- **Backtest engine**: Custom Jesse-inspired bar-by-bar engine for historical replay; OpenAlgo Analyzer Mode (sandbox) for live paper trading.
- **Agent cadence**: Configurable per strategy (`bar` / `daily` / `weekly` / `signal`-gated). Default `daily` for `AgentStrategy`; `signal` for `HybridStrategy`.
- **Strategy modes in v1**: Human Python (`BaseStrategy` subclass), Pure-agent (`AgentStrategy`), Hybrid (`HybridStrategy`). AI-generated frozen strategy deferred to v2.
- **PRD corrections** discovered during research: OpenAlgo port is **5000** (not 8010); `/api/v1/history` is **POST** (not GET); sandbox is **"Analyzer Mode"** with `/api/v1/analyzertoggle`. Original `docs/prd.md` will get an Errata note.

---

## Further Considerations (resolve before / during execution)

1. **LLM provider & cost ceiling** — Which provider should be the default for the analysts? Pure-agent strategy across a 1-year daily backtest = ~250 full debates × ~11 agent calls each ≈ thousands of LLM calls. Options: **A)** OpenAI `gpt-5.4-mini` for quick + `gpt-5.4` for deep (default); **B)** Anthropic Claude Haiku/Sonnet; **C)** Local Ollama (free but slow); **D)** Skip the default — require user to set provider explicitly. *Recommendation: A, with hard `max_llm_calls_per_run` budget cap.*
2. **F&O scope in v1** — Options/futures introduce lot-size math, expiry handling, option-PnL nuances, Greeks-aware sizing. Options: **A)** Equity-only in v1 (NSE/BSE), F&O in v2; **B)** Equity + index F&O (NIFTY/BANKNIFTY) in v1, single-stock derivatives later; **C)** Full F&O day 1. *Recommendation: B — index options are a major Indian-market use case and OpenAlgo's `optionchain`/`optiongreeks` make it tractable.*
3. **Persistence of agent transcripts** — Full JSON state per agent run can grow large in long backtests. Options: **A)** Persist all by default; **B)** Persist final-decision only, transcripts on-demand; **C)** Configurable retention. *Recommendation: C, default = last 100 runs full + summaries forever.*
