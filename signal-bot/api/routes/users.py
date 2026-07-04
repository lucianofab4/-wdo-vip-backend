import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

from api.dependencies import get_db
from database.models import TelegramUser, AccessRequest, InviteCode

router = APIRouter(prefix="/users", tags=["Usuarios"])

BOT_TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "Quantico20k_bot").strip().lstrip("@")

PLAN_DURATION = {"6months": 180, "lifetime": None, "dolar_mensal": 30, "dolar_semestral": 180, "dolar_teste": 1}


class UserOut(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    is_active: bool
    is_admin: bool
    plan: str
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AccessRequestOut(BaseModel):
    id: int
    telegram_id: Optional[int]
    username: Optional[str]
    first_name: Optional[str]
    buyer_name: Optional[str]
    plan: Optional[str]
    amount: Optional[float]
    status: str
    payment_status: str
    requested_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class UsersStats(BaseModel):
    total_active: int
    total_all: int
    pending_requests: int
    expired_count: int
    total_revenue: float
    users: list[UserOut]


class UserCreate(BaseModel):
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    plan: str = "free"


async def _notify_telegram(chat_id: int, text: str):
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        except Exception:
            pass


async def _expire_users(db: AsyncSession):
    """Desativa automaticamente usuários com plano expirado."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(TelegramUser).where(
            TelegramUser.is_active == True,
            TelegramUser.expires_at != None,
            TelegramUser.expires_at < now,
        )
    )
    expired = result.scalars().all()
    for u in expired:
        u.is_active = False
    if expired:
        await db.commit()
    return len(expired)


PLAN_DAYS = {
    "free": None, "mensal": 30, "semestral": 180,
    "dolar_mensal": 30, "dolar_semestral": 180,
    "6months": 180, "lifetime": None, "dolar_teste": 1,
}


@router.post("/", response_model=UserOut)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Adiciona um usuario manualmente sem precisar de pagamento."""
    if not data.telegram_id and not data.username:
        raise HTTPException(status_code=400, detail="Informe telegram_id ou username")

    # Se so username foi informado, gera ID temporario negativo unico
    import random as _rnd
    tg_id = data.telegram_id or -_rnd.randint(10**9, 10**12)

    # Busca por telegram_id ou por username se ja existe
    user = None
    if data.telegram_id:
        r = await db.execute(select(TelegramUser).where(TelegramUser.telegram_id == data.telegram_id))
        user = r.scalar_one_or_none()
    if not user and data.username:
        uname = data.username.lstrip("@")
        r = await db.execute(select(TelegramUser).where(TelegramUser.username == uname))
        user = r.scalar_one_or_none()

    days = PLAN_DAYS.get(data.plan)
    expires_at = datetime.now(timezone.utc) + timedelta(days=days) if days else None

    if user:
        user.is_active  = True
        user.plan       = data.plan
        user.expires_at = expires_at
        if data.telegram_id:
            user.telegram_id = data.telegram_id
        if data.username:
            user.username = data.username.lstrip("@")
        if data.first_name:
            user.first_name = data.first_name
    else:
        user = TelegramUser(
            telegram_id = tg_id,
            username    = data.username.lstrip("@") if data.username else None,
            first_name  = data.first_name or (data.username or "Manual"),
            is_active   = True,
            is_admin    = False,
            plan        = data.plan,
            expires_at  = expires_at,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    plan_labels = {
        "free": "Free", "mensal": "Mensal (30d)", "semestral": "Semestral (180d)",
        "dolar_mensal": "Dolar Mensal", "dolar_semestral": "Dolar Semestral",
        "6months": "6 Meses", "lifetime": "Vitalicio",
    }
    if data.telegram_id:
        await _notify_telegram(
            data.telegram_id,
            f"✅ <b>Seu acesso foi ativado!</b>\n\nPlano: {plan_labels.get(data.plan, data.plan)}\nBem-vindo aos sinais WDO!"
        )
    return user


@router.get("/", response_model=UsersStats)
async def get_users(db: AsyncSession = Depends(get_db)):
    expired_count = await _expire_users(db)

    total_all = await db.scalar(select(func.count(TelegramUser.id))) or 0
    total_active = await db.scalar(
        select(func.count(TelegramUser.id)).where(TelegramUser.is_active == True)
    ) or 0
    pending_requests = await db.scalar(
        select(func.count(AccessRequest.id)).where(AccessRequest.status == "pending")
    ) or 0
    total_revenue = float(await db.scalar(
        select(func.coalesce(func.sum(AccessRequest.amount), 0))
        .where(AccessRequest.payment_status == "paid")
    ) or 0)
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.is_active == True)
        .order_by(TelegramUser.created_at.desc())
    )
    users = result.scalars().all()
    return UsersStats(
        total_active=total_active,
        total_all=total_all,
        pending_requests=pending_requests,
        expired_count=expired_count,
        total_revenue=total_revenue,
        users=users,
    )


