"""Dynamic strategy discovery for user-authored files."""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from types import ModuleType

from nifty_ai.strategy.base import BaseStrategy


def load_strategy_module(path: str | Path) -> ModuleType:
    """Import a Python strategy file from disk."""
    file_path = Path(path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    module_name = f"nifty_ai_user_strategy_{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load strategy module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strategies_in_module(module: ModuleType) -> dict[str, type[BaseStrategy]]:
    """Return concrete `BaseStrategy` subclasses found in `module`."""
    found: dict[str, type[BaseStrategy]] = {}
    for name, obj in vars(module).items():
        if not inspect.isclass(obj):
            continue
        if obj is BaseStrategy or not issubclass(obj, BaseStrategy):
            continue
        if inspect.isabstract(obj):
            continue
        found[name] = obj
    return found


def discover_strategies(path: str | Path) -> dict[str, type[BaseStrategy]]:
    """Discover strategies from a file or directory."""
    target = Path(path)
    if target.is_file():
        return strategies_in_module(load_strategy_module(target))

    discovered: dict[str, type[BaseStrategy]] = {}
    for file_path in sorted(target.glob("*.py")):
        if file_path.name.startswith("_"):
            continue
        discovered.update(strategies_in_module(load_strategy_module(file_path)))
    return discovered