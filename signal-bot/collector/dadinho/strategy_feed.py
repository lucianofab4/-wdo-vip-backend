from loguru import logger
from database.connection import AsyncSessionFactory
from database.models import GameResult
from strategy_engine.dadinho.engine import DadinhoEngine


class DadinhoStrategyFeed:
    def __init__(self):
        self.engine = DadinhoEngine()

    async def process(self, result: dict):
        async with AsyncSessionFactory() as session:
            record = GameResult(
                game="dadinho",
                table_id=result["table_id"],
                result={
                    "die1": result["die1"],
                    "die2": result["die2"],
                    "total": result["total"],
                    "result_type": result["result_type"],
                    "is_double": result["is_double"],
                    "round_id": result.get("round_id"),
                },
                raw_data=result.get("raw"),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)

        await self.engine.evaluate(result, record.id)
