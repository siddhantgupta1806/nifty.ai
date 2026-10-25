"""Centralized runtime settings loaded from environment / .env."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide settings, overridable via env vars or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── OpenAlgo ──────────────────────────────────────────────────────────
    openalgo_api_key: str = Field(default="", alias="OPENALGO_API_KEY")
    openalgo_host: str = Field(default="http://127.0.0.1:5000", alias="OPENALGO_HOST")
    openalgo_ws: str = Field(default="ws://127.0.0.1:8765", alias="OPENALGO_WS")
    openalgo_mcp_url: str | None = Field(default=None, alias="OPENALGO_MCP_URL")

    # ── LLM ───────────────────────────────────────────────────────────────
    llm_provider: str = Field(default="openai", alias="NIFTY_AI_LLM_PROVIDER")
    deep_llm: str = Field(default="gpt-5.4", alias="NIFTY_AI_DEEP_LLM")
    quick_llm: str = Field(default="gpt-5.4-mini", alias="NIFTY_AI_QUICK_LLM")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")

    # ── Storage ───────────────────────────────────────────────────────────
    db_path: Path = Field(default=Path(".nifty_ai/nifty.duckdb"), alias="NIFTY_AI_DB_PATH")
    cache_dir: Path = Field(default=Path(".nifty_ai/cache"), alias="NIFTY_AI_CACHE_DIR")
    log_dir: Path = Field(default=Path(".nifty_ai/logs"), alias="NIFTY_AI_LOG_DIR")
    results_dir: Path = Field(default=Path(".nifty_ai/results"), alias="NIFTY_AI_RESULTS_DIR")

    # ── Guardrails ────────────────────────────────────────────────────────
    max_llm_calls_per_run: int = Field(default=2000, alias="NIFTY_AI_MAX_LLM_CALLS_PER_RUN")

    def ensure_dirs(self) -> None:
        """Create storage directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the process-wide Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
