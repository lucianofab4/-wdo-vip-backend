from strategy_engine.base_strategy import BaseStrategy


class SurfStrategy(BaseStrategy):
    """
    Analisa uma janela de resultados e entra no lado com maior frequência.
    """
    name = "surf"
    game = "bacbo"

    def should_enter(self, history: list) -> tuple[bool, str]:
        window = self.config.get("window", 10)
        threshold = self.config.get("threshold", 0.7)

        recent = [h for h in history[-window:] if h.get("result") in ("PLAYER", "BANKER")]
        if len(recent) < window:
            return False, ""

        player_count = sum(1 for r in recent if r["result"] == "PLAYER")
        banker_count = len(recent) - player_count

        player_rate = player_count / len(recent)
        banker_rate = banker_count / len(recent)

        if player_rate >= threshold:
            return True, "PLAYER"
        if banker_rate >= threshold:
            return True, "BANKER"

        return False, ""

    def resolve(self, result: dict, entry: str) -> str:
        outcome = result.get("result")
        if outcome == entry:
            return "win"
        if outcome == "TIE":
            return "pending"
        return "loss"
