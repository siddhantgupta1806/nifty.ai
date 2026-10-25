from __future__ import annotations

from datetime import datetime

from nifty_ai.paper import PaperConfig, PaperPreflightError, PaperRunner
from nifty_ai.strategy import BaseStrategy, OrderSide


class FakeClient:
    def __init__(self, analyzer_on: bool = True, cash: float = 100_000) -> None:
        self.analyzer_on = analyzer_on
        self.cash = cash
        self.orders = []
        self.toggles = []

    def _post(self, path, payload):
        if path == "/analyzertoggle":
            self.analyzer_on = bool(payload["mode"])
            self.toggles.append(self.analyzer_on)
            return {"analyzer_mode": self.analyzer_on}
        if path == "/analyzerstatus":
            return {"analyzer_mode": self.analyzer_on}
        raise AssertionError(path)

    def funds(self):
        return {"availablecash": self.cash}

    def positionbook(self):
        return []

    def placeorder(self, **kwargs):
        self.orders.append(kwargs)
        return {"orderid": f"paper-{len(self.orders)}", "status": "success"}


class BuyFirstBar(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.sent = False

    def should_long(self) -> bool:
        return not self.sent

    def should_short(self) -> bool:
        return False

    def go_long(self):
        self.sent = True
        return self.market_order(OrderSide.BUY, 10)

    def go_short(self):
        return None


def test_paper_runner_enables_analyzer_and_places_order():
    client = FakeClient(analyzer_on=False)
    runner = PaperRunner(BuyFirstBar(), client, symbol="RELIANCE", config=PaperConfig(auto_enable_analyzer=True))

    responses = runner.run_bars(
        [{"timestamp": datetime(2026, 5, 27, 9, 15), "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10}]
    )

    assert responses == [{"orderid": "paper-1", "status": "success"}]
    assert client.toggles == [True]
    assert client.orders[0]["symbol"] == "RELIANCE"
    assert client.orders[0]["action"] == "BUY"
    assert client.orders[0]["product"] == "MIS"


def test_paper_runner_preflight_requires_analyzer_when_not_auto_enabled():
    runner = PaperRunner(
        BuyFirstBar(),
        FakeClient(analyzer_on=False),
        symbol="RELIANCE",
        config=PaperConfig(auto_enable_analyzer=False),
    )

    try:
        runner.start()
    except PaperPreflightError as exc:
        assert "Analyzer Mode" in str(exc)
    else:
        raise AssertionError("expected PaperPreflightError")