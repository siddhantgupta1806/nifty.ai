CREATE TABLE IF NOT EXISTS trade_ledger (
    run_id VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    strategy_name VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    exchange VARCHAR NOT NULL,
    side VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    price DOUBLE NOT NULL,
    commission DOUBLE NOT NULL DEFAULT 0,
    slippage DOUBLE NOT NULL DEFAULT 0,
    product VARCHAR NOT NULL DEFAULT 'MIS',
    pricetype VARCHAR NOT NULL DEFAULT 'MARKET',
    agent_run_id VARCHAR,
    order_tag VARCHAR,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS daily_equity_curve (
    run_id VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    equity DOUBLE NOT NULL,
    cash DOUBLE NOT NULL,
    realized_pnl DOUBLE NOT NULL DEFAULT 0,
    unrealized_pnl DOUBLE NOT NULL DEFAULT 0,
    benchmark_value DOUBLE
);

CREATE TABLE IF NOT EXISTS agent_decisions (
    run_id VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR NOT NULL,
    final_rating VARCHAR NOT NULL,
    confidence DOUBLE,
    transcript_path VARCHAR
);

CREATE TABLE IF NOT EXISTS agent_transcripts (
    run_id VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR NOT NULL,
    state_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS candle_cache (
    exchange VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    ts TIMESTAMP NOT NULL,
    open DOUBLE NOT NULL,
    high DOUBLE NOT NULL,
    low DOUBLE NOT NULL,
    close DOUBLE NOT NULL,
    volume DOUBLE NOT NULL,
    PRIMARY KEY (exchange, symbol, ts)
);

CREATE INDEX IF NOT EXISTS idx_trade_ledger_run_id ON trade_ledger(run_id);
CREATE INDEX IF NOT EXISTS idx_daily_equity_curve_run_id ON daily_equity_curve(run_id);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_run_id ON agent_decisions(run_id);
CREATE INDEX IF NOT EXISTS idx_candle_cache_symbol_ts ON candle_cache(exchange, symbol, ts);