@router.get("/requests", response_model=list[AccessRequestOut])
async def get_requests(status: str = "pending", db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AccessRequest).where(AccessRequest.status == status)
        .order_by(AccessRequest.requested_at.desc())
    )
    return result.scalars().all()


@router.post("/requests/{request_id}/approve")
async def approve_request(request_id: int, db: AsyncSession = Depends(get_db)):
    req = await db.get(AccessRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")
    if req.status not in ("pending", "paid"):
        raise HTTPException(status_code=400, detail="Solicitacao nao esta pendente")

    code = InviteCode.generate()
    invite = InviteCode(code=code, created_by=0, target_telegram_id=req.telegram_id)
    db.add(invite)

    req.status = "approved"
    req.resolved_at = datetime.now(timezone.utc)

    # Se o usuário já existe no bot, aplica plano e expiração imediatamente
    if req.telegram_id and req.plan:
        user_result = await db.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == req.telegram_id)
        )
        existing_user = user_result.scalar_one_or_none()
        if existing_user:
            existing_user.plan = req.plan
            existing_user.is_active = True
            days = PLAN_DURATION.get(req.plan)
            if days is not None:
                now = datetime.now(timezone.utc)
                existing_user.expires_at = now + timedelta(days=days)
            else:
                existing_user.expires_at = None

    await db.commit()

    link = f"https://t.me/{BOT_USERNAME}?start={code}"
    plan_labels = {"lifetime": "Vitalicio", "6months": "6 Meses", "dolar_mensal": "Dolar Mensal", "dolar_semestral": "Dolar Semestral", "dolar_teste": "Dolar Teste"}
    plan_label = plan_labels.get(req.plan or "", "Acesso")
    msg = (
        f"<b>✅ Acesso Aprovado! — {plan_label}</b>\n\n"
        f"Clique no link abaixo para entrar no bot:\n{link}\n\n"
        f"<i>Este link e exclusivo para voce e so pode ser usado uma vez.</i>"
    )
    if req.telegram_id:
        await _notify_telegram(req.telegram_id, msg)

    return {"ok": True, "link": link}


@router.post("/requests/{request_id}/reject")
async def reject_request(request_id: int, db: AsyncSession = Depends(get_db)):
    req = await db.get(AccessRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")

    req.status = "rejected"
    req.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    if req.telegram_id:
        await _notify_telegram(
            req.telegram_id,
            "*Solicitacao recusada.*\n\nSeu acesso nao foi aprovado pelo administrador."
        )
    return {"ok": True}


@router.post("/{telegram_id}/renew")
async def renew_user(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """Renova o plano de 6 meses por mais 180 dias."""
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    now = datetime.now(timezone.utc)
    base = user.expires_at if (user.expires_at and user.expires_at > now) else now
    user.expires_at = base + timedelta(days=180)
    user.is_active = True
    user.plan = "6months"
    await db.commit()

    await _notify_telegram(
        telegram_id,
        "*Seu plano foi renovado!*\n\nVoce tem mais 6 meses de acesso aos sinais."
    )
    return {"ok": True, "expires_at": user.expires_at.isoformat()}


@router.delete("/{telegram_id}")
async def remove_user(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    user.is_active = False
    await db.commit()

    await _notify_telegram(
        telegram_id,
        "*Seu acesso foi removido pelo administrador.*"
    )
    return {"ok": True}
