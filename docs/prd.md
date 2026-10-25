This is a comprehensive, end-to-end (E2E) Product Requirement and Architecture Design Document. It is explicitly structured for any agentic coding assistant to parse, generate codebase scaffolds, write modules step-by-step, and implement a production-grade system.

---

# E2E PRD Document

## Project Name: Nifty.AI

**Target Execution Environment:** Agentic coding assistant CLI / Python 3.10+
**Core Tech Stack:** LangGraph, OpenAlgo REST API, DuckDB, QuantStats

---

## 1. Project Overview & Objective

### 1.1 Objective

Build an open-source, multi-agent algorithmic trading and backtesting system tailored for the **Indian Stock Market (NSE/BSE/NFO)**.

### 1.2 System Essence

This project merges the institutional-grade corporate hierarchy of **Tauric Research's TradingAgents** (Analyst $\rightarrow$ Debater $\rightarrow$ Trader $\rightarrow$ Risk Manager) with the execution capabilities and Indian broker connections of **OpenAlgo**, matching the backtesting utility of engines like **Jesse**.

```
                           ┌────────────────────────┐
                           │      Strategy Input    │
                           │  (Python FX / AI Code) │
                           └───────────┬────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LANGGRAPH MULTI-AGENT CORE                            │
│                                                                             │
│  ┌──────────────────────┐        ┌───────────────────┐        ┌──────────┐  │
│  │   Analyst Node       │        │   Debater Node    │        │Risk Node │  │
│  │ (OpenAlgo Hist Data) ├───────►│  (Bull vs Bear)   ├───────►│ (Capital │  │
│  └──────────────────────┘        └───────────────────┘        │ Guard)   │  │
└───────────────────────────────────────────────────────────────┼──────────┘  │
                                                                │             │
                                                                ▼             │
┌────────────────────────┐         ┌────────────────────────┐                 │
│  Analytics / Reporting │◄────────┤     OpenAlgo Engine    │◄────────────────┘
│ (QuantStats Engine /DB)│         │(Sandbox / Live Broker) │
└────────────────────────┘         └────────────────────────┘

```

---

## 2. Functional Requirements (PRD)

### 2.1 Core Features

#### FR-1: Indian Market Compatibility via OpenAlgo

* The system must translate all stock and derivative symbols to OpenAlgo formats (e.g., `NSE:RELIANCE`, `NFO:NIFTY25JUN26000CE`).
* All date-time operations must handle Indian Standard Time (IST) and automatically account for market hours (09:15 to 15:30) and market holidays.

#### FR-2: Engine Modes (Backtest, Paper, Live)

* **Backtest Mode:** Sequential iteration over historical candle data. Simulates fills using historical High/Low/Close data.
* **Paper/Live Mode:** Submits real-time REST API requests directly to OpenAlgo's local server port (default: `8010`).

#### FR-3: Strategy Flexibility

* **Explicit (Human) Mode:** Accepts a Python file containing an entry/exit class or function matching a strict interface.
* **Generative (AI) Mode:** An LLM Agent reviews a markdown prompt outlining a strategy idea, generates a validated Python strategy function, and passes it into the runtime.

#### FR-4: Analytics Tracking & Reporting

* Every trade must log: `Timestamp`, `Symbol`, `Direction` (BUY/SELL), `Price`, `Quantity`, `Execution Type` (Backtest/Paper/Live), and `Realized PnL`.
* Post-run, the engine must render an HTML/Markdown summary detailing the **Sharpe Ratio**, **Sortino Ratio**, **Max Drawdown**, and **Win Rate**.

---

## 3. Architecture & LangGraph Design

The architecture maintains an immutable state object (`AgentState`) passed sequentially across LangGraph nodes.

### 3.1 The Global State Object

