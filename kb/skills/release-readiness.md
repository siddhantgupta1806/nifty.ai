---
type: skill
name: release-readiness
description: Use before pushing the repository publicly or cutting a release.
---

# Skill: Release Readiness

## Steps

1. Run `pip check`.
2. Run `pytest -q`.
3. Inspect `git status --short` for secrets or generated runtime files.
4. Verify README quickstart commands still match CLI behavior.
5. Verify Docker files are syntactically present; validate on a Docker machine.
6. Confirm `docs/safety.md` and README safety warnings remain prominent.

## Output

Report pass/fail, commands run, warnings, and manual checks still needed.
