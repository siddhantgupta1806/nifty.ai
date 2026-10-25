"""DuckDB connection and migration helpers."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb

from nifty_ai.settings import get_settings


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: str | Path | None = None) -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection and ensure the schema exists."""
    path = Path(db_path) if db_path is not None else get_settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(path))
    run_migrations(conn)
    return conn


@contextmanager
def get_db(db_path: str | Path | None = None) -> Iterator[duckdb.DuckDBPyConnection]:
    """Context-managed DuckDB connection."""
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()


def run_migrations(conn: duckdb.DuckDBPyConnection) -> None:
    """Apply the current schema file."""
    conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))


def table_names(conn: duckdb.DuckDBPyConnection) -> set[str]:
    """Return all user table names in the database."""
    rows = conn.execute("SHOW TABLES").fetchall()
    return {str(row[0]) for row in rows}
