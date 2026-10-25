"""Tests for symbol formatting / parsing."""

from __future__ import annotations

from datetime import date

import pytest

from nifty_ai.openalgo.errors import OpenAlgoSymbolError
from nifty_ai.openalgo.symbols import (
    Exchange,
    OptionType,
    build_future_symbol,
    build_option_symbol,
    get_known_lot_size,
    parse_option_symbol,
)


def test_build_option_symbol_basic() -> None:
    assert build_option_symbol("NIFTY", date(2025, 5, 25), 25000, OptionType.CE) == "NIFTY25MAY2525000CE"
    assert build_option_symbol("BANKNIFTY", date(2025, 11, 30), 50000, "PE") == "BANKNIFTY30NOV2550000PE"


def test_build_option_symbol_lowercase_underlying_normalized() -> None:
    assert build_option_symbol("nifty", date(2025, 1, 1), 100, OptionType.CE) == "NIFTY01JAN25100CE"


def test_build_option_symbol_validates() -> None:
    with pytest.raises(OpenAlgoSymbolError):
        build_option_symbol("", date(2025, 5, 1), 100, OptionType.CE)
    with pytest.raises(OpenAlgoSymbolError):
        build_option_symbol("NIFTY", date(2025, 5, 1), 0, OptionType.CE)
    with pytest.raises(OpenAlgoSymbolError):
        build_option_symbol("NIFTY", date(2025, 5, 1), 100, "XX")


def test_build_future_symbol() -> None:
    assert build_future_symbol("RELIANCE", date(2025, 5, 30)) == "RELIANCE30MAY25FUT"
    assert build_future_symbol("nifty", date(2025, 5, 25)) == "NIFTY25MAY25FUT"


def test_parse_option_symbol_roundtrip() -> None:
    sym = build_option_symbol("NIFTY", date(2025, 5, 25), 25000, OptionType.CE)
    parsed = parse_option_symbol(sym)
    assert parsed.underlying == "NIFTY"
    assert parsed.expiry == date(2025, 5, 25)
    assert parsed.strike == 25000
    assert parsed.option_type is OptionType.CE


def test_parse_option_symbol_rejects_invalid() -> None:
    with pytest.raises(OpenAlgoSymbolError):
        parse_option_symbol("RELIANCE-EQ")


def test_known_lot_sizes() -> None:
    assert get_known_lot_size("NIFTY") == 75
    assert get_known_lot_size("nifty") == 75
    assert get_known_lot_size("UNKNOWNCO") is None


def test_exchange_enum_values() -> None:
    assert Exchange.NSE.value == "NSE"
    assert Exchange.NFO.value == "NFO"
    assert Exchange.NSE_INDEX.value == "NSE_INDEX"
