from strategy_engine.base_strategy import BaseStrategy

OPPOSITE = {"PLAYER": "BANKER", "BANKER": "PLAYER"}


class StreakStrategy(BaseStrategy):
    """
    Entra na direção oposta após N resultados iguais consecutivos.
    Ex: 4x BANKER → entra PLAYER.
    """
    name = "streak"
    game = "bacbo"

    def should_enter(self, history: list) -> tuple[bool, str]:
        min_streak = self.config.get("min_streak", 3)
        if len(history) < min_streak:
            return False, ""

        last = history[-1].get("result")
        if last not in ("PLAYER", "BANKER"):
            return False, ""

        count = self.streak(history, "result", last)
        if count >= min_streak:
            entry = OPPOSITE[last]
            return True, entry

        return False, ""

    def resolve(self, result: dict, entry: str) -> str:
        outcome = result.get("result")
        if outcome == entry:
            return "win"
        if outcome == "TIE":
            return "pending"
        return "loss"
