---
type: hook
name: pre-commit-checklist
trigger: before-commit
---

# Hook: Pre-Commit Checklist

- Run `pytest -q`.
- Run `pip check` when dependencies changed.
- Check no `.env`, `.nifty_ai`, reports, or DuckDB files are tracked.
- Check docs were updated for any changed user command, config key, or API.
- Check safety language for any trading-related user-facing change.
