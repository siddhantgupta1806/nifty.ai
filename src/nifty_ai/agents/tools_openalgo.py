"""OpenAlgo-backed LangChain tools for TradingAgents analyst nodes.

These tools mirror the upstream `tradingagents.agents.utils.*_tools` signatures
so they are drop-in replacements via the `ANALYST_TOOL_REGISTRY` patch in
`vendor_injection.py`. They route every data call through OpenAlgo
(`NiftyOpenAlgoClient`) instead of yfinance.

For domains OpenAlgo does not cover yet (Indian-equity fundamentals,
insider trades, institutional holders, earnings calendar), we return a
`[NO_DATA]` message so the LLM degrades gracefully instead of hallucinating.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timedelta
from typing import Annotated, Iterable

import pandas as pd
from langchain_core.tools import tool

from nifty_ai.openalgo.client import NiftyOpenAlgoClient
from nifty_ai.openalgo.errors import OpenAlgoError
from nifty_ai.openalgo.symbols import Exchange
from nifty_ai.settings import get_settings

logger = logging.getLogger(__name__)

_NO_DATA = "[NO_DATA]"
_TOOL_ERROR = "[TOOL_ERROR]"
_DEFAULT_EXCHANGE = Exchange.NSE


# --------------------------------------------------------------------------- #
# Client + exchange resolution
# --------------------------------------------------------------------------- #


_client_singleton: NiftyOpenAlgoClient | None = None


def get_client() -> NiftyOpenAlgoClient:
    """Return a process-wide `NiftyOpenAlgoClient` built from settings."""
    global _client_singleton
    if _client_singleton is None:
        s = get_settings()
        _client_singleton = NiftyOpenAlgoClient(
            api_key=s.openalgo_api_key,
            host=s.openalgo_host,
        )
    return _client_singleton


def set_client(client: NiftyOpenAlgoClient | None) -> None:
    """Override the singleton (used by tests + advanced wiring)."""
    global _client_singleton
    _client_singleton = client


def _resolve_exchange(symbol: str) -> Exchange:
    """Best-effort exchange resolution from a raw symbol string.

    Indices route to NSE_INDEX/BSE_INDEX, derivatives symbols (with embedded
    expiry tokens) route to NFO/BFO. Everything else defaults to NSE.
    """
    upper = symbol.upper().strip()
    if upper in {"NIFTY", "BANKNIFTY", "FINNIFTY", "NIFTYNXT50", "MIDCPNIFTY"}:
        return Exchange.NSE_INDEX
    if upper in {"SENSEX", "BANKEX"}:
        return Exchange.BSE_INDEX
    # NFO option symbols look like NIFTY25MAY2525000CE — contain digits + CE/PE
    if any(upper.endswith(suffix) for suffix in ("CE", "PE")) and any(ch.isdigit() for ch in upper):
        return Exchange.NFO
    return _DEFAULT_EXCHANGE


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _fetch_history_df(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = "D",
    exchange: Exchange | None = None,
) -> pd.DataFrame:
    """Call OpenAlgo `history`, return a normalised DataFrame indexed by datetime."""
    ex = exchange or _resolve_exchange(symbol)
    client = get_client()
    payload = client.history(
        symbol=symbol,
        exchange=ex.value,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
    )
    if not payload:
        return pd.DataFrame()
    df = pd.DataFrame(payload)
    # OpenAlgo returns either 'timestamp' (epoch) or 'date'; normalise to a
    # DatetimeIndex named 'Date' so stockstats / downstream code is identical
    # to yfinance shape.
    if "timestamp" in df.columns:
        df["Date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_convert(
            "Asia/Kolkata"
        ).dt.tz_localize(None)
    elif "date" in df.columns:
        df["Date"] = pd.to_datetime(df["date"])
    else:
        return pd.DataFrame()
    rename = {"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
    df = df.rename(columns=rename)
    keep = ["Date", "Open", "High", "Low", "Close", "Volume"]
    keep = [c for c in keep if c in df.columns]
    df = df[keep].sort_values("Date").reset_index(drop=True)
    return df


def _df_to_csv_report(df: pd.DataFrame, symbol: str, start_date: str, end_date: str) -> str:
    """Format a candle DataFrame as the CSV-with-header string the analysts expect."""
    if df.empty:
        return f"{_NO_DATA} No OpenAlgo candles for {symbol} in {start_date}..{end_date}."
    header = (
        f"# Source: OpenAlgo (NSE/BSE)\n"
        f"# Symbol: {symbol}\n"
        f"# Window: {start_date}..{end_date} (IST trading days only)\n"
    )
    buf = io.StringIO()
    df.to_csv(buf, index=False, date_format="%Y-%m-%d %H:%M:%S")
    return header + buf.getvalue()


# --------------------------------------------------------------------------- #
# Public LangChain tools (drop-in replacements for upstream)
# --------------------------------------------------------------------------- #


@tool
def get_stock_data(
    symbol: Annotated[str, "NSE/BSE trading symbol, e.g. RELIANCE, TCS, NIFTY"],
    start_date: Annotated[str, "Start date YYYY-MM-DD"],
    end_date: Annotated[str, "End date YYYY-MM-DD"],
) -> str:
    """Retrieve daily OHLCV history for an Indian-market symbol via OpenAlgo.

    Returns CSV-formatted candles with a short metadata header, or a
    `[NO_DATA]` message if OpenAlgo has no data for the window.
    """
    try:
        df = _fetch_history_df(symbol, start_date, end_date, interval="D")
        return _df_to_csv_report(df, symbol, start_date, end_date)
    except OpenAlgoError as exc:
        logger.warning("get_stock_data failed for %s: %s", symbol, exc)
        return f"{_TOOL_ERROR} {type(exc).__name__}: {exc}"


@tool
def get_indicators(
    symbol: Annotated[str, "NSE/BSE trading symbol"],
    indicator: Annotated[
        str | list[str],
        "Indicator name(s). Accepts a single name, list, or comma-separated string.",
    ],
    curr_date: Annotated[str, "Current trading date YYYY-MM-DD"],
    look_back_days: Annotated[int, "Number of trading days to look back"] = 30,
) -> str:
    """Compute technical indicators for an Indian-market symbol via OpenAlgo + stockstats."""
    if isinstance(indicator, str):
        wanted = [i.strip() for i in indicator.split(",") if i.strip()]
    else:
        wanted = [i.strip() for i in indicator if i and i.strip()]
    if not wanted:
        return f"{_TOOL_ERROR} At least one indicator is required."

    try:
        end = datetime.strptime(curr_date, "%Y-%m-%d")
    except ValueError:
        return f"{_TOOL_ERROR} curr_date must be YYYY-MM-DD."

    # Pull enough history for the longest typical lookback (e.g. SMA-200) + look_back_days.
    history_start = (end - timedelta(days=max(look_back_days, 30) + 365)).strftime("%Y-%m-%d")
    history_end = end.strftime("%Y-%m-%d")

    try:
        df = _fetch_history_df(symbol, history_start, history_end, interval="D")
    except OpenAlgoError as exc:
        return f"{_TOOL_ERROR} {type(exc).__name__}: {exc}"
    if df.empty:
        return f"{_NO_DATA} No OpenAlgo candles for {symbol} up to {curr_date}."

    try:
        from stockstats import wrap  # type: ignore
    except ImportError:
        return f"{_TOOL_ERROR} stockstats is not installed; cannot compute indicators."

    df_lower = df.rename(
        columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    )
    wrapped = wrap(df_lower)

    cutoff = end
    window_start = end - timedelta(days=look_back_days)
    out_sections = []
    for name in wanted:
        try:
            series = wrapped[name]
        except Exception as exc:  # noqa: BLE001 — stockstats raises plain Exceptions
            out_sections.append(f"## {name}\n{_TOOL_ERROR} unsupported indicator: {exc}\n")
            continue
        slice_df = pd.DataFrame({"Date": df["Date"], name: series}).dropna()
        slice_df = slice_df[(slice_df["Date"] >= window_start) & (slice_df["Date"] <= cutoff)]
        if slice_df.empty:
            out_sections.append(f"## {name}\n{_NO_DATA}\n")
            continue
        buf = io.StringIO()
        slice_df.to_csv(buf, index=False, date_format="%Y-%m-%d")
        out_sections.append(f"## {name} ({window_start.date()}..{cutoff.date()})\n{buf.getvalue()}")

    header = (
        f"# Source: OpenAlgo + stockstats\n"
        f"# Symbol: {symbol}\n"
        f"# Current date: {curr_date}, look_back_days={look_back_days}\n\n"
    )
    return header + "\n".join(out_sections)


@tool
def get_dividends_splits(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Indian corporate-action history is not provided by OpenAlgo in v1."""
    return f"{_NO_DATA} Dividends/splits feed not available via OpenAlgo for {ticker}."


