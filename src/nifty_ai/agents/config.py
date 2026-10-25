"""Build an Indian-market-tuned :class:`tradingagents.TradingAgentsConfig`."""

from __future__ import annotations

from pathlib import Path

from nifty_ai.settings import get_settings


def build_nifty_config(
    *,
    llm_provider: str | None = None,
    deep_think_llm: str | None = None,
    quick_think_llm: str | None = None,
    max_debate_rounds: int = 1,
    max_risk_discuss_rounds: int = 1,
    max_recur_limit: int = 40,
    results_dir: Path | str | None = None,
) -> "TradingAgentsConfig":  # type: ignore[name-defined]
    """Return a ``TradingAgentsConfig`` with defaults tuned for Nifty.AI.

    Imports ``tradingagents`` lazily so the rest of the codebase (CLI,
    backtest engine) keeps working when the heavy LLM stack is absent.
    """
    from tradingagents.config import TradingAgentsConfig  # noqa: WPS433

    s = get_settings()
    provider = llm_provider or s.llm_provider or "openai"
    deep = deep_think_llm or s.deep_llm or "gpt-4o"
    quick = quick_think_llm or s.quick_llm or "gpt-4o-mini"
    out_dir = Path(results_dir) if results_dir is not None else Path(s.results_dir)

    return TradingAgentsConfig(
        results_dir=out_dir,
        llm_provider=provider,
        deep_think_llm=deep,
        quick_think_llm=quick,
        max_debate_rounds=max_debate_rounds,
        max_risk_discuss_rounds=max_risk_discuss_rounds,
        max_recur_limit=max_recur_limit,
    )
