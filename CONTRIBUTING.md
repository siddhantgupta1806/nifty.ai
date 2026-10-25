# Contributing

Thanks for improving Nifty.AI. This project is a research and education tool for Indian-market trading systems.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy .env.example .env
```

Run checks before opening a pull request:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests
```

## Pull Request Guidelines

- Keep changes scoped to one subsystem.
- Add tests for new behavior.
- Do not include API keys, broker credentials, account IDs, or live trading logs.
- Update docs when behavior or setup changes.
- Preserve the educational-use warnings in user-facing docs and UI.

## Trading Safety

Do not submit changes that encourage unattended live trading. Features that place live orders must default to Analyzer Mode or a simulator until explicitly enabled by a human operator.
