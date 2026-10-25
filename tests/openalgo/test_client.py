"""Tests for the OpenAlgo HTTP client (mocked with respx)."""

from __future__ import annotations

from datetime import date

import httpx
import pytest
import respx

from nifty_ai.openalgo.client import NiftyOpenAlgoClient
from nifty_ai.openalgo.errors import (
    OpenAlgoAuthError,
    OpenAlgoError,
    OpenAlgoMarketClosedError,
    OpenAlgoRateLimitError,
)

BASE = "http://127.0.0.1:5000"


# ── construction ─────────────────────────────────────────────────────────────


def test_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENALGO_API_KEY", "")
    import nifty_ai.settings as s

    s._settings = None
    with pytest.raises(OpenAlgoAuthError):
        NiftyOpenAlgoClient()


# ── history ──────────────────────────────────────────────────────────────────


@respx.mock
def test_history_returns_unwrapped_data() -> None:
    candles = [
        {
            "time": "2025-04-01 09:15:00",
            "open": 625.5,
            "high": 627.25,
            "low": 625.0,
            "close": 626.75,
            "volume": 12500,
        }
    ]
    route = respx.post(f"{BASE}/api/v1/history").mock(
        return_value=httpx.Response(200, json={"status": "success", "data": candles})
    )
    with NiftyOpenAlgoClient() as client:
        result = client.history(
            symbol="SBIN",
            exchange="NSE",
            interval="5m",
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 8),
        )
    assert result == candles
    assert route.called
    sent = route.calls.last.request.read().decode()
    assert "SBIN" in sent and "5m" in sent and "apikey" in sent


# ── orders ───────────────────────────────────────────────────────────────────


@respx.mock
def test_placeorder_sends_expected_payload() -> None:
    respx.post(f"{BASE}/api/v1/placeorder").mock(
        return_value=httpx.Response(
            200, json={"status": "success", "data": {"orderid": "X-1001"}}
        )
    )
    with NiftyOpenAlgoClient() as client:
        result = client.placeorder(
            strategy="UnitTest",
            symbol="RELIANCE",
            exchange="NSE",
            action="BUY",
            quantity=10,
            pricetype="MARKET",
            product="MIS",
        )
    assert result == {"orderid": "X-1001"}


# ── error mapping ────────────────────────────────────────────────────────────


@respx.mock
def test_auth_error_on_401() -> None:
    respx.post(f"{BASE}/api/v1/funds").mock(
        return_value=httpx.Response(401, json={"status": "error", "message": "invalid"})
    )
    with NiftyOpenAlgoClient() as client, pytest.raises(OpenAlgoAuthError):
        client.funds()


@respx.mock
def test_rate_limit_error_eventually_raises() -> None:
    # respx replays the same response on each retry; tenacity will exhaust attempts
    respx.post(f"{BASE}/api/v1/funds").mock(
        return_value=httpx.Response(429, json={"status": "error", "message": "rate"})
    )
    with NiftyOpenAlgoClient() as client, pytest.raises(OpenAlgoRateLimitError):
        client.funds()


@respx.mock
def test_market_closed_error_from_message() -> None:
    respx.post(f"{BASE}/api/v1/placeorder").mock(
        return_value=httpx.Response(
            200,
            json={"status": "error", "message": "Market is closed outside trading hours"},
        )
    )
    with NiftyOpenAlgoClient() as client, pytest.raises(OpenAlgoMarketClosedError):
        client.placeorder(
            strategy="t",
            symbol="SBIN",
            exchange="NSE",
            action="BUY",
            quantity=1,
        )


@respx.mock
def test_generic_error_status() -> None:
    respx.post(f"{BASE}/api/v1/funds").mock(
        return_value=httpx.Response(
            200, json={"status": "error", "message": "something broke"}
        )
    )
    with NiftyOpenAlgoClient() as client, pytest.raises(OpenAlgoError):
        client.funds()


# ── holidays parsing ─────────────────────────────────────────────────────────


@respx.mock
def test_fetch_holidays_parses_dates() -> None:
    respx.post(f"{BASE}/api/v1/holidays").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": [
                    {"date": "2025-01-26", "holiday_name": "Republic Day"},
                    {"date": "2025-08-15", "holiday_name": "Independence Day"},
                    {"date": "bad-date"},
                ],
            },
        )
    )
    with NiftyOpenAlgoClient() as client:
        h = client.fetch_holidays(2025)
    assert date(2025, 1, 26) in h
    assert date(2025, 8, 15) in h
    assert len(h) == 2  # malformed entry skipped


# ── analyzer helpers ─────────────────────────────────────────────────────────


@respx.mock
def test_analyzer_status_via_helper() -> None:
    from nifty_ai.openalgo import analyzer

    respx.post(f"{BASE}/api/v1/analyzerstatus").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": {"analyzer_mode": True, "virtual_capital": 10_000_000.0},
            },
        )
    )
    with NiftyOpenAlgoClient() as client:
        data = analyzer.analyzer_status(client)
        assert data["analyzer_mode"] is True
        assert analyzer.is_analyzer_on(client) is True