```python
from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    # Context
    symbol: str
    current_date: str            # Format: YYYY-MM-DD (or timestamp for intraday)
    mode: str                    # "BACKTEST" | "PAPER" | "LIVE"
    
    # Raw Market Context Data
    market_data: Dict[str, Any]  # Historical OHLCV, current ticker metrics
    news_sentiment: float        # Unified scale from -1.0 (Bearish) to 1.0 (Bullish)
    
    # Strategy Context
    strategy_signal: int         # 1 = Buy, -1 = Sell, 0 = Neutral
    
    # Agent Communication Logs
    analyst_reports: str
    debate_transcript: str
    winning_thesis: str          # "BULL" | "BEAR" | "NEUTRAL"
    
    # Output Instructions
    proposed_action: str         # "BUY" | "SELL" | "HOLD"
    proposed_quantity: int
    final_action: str            # Post-risk assessment clearance
    final_quantity: int

```

### 3.2 LangGraph Nodes & Topology

```
[START] ──► fetch_market_data ──► run_analysts ──► execute_strategy ──► risk_compliance ──► [END]

```

1. **`fetch_market_data_node`**: Intercepts the date/symbol. Queries the local OpenAlgo instance database or historical endpoint to append current context into state.
2. **`run_analysts_node`**: Spawns concurrent analyst prompts (Technical, News, Structural Trend). Synthesizes text reports into `analyst_reports`.
3. **`execute_strategy_node`**:
* *If Human/AI Code:* Runs the provided Python strategy function against the state.
* *If Agentic Debate:* Spawns a Bull vs Bear prompt loop evaluating the reports. Output populates `strategy_signal`.


4. **`risk_compliance_node`**: Evaluates total capital drawdowns, leverage limitations, and asset exposure rules. Adjusts `proposed_quantity` to populate `final_quantity` and `final_action`.

---

## 4. Database Schema (DuckDB File-Backed)

To maximize local processing speed during multi-year backtests, the engine writes directly to an internal file-backed DuckDB database (`ati_vault.db`).

### 4.1 Schema Definition

```sql
-- Execution Log Table
CREATE TABLE IF NOT EXISTS trade_ledger (
    trade_id VARCHAR PRIMARY KEY,
    execution_time TIMESTAMP,
    symbol VARCHAR,
    action VARCHAR,        -- 'BUY', 'SELL'
    price DOUBLE,
    quantity INT,
    execution_mode VARCHAR, -- 'BACKTEST', 'PAPER', 'LIVE'
    realized_pnl DOUBLE DEFAULT 0.0
);

-- Daily Balance Snapshots (For Equity Curve rendering)
CREATE TABLE IF NOT EXISTS daily_equity_curve (
    snapshot_date DATE PRIMARY KEY,
    cash_balance DOUBLE,
    portfolio_value DOUBLE,
    total_equity DOUBLE
);

```

---

## 5. Directory Structure for Code Generation

Instruct the coding assistant to instantiate this exact directory layout before writing functionality:

```text
agentic_trade_india/
│
├── config/
│   ├── __init__.py
│   └── settings.py          # Port mapping (OpenAlgo:8010), LLM Model targets, APIs
│
├── core/
│   ├── __init__.py
│   ├── state.py             # AgentState TypedDict definition
│   ├── graph.py             # LangGraph compilation workflow
│   └── openalgo_client.py   # Client abstraction wrapping OpenAlgo endpoints
│
├── agents/
│   ├── __init__.py
│   ├── analysts.py          # Tech/News analyst prompts and logic
│   ├── debater.py           # Bull/Bear loop structures
│   └── risk_manager.py      # Capital rule validation engine
│
├── strategy/
│   ├── __init__.py
│   ├── interface.py         # Base class template for custom strategies
│   └── factory.py           # Dynamics to load user custom code or invoke AI generator
│
├── database/
│   ├── __init__.py
│   └── connection.py        # DuckDB connections and logging functions
│
├── analytics/
│   ├── __init__.py
│   └── reporting.py         # QuantStats processing and HTML generation script
│
├── main.py                  # Orchestrator CLI entry point
└── requirements.txt

```

---

## 6. Comprehensive Implementation Reference Code

Provide the code blocks below directly to the coding assistant as implementation blueprints.

### 6.1 `core/openalgo_client.py` (The Integration Bridge)

