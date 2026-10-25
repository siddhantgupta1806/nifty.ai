"""IST-aware market calendar utilities for Indian exchanges.

Regular equity hours: 09:15–15:30 IST (pre-open 09:00–09:15, post-close 15:40–16:00).
Commodity (MCX) day session: 09:00–23:30 IST. Holiday list comes from OpenAlgo's
`/api/v1/holidays` endpoint and is cached per-process.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

import pytz

if TYPE_CHECKING:
    from nifty_ai.openalgo.client import NiftyOpenAlgoClient


IST = pytz.timezone("Asia/Kolkata")

# Regular equity / index segment
EQUITY_OPEN = time(9, 15)
EQUITY_CLOSE = time(15, 30)
MIS_SQUARE_OFF = time(15, 20)  # auto square-off for MIS intraday

# Pre/post sessions
PRE_OPEN_START = time(9, 0)
POST_CLOSE_END = time(16, 0)


def now_ist() -> datetime:
    """Current wall-clock time in IST (tz-aware)."""
    return datetime.now(IST)


def to_ist(dt: datetime) -> datetime:
    """Convert any tz-aware/naive datetime to IST (naive treated as UTC)."""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(IST)


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5  # 5 = Sat, 6 = Sun


def is_market_open(
    dt: datetime | None = None,
    *,
    holidays: set[date] | None = None,
    segment: str = "equity",
) -> bool:
    """Return True if the market is open at `dt` (default: now in IST)."""
    dt = to_ist(dt) if dt else now_ist()
    if is_weekend(dt.date()):
        return False
    if holidays and dt.date() in holidays:
        return False
    t = dt.time()
    if segment == "equity":
        return EQUITY_OPEN <= t <= EQUITY_CLOSE
    if segment == "commodity":
        return time(9, 0) <= t <= time(23, 30)
    raise ValueError(f"unknown segment: {segment!r}")


def next_trading_day(d: date, holidays: set[date] | None = None) -> date:
    """Return the next non-weekend, non-holiday trading day strictly after `d`."""
    holidays = holidays or set()
    cur = d + timedelta(days=1)
    while is_weekend(cur) or cur in holidays:
        cur += timedelta(days=1)
    return cur


def is_trading_day(d: date, holidays: set[date] | None = None) -> bool:
    """Return True if `d` is a regular weekday and not in the holiday set."""
    return not is_weekend(d) and (d not in (holidays or set()))


@dataclass(frozen=True)
class Session:
    open_at: datetime  # tz-aware IST
    close_at: datetime
    square_off_at: datetime


def session_for(d: date) -> Session:
    """Return the IST session boundaries for a given equity trading day."""
    return Session(
        open_at=IST.localize(datetime.combine(d, EQUITY_OPEN)),
        close_at=IST.localize(datetime.combine(d, EQUITY_CLOSE)),
        square_off_at=IST.localize(datetime.combine(d, MIS_SQUARE_OFF)),
    )


class HolidayCache:
    """Per-process holiday cache; lazily fetches via the OpenAlgo client."""

    def __init__(self, client: NiftyOpenAlgoClient) -> None:
        self._client = client
        self._cache: dict[int, set[date]] = {}

    def holidays(self, year: int) -> set[date]:
        if year not in self._cache:
            self._cache[year] = self._client.fetch_holidays(year)
        return self._cache[year]

    def is_holiday(self, d: date) -> bool:
        return d in self.holidays(d.year)

    def next_trading_day(self, d: date) -> date:
        return next_trading_day(d, self.holidays(d.year))
