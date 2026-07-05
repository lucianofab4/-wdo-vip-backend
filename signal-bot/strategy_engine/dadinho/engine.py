from collections import deque
from loguru import logger
from sqlalchemy import select
from database.connection import AsyncSessionFactory
from database.models import StrategyConfig
from strategy_engine.dadinho.streak import DadinhoStreakStrategy
from strategy_engine.dadinho.high_low import HighLowStrategy
from strategy_engine.signal_dispatcher import dispatch_signal, update_signal_status


STRATEGY_CLASSES = {
    "streak": DadinhoStreakStrategy,
    "high_low": HighLowStrategy,
}


class DadinhoEngine:
    def __init__(self):
        self._history: deque = deque(maxlen=100)
        self._open_signals: dict[str, dict] = {}

    async def _load_strategies(self) -> list:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(StrategyConfig).where(
                    StrategyConfig.game == "dadinho",
                    StrategyConfig.is_active == True,
                )
            )
            configs = result.scalars().all()

        strategies = []
        for cfg in configs:
            cls = STRATEGY_CLASSES.get(cfg.strategy)
            if cls:
                strategies.append(cls(config=cfg.config))
        return strategies

    async def evaluate(self, result: dict, result_id: int):
        self._history.append(result)
        history = list(self._history)

        for strategy_name, open_sig in list(self._open_signals.items()):
            entry = open_sig["entry"]
            sig_id = open_sig["signal_id"]
            gale = open_sig["gale"]

            cls = STRATEGY_CLASSES.get(strategy_name)
            if not cls:
                continue

            strategy = cls(config=open_sig.get("config", {}))
            status = strategy.resolve(result, entry)

            if status == "pending":
                continue

            if status == "loss" and gale < open_sig.get("max_gale", 2):
                new_gale = gale + 1
                await update_signal_status(sig_id, "loss")
                new_id = await dispatch_signal("dadinho", result["table_id"], strategy_name, entry, new_gale, result_id)
                self._open_signals[strategy_name] = {**open_sig, "gale": new_gale, "signal_id": new_id}
                logger.info(f"[Dadinho/{strategy_name}] GALE {new_gale}: {entry}")
            else:
                await update_signal_status(sig_id, status)
                del self._open_signals[strategy_name]
                logger.info(f"[Dadinho/{strategy_name}] Resolvido: {status.upper()}")

        strategies = await self._load_strategies()
        for strategy in strategies:
            if strategy.name in self._open_signals:
                continue

            strategy._history = deque(history, maxlen=100)
            should, entry = strategy.should_enter(history)

            if should:
                sig_id = await dispatch_signal(
                    "dadinho", result["table_id"], strategy.name, entry, 0, result_id
                )
                self._open_signals[strategy.name] = {
                    "signal_id": sig_id,
                    "entry": entry,
                    "gale": 0,
                    "max_gale": strategy.max_gale,
                    "config": strategy.config,
                }
                logger.info(f"[Dadinho/{strategy.name}] ENTRADA: {entry}")
