.PHONY: install install-dev test lint fmt typecheck clean web mcp backtest report docker-build docker-up

PY ?= python

install:
	$(PY) -m pip install -e .

install-dev:
	$(PY) -m pip install -e ".[dev]"
	pre-commit install || true

test:
	$(PY) -m pytest -q

lint:
	ruff check src tests

fmt:
	ruff format src tests
	ruff check --fix src tests

typecheck:
	mypy src/nifty_ai

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov .nifty_ai/reports

web:
	nifty web --port 8766

mcp:
	nifty-mcp

backtest:
	nifty backtest --strategy examples/strategies/ema_cross.py --candles examples/data/reliance_1m.csv --symbol RELIANCE --capital 1000000 --persist-db .nifty_ai/nifty.duckdb

report:
	nifty report --run-id $(RUN_ID) --db .nifty_ai/nifty.duckdb --out reports/report.html

docker-build:
	docker build -t nifty-ai .

docker-up:
	docker compose up --build
