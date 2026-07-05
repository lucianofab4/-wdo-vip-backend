from loguru import logger
from database.connection import AsyncSessionFactory
from database.models import GameResult
from strategy_engine.bacbo.engine import BacBoEngine


class BacBoStrategyFeed:
    def __init__(self):
        self.engine = BacBoEngine()

    async def process(self, result: dict):
        await self.engine.warm_up()
        async with AsyncSessionFactory() as session:
            record = GameResult(
                game="bacbo",
                table_id=result["table_id"],
                result={
                    "outcome": result["result"],
                    "player_dice": result.get("player_dice"),
                    "banker_dice": result.get("banker_dice"),
                    "round_id": result.get("round_id"),
                },
                raw_data=result.get("raw"),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.debug(f"[BacBo] Resultado salvo: id={record.id}")

        await self.engine.evaluate(result, record.id)
