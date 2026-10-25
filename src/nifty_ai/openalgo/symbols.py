"""Indian-market symbol formatting & validation for OpenAlgo.

OpenAlgo accepts a single `symbol` string plus an `exchange` field. F&O symbols
follow the pattern `<UNDERLYING><DDMMMYY><STRIKE><CE|PE>` for options and
`<UNDERLYING><DDMMMYY>FUT` for futures (e.g. `NIFTY25MAY2525000CE`,
`RELIANCE30MAY25FUT`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum

from nifty_ai.openalgo.errors import OpenAlgoSymbolError


class Exchange(str, Enum):
    """OpenAlgo exchange codes."""

    NSE = "NSE"
    BSE = "BSE"
    NSE_INDEX = "NSE_INDEX"
    BSE_INDEX = "BSE_INDEX"
    NFO = "NFO"
    BFO = "BFO"
    MCX = "MCX"
    NCDEX = "NCDEX"
    CDS = "CDS"
    BCD = "BCD"


class OptionType(str, Enum):
    CE = "CE"  # Call European
    PE = "PE"  # Put European


_MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


def _fmt_expiry(expiry: date) -> str:
    """Format a date as `DDMMMYY` (e.g. 2025-05-30 → '30MAY25')."""
    return f"{expiry.day:02d}{_MONTHS[expiry.month - 1]}{expiry.year % 100:02d}"


def build_option_symbol(
    underlying: str,
    expiry: date,
    strike: int,
    option_type: OptionType | str,
) -> str:
    """Build an OpenAlgo option symbol.

    >>> build_option_symbol("NIFTY", date(2025, 5, 25), 25000, OptionType.CE)
    'NIFTY25MAY2525000CE'
    """
    underlying = underlying.upper().strip()
    if not underlying:
        raise OpenAlgoSymbolError("underlying must be a non-empty string")
    if strike <= 0:
        raise OpenAlgoSymbolError(f"strike must be positive, got {strike}")
    opt = option_type.value if isinstance(option_type, OptionType) else option_type.upper()
    if opt not in ("CE", "PE"):
        raise OpenAlgoSymbolError(f"option_type must be CE or PE, got {opt!r}")
    return f"{underlying}{_fmt_expiry(expiry)}{strike}{opt}"


def build_future_symbol(underlying: str, expiry: date) -> str:
    """Build an OpenAlgo futures symbol.

    >>> build_future_symbol("NIFTY", date(2025, 5, 25))
    'NIFTY25MAY25FUT'
    """
    underlying = underlying.upper().strip()
    if not underlying:
        raise OpenAlgoSymbolError("underlying must be a non-empty string")
    return f"{underlying}{_fmt_expiry(expiry)}FUT"


@dataclass(frozen=True)
class ParsedOption:
    underlying: str
    expiry: date
    strike: int
    option_type: OptionType


_OPTION_RE = re.compile(
    r"^(?P<underlying>[A-Z]+?)"
    r"(?P<day>\d{2})"
    r"(?P<mon>JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
    r"(?P<yy>\d{2})"
    r"(?P<strike>\d+)"
    r"(?P<opt>CE|PE)$"
)


def parse_option_symbol(symbol: str) -> ParsedOption:
    """Parse an OpenAlgo option symbol into its components.

    >>> p = parse_option_symbol("NIFTY25MAY2525000CE")
    >>> (p.underlying, p.strike, p.option_type.value)
    ('NIFTY', 25000, 'CE')
    """
    m = _OPTION_RE.match(symbol.upper().strip())
    if not m:
        raise OpenAlgoSymbolError(f"not a valid option symbol: {symbol!r}")
    month = _MONTHS.index(m["mon"]) + 1
    year = 2000 + int(m["yy"])
    return ParsedOption(
        underlying=m["underlying"],
        expiry=date(year, month, int(m["day"])),
        strike=int(m["strike"]),
        option_type=OptionType(m["opt"]),
    )


# Standard F&O lot sizes for major underlyings (as of 2025-2026; subject to SEBI revisions).
# Use OpenAlgo `/api/v1/symbol` for the authoritative current lot size.
KNOWN_LOT_SIZES: dict[str, int] = {
    "NIFTY": 75,
    "BANKNIFTY": 30,
    "FINNIFTY": 65,
    "MIDCPNIFTY": 120,
    "SENSEX": 20,
    "BANKEX": 30,
}


def get_known_lot_size(underlying: str) -> int | None:
    """Return a known lot size for an index/stock underlying, or None."""
    return KNOWN_LOT_SIZES.get(underlying.upper())
