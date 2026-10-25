# Safety and Educational Use

Nifty.AI is an educational research project. It is not financial advice, not a SEBI-registered advisory product, and not a production trading system.

## Do Not Live Trade

Do not use this project to place live trades. LLM-generated outputs can be wrong, stale, overconfident, or inconsistent with market rules.

## Safe Defaults

- Backtesting is offline and deterministic.
- Paper trading uses OpenAlgo Analyzer Mode.
- Unit tests use mocks and local fixtures.
- User-facing docs warn against live trading.

## Manual Checks Before Paper Trading

1. OpenAlgo is running locally.
2. Analyzer Mode is enabled.
3. Broker adapter is not in live mode.
4. Symbol, exchange, product, and quantity are correct.
5. Strategy behavior was tested offline first.

## Secrets

Never commit `.env`, API keys, broker credentials, account IDs, generated DuckDB files, or reports containing account data.
