# Strategies

Strategies subclass `BaseStrategy` and receive a `StrategyContext` before each bar.

## Required Hooks

- `should_long()`
- `should_short()`
- `go_long()`
- `go_short()`

## Optional Hooks

- `before()`
- `after()`
- `update_position()`
- `should_cancel_entry()`
- `on_open_position()`
- `on_close_position()`

## Runtime Properties

Strategies can read:

- `self.symbol`
- `self.timestamp`
- `self.price`
- `self.candles`
- `self.position`
- `self.balance`
- `self.portfolio_value`
- `self.is_backtesting`
- `self.is_papertrading`

## Order Creation

Use `self.market_order(...)` or construct `OrderIntent` directly. The engine consumes intents and the broker simulator decides whether/how they fill.

## Modes

- Human Python: deterministic rules.
- Pure agent: `AgentStrategy` delegates to TradingAgents.
- Hybrid: deterministic signal plus risk overlay.

See `examples/strategies` for working templates.
