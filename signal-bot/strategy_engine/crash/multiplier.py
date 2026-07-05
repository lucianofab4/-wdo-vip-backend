from strategy_engine.base_strategy import BaseStrategy


class MultiplierStrategy(BaseStrategy):
    """
    Entra quando N rodadas consecutivas crasharam abaixo do alvo.
    Ex: 3 crashes < 2x → entra apostando em >= 2x.
    """
    name = "multiplier"
    game = "crash"

    def should_enter(self, history: list) -> tuple[bool, str]:
        target = float(self.config.get("target", 2.0))
        min_streak_low = int(self.config.get("min_streak_low", 3))

        if len(history) < min_streak_low:
            return False, ""

        recent = history[-min_streak_low:]
        all_low = all(r.get("multiplier", 999) < target for r in recent)

        if all_low:
            return True, f"{target}x"

        return False, ""

    def resolve(self, result: dict, entry: str) -> str:
        target = float(entry.replace("x", ""))
        multiplier = result.get("multiplier", 0)
        return "win" if multiplier >= target else "loss"
