"""Tests for IST calendar utilities."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from nifty_ai.openalgo.calendar import (
    IST,
    is_market_open,
    is_trading_day,
    is_weekend,
    next_trading_day,
    session_for,
)


def test_is_weekend() -> None:
    assert is_weekend(date(2025, 5, 24))  # Saturday
    assert is_weekend(date(2025, 5, 25))  # Sunday
    assert not is_weekend(date(2025, 5, 23))  # Friday


def test_is_market_open_during_session() -> None:
    # Friday 2025-05-23 11:00 IST
    dt = IST.localize(datetime(2025, 5, 23, 11, 0))
    assert is_market_open(dt)


def test_is_market_open_before_open() -> None:
    dt = IST.localize(datetime(2025, 5, 23, 8, 0))
    assert not is_market_open(dt)


def test_is_market_open_after_close() -> None:
    dt = IST.localize(datetime(2025, 5, 23, 16, 0))
    assert not is_market_open(dt)


def test_is_market_open_on_weekend() -> None:
    dt = IST.localize(datetime(2025, 5, 24, 11, 0))
    assert not is_market_open(dt)


def test_is_market_open_on_holiday() -> None:
    holidays = {date(2025, 5, 23)}
    dt = IST.localize(datetime(2025, 5, 23, 11, 0))
    assert not is_market_open(dt, holidays=holidays)


def test_next_trading_day_skips_weekend() -> None:
    # Friday → Monday
    assert next_trading_day(date(2025, 5, 23)) == date(2025, 5, 26)


def test_next_trading_day_skips_holidays() -> None:
    holidays = {date(2025, 5, 26)}  # Monday is a holiday
    assert next_trading_day(date(2025, 5, 23), holidays) == date(2025, 5, 27)


def test_is_trading_day() -> None:
    assert is_trading_day(date(2025, 5, 23))  # Friday
    assert not is_trading_day(date(2025, 5, 24))  # Saturday
    assert not is_trading_day(date(2025, 5, 23), {date(2025, 5, 23)})


def test_session_for_boundaries() -> None:
    sess = session_for(date(2025, 5, 23))
    assert sess.open_at.hour == 9 and sess.open_at.minute == 15
    assert sess.close_at.hour == 15 and sess.close_at.minute == 30
    assert sess.square_off_at.hour == 15 and sess.square_off_at.minute == 20


def test_is_market_open_invalid_segment() -> None:
    dt = IST.localize(datetime(2025, 5, 23, 11, 0))
    with pytest.raises(ValueError):
        is_market_open(dt, segment="forex")
