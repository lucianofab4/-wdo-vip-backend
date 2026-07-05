from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.schemas import StatsOut
from database.models import Signal

router = APIRouter(prefix="/stats", tags=["Estatísticas"])

GAMES = ["bacbo", "dadinho", "crash"]


@router.get("/", response_model=list[StatsOut])
async def get_stats(db: AsyncSession = Depends(get_db)):
    stats = []
    for game in GAMES:
        wins = await db.scalar(
            select(func.count(Signal.id)).where(Signal.game == game, Signal.status == "win")
        ) or 0
        losses = await db.scalar(
            select(func.count(Signal.id)).where(Signal.game == game, Signal.status == "loss")
        ) or 0
        pending = await db.scalar(
            select(func.count(Signal.id)).where(Signal.game == game, Signal.status == "pending")
        ) or 0
        wins_direct = await db.scalar(
            select(func.count(Signal.id)).where(
                Signal.game == game, Signal.status == "win", Signal.gale_level == 0
            )
        ) or 0
        wins_gale1 = await db.scalar(
            select(func.count(Signal.id)).where(
                Signal.game == game, Signal.status == "win", Signal.gale_level == 1
            )
        ) or 0
        wins_gale2 = await db.scalar(
            select(func.count(Signal.id)).where(
                Signal.game == game, Signal.status == "win", Signal.gale_level == 2
            )
        ) or 0
        total = wins + losses
        rate = round(wins / total * 100, 2) if total > 0 else 0.0
        stats.append(StatsOut(
            game=game,
            total=total,
            wins=wins,
            losses=losses,
            pending=pending,
            win_rate=rate,
            wins_direct=wins_direct,
            wins_gale1=wins_gale1,
            wins_gale2=wins_gale2,
        ))
    return stats
