"""Typed HTTP client over the OpenAlgo REST API.

OpenAlgo runs locally on port 5000 by default. All endpoints are POST and accept
an `apikey` field in the JSON body (or `X-API-KEY` header). This client returns
parsed-and-unwrapped `data` payloads and raises typed errors on failure.

Reference: https://docs.openalgo.in
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from nifty_ai.openalgo.errors import (
    OpenAlgoAuthError,
    OpenAlgoError,
    OpenAlgoMarketClosedError,
    OpenAlgoRateLimitError,
)
from nifty_ai.settings import get_settings

Action = Literal["BUY", "SELL", "SHORT", "COVER"]
PriceType = Literal["LIMIT", "MARKET", "SL", "SL-M"]
Product = Literal["MIS", "NRML", "CNC", "MARGIN"]
Interval = Literal["1m", "3m", "5m", "10m", "15m", "30m", "60m", "1d", "1w", "1mo"]


class NiftyOpenAlgoClient:
    """Synchronous OpenAlgo client.

    All public methods unwrap the OpenAlgo `{status, data}` envelope and return
    `data` directly. Network errors are retried; semantic errors (auth, market
    closed) raise typed exceptions.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        host: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        s = get_settings()
        self._api_key = api_key or s.openalgo_api_key
        self._host = (host or s.openalgo_host).rstrip("/")
        if not self._api_key:
            raise OpenAlgoAuthError("OPENALGO_API_KEY is not set")
        self._client = httpx.Client(
            base_url=self._host,
            timeout=timeout,
            headers={"X-API-KEY": self._api_key, "Content-Type": "application/json"},
        )

    # ── Context manager ────────────────────────────────────────────────────
    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> NiftyOpenAlgoClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ── Core request helper ────────────────────────────────────────────────
    @retry(
        retry=retry_if_exception_type((httpx.TransportError, OpenAlgoRateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
        reraise=True,
    )
    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        body = {"apikey": self._api_key, **payload}
        try:
            resp = self._client.post(f"/api/v1{path}", json=body)
        except httpx.HTTPError as e:
            raise OpenAlgoError(f"transport error calling {path}: {e}") from e

        if resp.status_code == 401:
            raise OpenAlgoAuthError("invalid API key", payload={"path": path})
        if resp.status_code == 429:
            raise OpenAlgoRateLimitError("rate limit exceeded", payload={"path": path})
        if resp.status_code >= 500:
            raise OpenAlgoError(
                f"server error {resp.status_code} on {path}: {resp.text[:200]}"
            )

        try:
            data = resp.json()
        except ValueError as e:
            raise OpenAlgoError(f"non-JSON response on {path}: {resp.text[:200]}") from e

        status = (data.get("status") or "").lower()
        if status == "error":
            msg = str(data.get("message") or "unknown OpenAlgo error")
            low = msg.lower()
            if "market" in low and ("clos" in low or "hour" in low):
                raise OpenAlgoMarketClosedError(msg, payload=data)
            if "rate" in low and "limit" in low:
                raise OpenAlgoRateLimitError(msg, payload=data)
            if "auth" in low or "api key" in low or "apikey" in low:
                raise OpenAlgoAuthError(msg, payload=data)
            raise OpenAlgoError(msg, payload=data)

        if resp.status_code >= 400:
            raise OpenAlgoError(
                f"HTTP {resp.status_code} on {path}: {data}", payload=data
            )
        return data.get("data", data)

    # ── Historical & quote data ────────────────────────────────────────────
    def history(
        self,
        *,
        symbol: str,
        exchange: str,
        interval: Interval,
        start_date: str | date,
        end_date: str | date,
    ) -> list[dict[str, Any]]:
        """Return a list of OHLCV candle dicts.

        Each candle has keys: `time` (string), `open`, `high`, `low`, `close`, `volume`.
        """
        payload = {
            "symbol": symbol,
            "exchange": exchange,
            "interval": interval,
            "start_date": str(start_date),
            "end_date": str(end_date),
        }
        return self._post("/history", payload)

    def quotes(self, *, symbol: str, exchange: str) -> dict[str, Any]:
        return self._post("/quotes", {"symbol": symbol, "exchange": exchange})

    def multiquotes(self, instruments: list[dict[str, str]]) -> list[dict[str, Any]]:
        return self._post("/multiquotes", {"symbols": instruments})

    def depth(self, *, symbol: str, exchange: str) -> dict[str, Any]:
        return self._post("/depth", {"symbol": symbol, "exchange": exchange})

    # ── Orders ─────────────────────────────────────────────────────────────
    def placeorder(
        self,
        *,
        strategy: str,
        symbol: str,
        exchange: str,
        action: Action,
        quantity: int,
        pricetype: PriceType = "MARKET",
        price: float = 0.0,
        trigger_price: float = 0.0,
        product: Product = "MIS",
    ) -> dict[str, Any]:
        return self._post(
            "/placeorder",
            {
                "strategy": strategy,
                "symbol": symbol,
                "exchange": exchange,
                "action": action,
                "quantity": str(quantity),
                "pricetype": pricetype,
                "price": str(price),
                "trigger_price": str(trigger_price),
                "product": product,
            },
        )

    def modifyorder(
        self,
        *,
        orderid: str,
        quantity: int | None = None,
        price: float | None = None,
        pricetype: PriceType | None = None,
        trigger_price: float | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"orderid": orderid}
        if quantity is not None:
            payload["quantity"] = str(quantity)
        if price is not None:
            payload["price"] = str(price)
        if pricetype is not None:
            payload["pricetype"] = pricetype
        if trigger_price is not None:
            payload["trigger_price"] = str(trigger_price)
        return self._post("/modifyorder", payload)

    def cancelorder(self, *, orderid: str) -> dict[str, Any]:
        return self._post("/cancelorder", {"orderid": orderid})

    # ── Account ────────────────────────────────────────────────────────────
    def funds(self) -> dict[str, Any]:
        return self._post("/funds", {})

    def positionbook(self) -> list[dict[str, Any]]:
        return self._post("/positionbook", {})

    def holdings(self) -> list[dict[str, Any]]:
        return self._post("/holdings", {})

    def orderbook(self) -> dict[str, Any]:
        return self._post("/orderbook", {})

    def tradebook(self) -> list[dict[str, Any]]:
        return self._post("/tradebook", {})

    # ── Symbols & options ──────────────────────────────────────────────────
    def search(self, *, query: str, exchange: str | None = None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"query": query}
        if exchange:
            payload["exchange"] = exchange
        return self._post("/search", payload)

    def symbol_info(self, *, symbol: str, exchange: str) -> dict[str, Any]:
        return self._post("/symbol", {"symbol": symbol, "exchange": exchange})

    def optionchain(
        self,
        *,
        underlying: str,
        exchange: str = "NSE_INDEX",
        expiry_date: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"underlying": underlying, "exchange": exchange}
        if expiry_date:
            payload["expiry_date"] = expiry_date
        return self._post("/optionchain", payload)

    def optiongreeks(self, *, symbol: str, exchange: str = "NFO") -> dict[str, Any]:
        return self._post("/optiongreeks", {"symbol": symbol, "exchange": exchange})

    # ── Calendar & timings ─────────────────────────────────────────────────
    def fetch_holidays(self, year: int) -> set[date]:
        """Return the set of holiday dates for a given year."""
        from datetime import datetime as _dt

        data = self._post("/holidays", {"year": year})
        out: set[date] = set()
        for entry in data or []:
            raw = entry.get("date")
            if not raw:
                continue
            try:
                out.add(_dt.strptime(raw, "%Y-%m-%d").date())
            except ValueError:
                continue
        return out

    def timings(self, *, target_date: str | date | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if target_date is not None:
            payload["date"] = str(target_date)
        return self._post("/timings", payload)
