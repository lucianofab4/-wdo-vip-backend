from datetime import datetime
from loguru import logger
from database.connection import AsyncSessionFactory
from database.models import Signal


async def dispatch_signal(game: str, table_id: str, strategy: str, entry: str,
                          gale_level: int = 0, result_id: int = None) -> int:
    async with AsyncSessionFactory() as session:
        signal = Signal(
            game=game,
            table_id=table_id,
            strategy=strategy,
            entry=entry,
            gale_level=gale_level,
            status="pending",
            result_id=result_id,
        )
        session.add(signal)
        await session.commit()
        await session.refresh(signal)
        logger.info(f"[Dispatcher] Sinal salvo: {game} | {entry} | gale={gale_level} | id={signal.id}")
        return signal.id


async def update_signal_status(signal_id: int, status: str):
    async with AsyncSessionFactory() as session:
        signal = await session.get(Signal, signal_id)
        if signal:
            signal.status = status
            signal.resolved_at = datetime.utcnow()
            await session.commit()
            logger.info(f"[Dispatcher] Sinal {signal_id} -> {status}")
