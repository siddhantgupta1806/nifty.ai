---
type: hook
name: post-implementation-review
trigger: after-feature-implementation
---

# Hook: Post-Implementation Review

- Identify public surfaces touched: CLI, web, MCP, docs, schema, tests.
- Confirm the new behavior has at least one focused test.
- Confirm shared logic lives in `services/` when used by multiple interfaces.
- Confirm no live OpenAlgo call is introduced into default tests.
- Record any manual validation needed in `docs/TODO.md`.