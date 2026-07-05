from strategy_engine.base_strategy import BaseStrategy


class HighLowStrategy(BaseStrategy):
    """
    Analisa frequência de HIGH/LOW numa janela e entra no mais frequente.
    """
    name = "high_low"
    game = "dadinho"

    def should_enter(self, history: list) -> tuple[bool, str]:
        window = self.config.get("window", 10)
        threshold = self.config.get("threshold", 0.65)

        recent = [h for h in history[-window:] if h.get("result_type") in ("HIGH", "LOW")]
        if len(recent) < 5:
            return False, ""

        highs = sum(1 for r in recent if r["result_type"] == "HIGH")
        lows = len(recent) - highs

        if highs / len(recent) >= threshold:
            return True, "HIGH"
        if lows / len(recent) >= threshold:
            return True, "LOW"

        return False, ""

    def resolve(self, result: dict, entry: str) -> str:
        if result.get("result_type") == entry:
            return "win"
        if result.get("result_type") == "EQUAL":
            return "pending"
        return "loss"
