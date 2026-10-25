"""High-level constructor for an Indian-market `TradingAgentsGraph`.

This is the only entrypoint the rest of Nifty.AI uses to obtain a configured
multi-agent graph. It guarantees the OpenAlgo vendor patch is applied
*before* the graph is built, so analyst tool nodes resolve to our
OpenAlgo-backed tools.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from nifty_ai.agents.config import build_nifty_config
from nifty_ai.agents.vendor_injection import apply_openalgo_patch


def build_nifty_graph(
    *,
    selected_analysts: Sequence[str] | None = None,
    llm_provider: str | None = None,
    deep_think_llm: str | None = None,
    quick_think_llm: str | None = None,
    max_debate_rounds: int = 1,
    max_risk_discuss_rounds: int = 1,
    max_recur_limit: int = 40,
    results_dir: Path | str | None = None,
    debug: bool = False,
):
    """Return a fully wired ``TradingAgentsGraph`` ready for ``.propagate(...)``.

    Lazily imports ``tradingagents`` so callers that only need the OpenAlgo /
    backtest layers do not pay the heavy LLM-stack import cost.
    """
    apply_openalgo_patch()

    from tradingagents.graph.trading_graph import TradingAgentsGraph  # noqa: WPS433

    config = build_nifty_config(
        llm_provider=llm_provider,
        deep_think_llm=deep_think_llm,
        quick_think_llm=quick_think_llm,
        max_debate_rounds=max_debate_rounds,
        max_risk_discuss_rounds=max_risk_discuss_rounds,
        max_recur_limit=max_recur_limit,
        results_dir=results_dir,
    )

    kwargs: dict = {"config": config, "debug": debug}
    if selected_analysts is not None:
        kwargs["selected_analysts"] = list(selected_analysts)

    return TradingAgentsGraph(**kwargs)
