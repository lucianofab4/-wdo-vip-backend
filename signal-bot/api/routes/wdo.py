from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db
from database.models import FreeSubscriber, WdoSignal

router = APIRouter(prefix="/wdo", tags=["WDO"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class WdoSignalCreate(BaseModel):
    direction: str        # COMPRA | VENDA
    entry_price: Optional[float] = None
    signal_type: str      # REGIAO_SUPORTE | REGIAO_RESISTENCIA | MM6_PULLBACK | OPEN_DRIVE | GAP_FADE | TOPO_DIA | FUNDO_DIA
    signal_time: Optional[str] = None   # HH:MM


class WdoSignalResult(BaseModel):
    status: str           # win | loss | cancelled
    pts_result: Optional[float] = None


class WdoSignalOut(BaseModel):
    id: int
    direction: str
    entry_price: Optional[float]
    signal_type: str
    status: str
    pts_result: Optional[float]
    signal_time: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class WdoStatsOut(BaseModel):
    total: int
    wins: int
    losses: int
    pending: int
    cancelled: int
    win_rate: float


class FreeSubscriberIn(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    joined_at: Optional[datetime] = None


class FreeSubscriberOut(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    joined_at: Optional[datetime]
    synced_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── Endpoints — Sinais WDO ─────────────────────────────────────────────────────

@router.post("/signals", response_model=WdoSignalOut)
async def create_wdo_signal(data: WdoSignalCreate, db: AsyncSession = Depends(get_db)):
    """Monitor chama este endpoint quando um sinal é disparado."""
    sig = WdoSignal(
        direction=data.direction,
        entry_price=data.entry_price,
        signal_type=data.signal_type,
        signal_time=data.signal_time,
        status="pending",
    )
    db.add(sig)
    await db.commit()
    await db.refresh(sig)
    return sig


@router.patch("/signals/{signal_id}/result", response_model=WdoSignalOut)
async def update_wdo_signal(signal_id: int, data: WdoSignalResult, db: AsyncSession = Depends(get_db)):
    """Monitor chama este endpoint quando o sinal bate +6pts (win) ou -3pts (loss)."""
    sig = await db.get(WdoSignal, signal_id)
    if not sig:
        raise HTTPException(status_code=404, detail="Sinal nao encontrado")
    sig.status = data.status
    sig.pts_result = data.pts_result
    sig.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sig)
    return sig


@router.get("/signals", response_model=list[WdoSignalOut])
async def list_wdo_signals(
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    hour: Optional[str] = Query(None, description="HH (ex: 10)"),
    direction: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(WdoSignal).order_by(desc(WdoSignal.created_at)).limit(limit)
    if direction:
        q = q.where(WdoSignal.direction == direction)
    if status:
        q = q.where(WdoSignal.status == status)
    if date:
        from sqlalchemy import cast, Date
        q = q.where(func.date(WdoSignal.created_at) == date)
    if hour:
        q = q.where(WdoSignal.signal_time.startswith(hour + ":"))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats", response_model=WdoStatsOut)
async def wdo_stats(
    date: Optional[str] = Query(None, description="YYYY-MM-DD — default: hoje"),
    hour_from: Optional[str] = Query(None, description="HH inicio (ex: 09)"),
    hour_to: Optional[str] = Query(None, description="HH fim ex: 17)"),
    db: AsyncSession = Depends(get_db),
):
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    q = select(WdoSignal).where(func.date(WdoSignal.created_at) == date)
    if hour_from:
        q = q.where(WdoSignal.signal_time >= hour_from + ":00")
    if hour_to:
        q = q.where(WdoSignal.signal_time <= hour_to + ":59")

    result = await db.execute(q)
    sigs = result.scalars().all()

    total     = len(sigs)
    wins      = sum(1 for s in sigs if s.status == "win")
    losses    = sum(1 for s in sigs if s.status == "loss")
    pending   = sum(1 for s in sigs if s.status == "pending")
    cancelled = sum(1 for s in sigs if s.status == "cancelled")
    win_rate  = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0

    return WdoStatsOut(
        total=total, wins=wins, losses=losses,
        pending=pending, cancelled=cancelled, win_rate=win_rate,
    )


# ── Endpoints — Assinantes Free ────────────────────────────────────────────────

@router.get("/free-subscribers", response_model=list[FreeSubscriberOut])
async def list_free_subscribers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FreeSubscriber).order_by(FreeSubscriber.synced_at.desc())
    )
    return result.scalars().all()


@router.post("/free-subscribers/sync")
async def sync_free_subscribers(
    subscribers: list[FreeSubscriberIn],
    db: AsyncSession = Depends(get_db),
):
    """Monitor sincroniza periodicamente a lista de assinantes free."""
    upserted = 0
    for sub in subscribers:
        result = await db.execute(
            select(FreeSubscriber).where(FreeSubscriber.telegram_id == sub.telegram_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.username   = sub.username
            existing.first_name = sub.first_name
            if sub.joined_at:
                existing.joined_at = sub.joined_at
        else:
            db.add(FreeSubscriber(
                telegram_id=sub.telegram_id,
                username=sub.username,
                first_name=sub.first_name,
                joined_at=sub.joined_at,
            ))
        upserted += 1
    await db.commit()
    return {"ok": True, "upserted": upserted}
