"""Hybrid Python signal + risk overlay example."""

from nifty_ai.strategy import HybridStrategy


class HybridNiftyStrategy(HybridStrategy):
    name = "hybrid_nifty"
    timeframe = "1m"

    def python_should_long(self) -> bool:
        if len(self.candles) < 5 or self.position.is_open:
            return False
        return bool(self.candles["close"].iloc[-1] > self.candles["close"].rolling(5).mean().iloc[-1])
