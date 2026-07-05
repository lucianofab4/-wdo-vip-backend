from strategy_engine.base_strategy import BaseStrategy

OPPOSITE = {"PLAYER": "BANKER", "BANKER": "PLAYER"}


class ReverseStrategy(BaseStrategy):
    """
    Entra na mesma direção que o último resultado (surfando a tendência).
    Ativa apenas após N iguais consecutivos, apostando na continuidade.
    """
    name = "reverse"
    game = "bacbo"

    def should_enter(self, history: list) -> tuple[bool, str]:
        min_streak = self.config.get("min_streak", 4)
        if len(history) < min_streak:
            return False, ""

        last = history[-1].get("result")
        if last not in ("PLAYER", "BANKER"):
            return False, ""

        count = self.streak(history, "result", last)
        if count >= min_streak:
            # Aposta na continuidade
            return True, last

        return False, ""

    def resolve(self, result: dict, entry: str) -> str:
        outcome = result.get("result")
        if outcome == entry:
            return "win"
        if outcome == "TIE":
            return "pending"
        return "loss"