@tool
def get_news(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    start_date: Annotated[str, "Start date YYYY-MM-DD"],
    end_date: Annotated[str, "End date YYYY-MM-DD"],
) -> str:
    """News feed for Indian equities is not yet integrated (v2 backlog)."""
    return (
        f"{_NO_DATA} News feed for Indian markets is not wired in v1. "
        f"Proceed using price action and structural context only."
    )


@tool
def get_global_news(
    curr_date: Annotated[str, "Current date YYYY-MM-DD"],
    look_back_days: Annotated[int, "Look-back window in days"] = 7,
    limit: Annotated[int, "Maximum articles"] = 5,
) -> str:
    """Global news feed is not wired in v1 for the India build."""
    return f"{_NO_DATA} Global news feed disabled in Nifty.AI v1."


@tool
def get_insider_transactions(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Indian SAST/insider-trade feed is not available via OpenAlgo."""
    return f"{_NO_DATA} Insider transactions feed not available for {ticker} in v1."


@tool
def get_market_context(
    curr_date: Annotated[str, "Current date YYYY-MM-DD"],
) -> str:
    """Macro/market-context feed is not wired in v1."""
    return f"{_NO_DATA} Market-context feed not wired in v1."


@tool
def get_earnings_calendar(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Earnings calendar is not wired in v1 for the India build."""
    return f"{_NO_DATA} Earnings calendar not available for {ticker} in v1."


@tool
def get_fundamentals(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    curr_date: Annotated[str, "Current date YYYY-MM-DD"],
) -> str:
    """Indian fundamentals (P&L, balance sheet) are deferred to v2."""
    return (
        f"{_NO_DATA} Indian fundamentals integration deferred to v2 for {ticker}. "
        f"Base your view on price action, technicals, and option-chain signal only."
    )


@tool
def get_balance_sheet(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    freq: Annotated[str, "annual or quarterly"] = "quarterly",
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Balance sheet data is not wired in v1 for Indian equities."""
    return f"{_NO_DATA} Balance sheet feed not wired in v1 for {ticker}."


@tool
def get_cashflow(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    freq: Annotated[str, "annual or quarterly"] = "quarterly",
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Cashflow statement data is not wired in v1 for Indian equities."""
    return f"{_NO_DATA} Cashflow statement feed not wired in v1 for {ticker}."


@tool
def get_income_statement(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    freq: Annotated[str, "annual or quarterly"] = "quarterly",
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Income statement data is not wired in v1 for Indian equities."""
    return f"{_NO_DATA} Income statement feed not wired in v1 for {ticker}."


@tool
def get_analyst_ratings(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Sell-side analyst ratings are not wired in v1 for Indian equities."""
    return f"{_NO_DATA} Sell-side analyst ratings feed not wired in v1 for {ticker}."


@tool
def get_short_interest(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Short-interest data is not wired in v1 for Indian equities."""
    return f"{_NO_DATA} Short-interest feed not wired in v1 for {ticker}."


@tool
def get_institutional_holders(
    ticker: Annotated[str, "NSE/BSE trading symbol"],
    curr_date: Annotated[str | None, "Current date YYYY-MM-DD"] = None,
) -> str:
    """Institutional holder data is not wired in v1 for Indian equities."""
    return f"{_NO_DATA} Institutional holders feed not wired in v1 for {ticker}."


# --------------------------------------------------------------------------- #
# Extra derivatives tools (exposed to a Derivatives Analyst in Phase 8)
# --------------------------------------------------------------------------- #


@tool
def get_option_chain(
    underlying: Annotated[str, "Underlying symbol, e.g. NIFTY, BANKNIFTY, RELIANCE"],
    expiry: Annotated[str, "Expiry date YYYY-MM-DD"],
) -> str:
    """Fetch the full option chain for an underlying + expiry via OpenAlgo."""
    try:
        chain = get_client().optionchain(symbol=underlying, expiry=expiry)
    except OpenAlgoError as exc:
        return f"{_TOOL_ERROR} {type(exc).__name__}: {exc}"
    if not chain:
        return f"{_NO_DATA} No option chain returned for {underlying} expiry {expiry}."
    df = pd.DataFrame(chain)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return f"# OpenAlgo option chain — {underlying} expiry {expiry}\n" + buf.getvalue()


@tool
def get_option_greeks(
    symbol: Annotated[str, "Full option symbol, e.g. NIFTY25MAY2525000CE"],
) -> str:
    """Fetch Greeks (delta/gamma/theta/vega/IV) for a single option contract."""
    try:
        greeks = get_client().optiongreeks(symbol=symbol)
    except OpenAlgoError as exc:
        return f"{_TOOL_ERROR} {type(exc).__name__}: {exc}"
    if not greeks:
        return f"{_NO_DATA} No greeks returned for {symbol}."
    lines = [f"# OpenAlgo greeks — {symbol}"]
    for k, v in greeks.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)


# Tuples used by `vendor_injection.py` to overwrite ANALYST_TOOL_REGISTRY.
# Keep names matching upstream so analyst prompts (which list tool names)
# still resolve.

OPENALGO_MARKET_TOOLS: tuple = (get_stock_data, get_indicators, get_dividends_splits)
OPENALGO_SOCIAL_TOOLS: tuple = (get_news,)
OPENALGO_NEWS_TOOLS: tuple = (
    get_news,
    get_global_news,
    get_insider_transactions,
    get_market_context,
    get_earnings_calendar,
)
OPENALGO_FUNDAMENTALS_TOOLS: tuple = (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_analyst_ratings,
    get_institutional_holders,
    get_short_interest,
    get_dividends_splits,
)
OPENALGO_DERIVATIVES_TOOLS: tuple = (get_option_chain, get_option_greeks)


def all_openalgo_tools() -> Iterable:
    yield from OPENALGO_MARKET_TOOLS
    yield from OPENALGO_NEWS_TOOLS
    yield from OPENALGO_FUNDAMENTALS_TOOLS
    yield from OPENALGO_DERIVATIVES_TOOLS
