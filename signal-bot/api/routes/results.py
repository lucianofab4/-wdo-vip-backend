from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.schemas import GameResultOut
from database.models import GameResult

router = APIRouter(prefix="/results", tags=["Resultados"])


@router.get("/", response_model=list[GameResultOut])
async def list_results(
    game: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    query = select(GameResult).order_by(desc(GameResult.created_at)).limit(limit).offset(offset)
    if game:
        query = query.where(GameResult.game == game)
    result = await db.execute(query)
    return result.scalars().all()
