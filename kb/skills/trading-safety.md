---
type: skill
name: trading-safety-review
description: Use before changing order routing, paper/live behavior, broker integration, or agent-generated trade decisions.
---

# Skill: Trading Safety Review

## When To Use

- Order placement, modification, cancellation, or routing changes.
- Analyzer Mode or live broker behavior changes.
- Strategy sizing, lot-size, product, or exchange logic changes.
- Agent decision parsing or risk overlay changes.

## Checklist

1. Confirm the default path is simulation or Analyzer Mode.
2. Confirm live broker behavior is not silently enabled.
3. Confirm quantity, lot size, product, exchange, and price type are explicit.
4. Confirm LLM output is treated as advisory/fallible.
5. Confirm tests do not require live market connectivity.
6. Confirm docs include educational-use warnings.

## Stop Conditions

Stop and ask for human review if a change could place real orders or expose credentials.
