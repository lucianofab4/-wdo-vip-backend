from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from api.schemas import SignalOut
from database.models import Signal

router = APIRouter(prefix="/signals", tags=["Sinais"])


@router.get("/", response_model=list[SignalOut])
async def list_signals(
    game: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Signal).order_by(desc(Signal.created_at)).limit(limit).offset(offset)
    if game:
        query = query.where(Signal.game == game)
    if status:
        query = query.where(Signal.status == status)
    result = await db.execute(query)
    return result.scalars().all()