```python
import requests
from typing import Dict, Any, List

class OpenAlgoClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8010", api_key: str = "DefaultKey"):
        self.base_url = base_url
        self.headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    def get_historical_candles(self, exchange: str, symbol: str, interval: str, start: str, end: str) -> List[Dict[str, Any]]:
        """
        Wraps OpenAlgo public history endpoints for Indian Markets
        """
        url = f"{self.base_url}/api/v1/public/history"
        params = {
            "exchange": exchange,
            "symbol": symbol,
            "interval": interval,
            "start_date": start,
            "end_date": end
        }
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception as e:
            print(f"Error querying OpenAlgo history: {e}")
            return []

    def place_order(self, exchange: str, symbol: str, action: str, quantity: int, product: str = "MIS") -> Dict[str, Any]:
        """
        Routes execution straight to OpenAlgo's orders hub (Sandbox or Live)
        """
        url = f"{self.base_url}/api/v1/orders"
        payload = {
            "exchange": exchange,
            "symbol": symbol,
            "action": action.upper(),  # BUY or SELL
            "quantity": quantity,
            "order_type": "MARKET",
            "product": product,        # MIS for Intraday, NRML / CNC for Delivery
            "price": 0,
            "trigger_price": 0
        }
        response = requests.post(url, json=payload, headers=self.headers, timeout=5)
        return response.json()

```

### 6.2 `strategy/interface.py` (The Base Class Contract)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseStrategy(ABC):
    @abstractmethod
    def evaluate(self, market_data: Dict[str, Any]) -> int:
        """
        Executes structural strategy tracking.
        Returns:
             1  -> Strong Bullish / Buy Signal
            -1  -> Strong Bearish / Sell Signal
             0  -> Neutral / Hold Signal
        """
        pass

```

### 6.3 `analytics/reporting.py` (Performance Analysis Metrics)

```python
import duckdb
import pandas as pd
import quantstats as qs
import os

def generate_performance_report(db_path: str = "ati_vault.db", output_html: str = "report.html"):
    """
    Extracts daily returns records and compiles institutional metric views
    """
    con = duckdb.connect(db_path)
    
    # Extrapolate returns from the daily equity curve ledger
    df = con.execute("""
        SELECT snapshot_date, total_equity 
        FROM daily_equity_curve 
        ORDER BY snapshot_date ASC
    """).df()
    
    con.close()
    
    if df.empty or len(df) < 2:
        print("Insufficient historical database intervals to generate reporting structures.")
        return

    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
    df.set_index('snapshot_date', inplace=True)
    
    # Calculate daily percentage return profiles
    df['returns'] = df['total_equity'].pct_change()
    df.dropna(inplace=True)
    
    # Render static report
    qs.extend_pandas()
    qs.reports.html(df['returns'], output=output_html, title="Nifty.AI Performance Strategy Report")
    print(f"Analytics report generated successfully at: {os.path.abspath(output_html)}")

```

---

## 7. Step-by-Step Prompt Execution Guide for Coding Assistants

To build this entire codebase using an agentic coding assistant, feed it the following precise prompt sequence:

1. **Step 1 (Scaffolding):**
> "Read the directory specification outlined in section 5 of the provided document. Create the basic package structure, populate `requirements.txt` with `langgraph`, `requests`, `duckdb`, `quantstats`, `pandas`, and create empty `__init__.py` modules across all directories."


2. **Step 2 (Core Interfaces):**
> "Implement the state machine specification (`core/state.py`), the abstract base strategy definition (`strategy/interface.py`), and the OpenAlgo REST connection interface (`core/openalgo_client.py`). Ensure full type-hint enforcement."


3. **Step 3 (Agent Architecture):**
> "Implement the LangGraph nodes inside `core/graph.py` using standard components. Link the analytical research nodes to pass feedback data down into the risk mitigation validation models before finalizing transaction payloads."


4. **Step 4 (Database Integration & Main Loop):**
> "Write the DuckDB synchronization operations inside `database/connection.py`. Connect the analytical reporting module (`analytics/reporting.py`) and write an interactive CLI terminal orchestrator inside `main.py` that lets me toggle between backtesting historical candles and running live paper trading against the OpenAlgo sandbox environment."