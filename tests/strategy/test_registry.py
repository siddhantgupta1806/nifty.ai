from __future__ import annotations

from pathlib import Path

from nifty_ai.strategy.registry import discover_strategies


def test_discover_strategies_from_file(tmp_path: Path):
    strategy_file = tmp_path / "sample_strategy.py"
    strategy_file.write_text(
        "from nifty_ai.strategy import BaseStrategy\n"
        "class SampleStrategy(BaseStrategy):\n"
        "    def should_long(self): return True\n"
        "    def should_short(self): return False\n"
        "    def go_long(self): return None\n"
        "    def go_short(self): return None\n",
        encoding="utf-8",
    )

    found = discover_strategies(strategy_file)

    assert set(found) == {"SampleStrategy"}