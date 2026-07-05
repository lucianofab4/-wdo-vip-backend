from strategy_engine.base_strategy import BaseStrategy

OPPOSITE_TYPE = {"HIGH": "LOW", "LOW": "HIGH"}


class DadinhoStreakStrategy(BaseStrategy):
    """Entra no oposto após N resultados HIGH ou LOW consecutivos."""
    name = "streak"
    game = "dadinho"

    def should_enter(self, history: list) -> tuple[bool, str]:
        min_streak = self.config.get("min_streak", 3)
        relevant = [h for h in history if h.get("result_type") in ("HIGH", "LOW")]
        if len(relevant) < min_streak:
            return False, ""

        last = relevant[-1].get("result_type")
        count = 0
        for item in reversed(relevant):
            if item.get("result_type") == last:
                count += 1
            else:
                break

        if count >= min_streak:
            return True, OPPOSITE_TYPE[last]

        return False, ""

    def resolve(self, result: dict, entry: str) -> str:
        if result.get("result_type") == entry:
            return "win"
        if result.get("result_type") == "EQUAL":
            return "pending"
        return "loss"
