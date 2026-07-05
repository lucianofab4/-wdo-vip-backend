import statistics
from strategy_engine.base_strategy import BaseStrategy


class TimingStrategy(BaseStrategy):
    """
    Entra quando a média dos últimos N multiplicadores está abaixo do histórico.
    Indica que a volatilidade pode gerar um multiplicador maior.
    """
    name = "timing"
    game = "crash"

    def should_enter(self, history: list) -> tuple[bool, str]:
        window = int(self.config.get("window", 10))
        long_window = int(self.config.get("long_window", 30))
        target = float(self.config.get("target", 1.5))

        if len(history) < long_window:
            return False, ""

        recent_avg = statistics.mean(r["multiplier"] for r in history[-window:])
        long_avg = statistics.mean(r["multiplier"] for r in history[-long_window:])

        # Entra quando média recente está significativamente abaixo da média longa
        if recent_avg < long_avg * 0.6:
            return True, f"{target}x"

        return False, ""

    def resolve(self, result: dict, entry: str) -> str:
        target = float(entry.replace("x", ""))
        return "win" if result.get("multiplier", 0) >= target else "loss"
