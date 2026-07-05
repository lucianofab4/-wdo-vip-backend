from loguru import logger
from database.connection import AsyncSessionFactory
from database.models import GameResult
from strategy_engine.crash.engine import CrashEngine


class CrashStrategyFeed:
    def __init__(self):
        self.engine = CrashEngine()

    async def process(self, result: dict):
        async with AsyncSessionFactory() as session:
            record = GameResult(
                game="crash",
                table_id=result["table_id"],
                result={
                    "multiplier": result["multiplier"],
                    "round_id": result.get("round_id"),
                },
                raw_data=result.get("raw"),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)

        await self.engine.evaluate(result, record.id)
