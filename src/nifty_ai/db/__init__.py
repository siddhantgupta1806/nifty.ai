"""DuckDB persistence layer (Phase 7)."""

from nifty_ai.db.connection import connect, get_db, run_migrations, table_names

__all__ = ["connect", "get_db", "run_migrations", "table_names"]
