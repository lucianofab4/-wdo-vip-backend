import os
import uuid
import mercadopago
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import httpx
from loguru import logger

from api.dependencies import get_db
from database.models import AccessRequest, TelegramUser, InviteCode

router = APIRouter(prefix="/payments", tags=["Pagamentos"])

MP_TOKEN      = os.getenv("MP_ACCESS_TOKEN", "")
BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_USERNAME  = os.getenv("TELEGRAM_BOT_USERNAME", "Quantico20k_bot").strip().lstrip("@")
ADMIN_IDS     = [int(x) for x in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if x.strip()]
API_BASE_URL  = os.getenv("RAILWAY_API_URL", "http://localhost:8000")

# Canal VIP — bot Wdotrader_bot precisa ser admin com permissao de convidar
VIP_BOT_TOKEN  = os.getenv("VIP_BOT_TOKEN",  "8992965841:AAGOg60JQ5ysTi9nyNcnm-B8COFuuhlJScM")
VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID", "-1004459210142")

PLANS = {
    "6months":        {"label": "6 Meses",          "amount": 80.00},
    "lifetime":       {"label": "Vitalicio",         "amount": 99.00},
    "dolar_mensal":   {"label": "Dolar Mensal",      "amount": 200.00},
    "dolar_semestral":{"label": "Dolar Semestral",   "amount": 999.00},
    "dolar_teste":    {"label": "Dolar Teste R$1",   "amount": 1.00},
}


class CreatePaymentRequest(BaseModel):
    plan: str           # 6months | lifetime
    buyer_name: str
    telegram_username: str  # @username sem o @


class CreatePaymentResponse(BaseModel):
    payment_id: str
    qr_code: str
    qr_code_base64: str
    pix_copy_paste: str
    amount: float
    plan_label: str
    expires_in_minutes: int = 30


async def _notify_telegram(chat_id: int, text: str):
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        except Exception:
            pass


async def _gerar_link_canal(expire_horas: int = 48) -> str:
    """Gera link de convite único (1 uso) para o canal VIP."""
    import time as _t
    expire_ts = int(_t.time()) + expire_horas * 3600
    url = f"https://api.telegram.org/bot{VIP_BOT_TOKEN}/createChatInviteLink"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json={
            "chat_id":      VIP_CHANNEL_ID,
            "member_limit": 1,
            "expire_date":  expire_ts,
        })
        data = r.json()
    if data.get("ok"):
        return data["result"]["invite_link"]
    logger.error(f"[Canal] Falha ao gerar invite link: {data}")
    return ""


async def _remover_do_canal(telegram_id: int):
    """Remove (bane + desbane) um usuário do canal VIP."""
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            f"https://api.telegram.org/bot{VIP_BOT_TOKEN}/banChatMember",
            json={"chat_id": VIP_CHANNEL_ID, "user_id": telegram_id, "revoke_messages": False},
        )
        await client.post(
            f"https://api.telegram.org/bot{VIP_BOT_TOKEN}/unbanChatMember",
            json={"chat_id": VIP_CHANNEL_ID, "user_id": telegram_id},
        )


@router.post("/create", response_model=CreatePaymentResponse)
async def create_payment(body: CreatePaymentRequest, db: AsyncSession = Depends(get_db)):
    if body.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plano invalido")

    if not MP_TOKEN:
        raise HTTPException(status_code=503, detail="Pagamentos nao configurados")

    plan = PLANS[body.plan]
    username = body.telegram_username.lstrip("@").strip()

    sdk = mercadopago.SDK(MP_TOKEN)

    safe_name = body.buyer_name.lower().replace(" ", "").replace(".", "")[:20] or "usuario"
    payment_data = {
        "transaction_amount": float(plan["amount"]),
        "description": f"Signal Bot {plan['label']}",
        "payment_method_id": "pix",
        "payer": {
            "email": f"{safe_name}.{username}@gmail.com",
            "first_name": body.buyer_name.split()[0] if body.buyer_name else username,
            "last_name": " ".join(body.buyer_name.split()[1:]) or "Usuario",
        },
        "external_reference": f"{username}|{body.plan}",
        "notification_url": f"{API_BASE_URL}/payments/webhook",
    }

    response = sdk.payment().create(payment_data)
    result = response.get("response", {})

    if response.get("status") not in (200, 201):
        logger.error(f"[MP] Falha ao criar pagamento. HTTP status={response.get('status')} | body={result}")
        raise HTTPException(status_code=502, detail=f"Erro MP: {result.get('message', result)}")

    mp_id = str(result["id"])
    pix_data = result.get("point_of_interaction", {}).get("transaction_data", {})

    # Salva solicitação como pagamento pendente
    existing = await db.execute(
        select(AccessRequest).where(AccessRequest.username == username)
    )
    req = existing.scalar_one_or_none()

    if req:
        req.payment_id     = mp_id
        req.plan           = body.plan
        req.amount         = plan["amount"]
        req.buyer_name     = body.buyer_name
        req.payment_status = "pending"
        req.status         = "awaiting_payment"
    else:
        req = AccessRequest(
            username=username,
            buyer_name=body.buyer_name,
            plan=body.plan,
            amount=plan["amount"],
            payment_id=mp_id,
            payment_status="pending",
            status="awaiting_payment",
        )
        db.add(req)

    await db.commit()

    return CreatePaymentResponse(
        payment_id=mp_id,
        qr_code=pix_data.get("qr_code", ""),
        qr_code_base64=pix_data.get("qr_code_base64", ""),
        pix_copy_paste=pix_data.get("qr_code", ""),
        amount=plan["amount"],
        plan_label=plan["label"],
    )


@router.post("/webhook")
async def mercadopago_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Recebe notificações do Mercado Pago."""
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}

    # MP envia notificação de pagamento aprovado
    if body.get("type") != "payment":
        return {"ok": True}

    payment_id = str(body.get("data", {}).get("id", ""))
    if not payment_id:
        return {"ok": True}

    # Consulta o pagamento no MP para confirmar
    sdk = mercadopago.SDK(MP_TOKEN)
    response = sdk.payment().get(payment_id)
    payment = response.get("response", {})

    if payment.get("status") != "approved":
        return {"ok": True}

    external_ref = payment.get("external_reference", "")
    parts = external_ref.split("|")
    if len(parts) < 2:
        return {"ok": True}

    username, plan_key = parts[0], parts[1]
    plan = PLANS.get(plan_key, {})

    # Atualiza a solicitação
    result = await db.execute(
        select(AccessRequest).where(AccessRequest.payment_id == payment_id)
    )
    req = result.scalar_one_or_none()

    if not req:
        result2 = await db.execute(
            select(AccessRequest).where(AccessRequest.username == username)
        )
        req = result2.scalar_one_or_none()

    # Gera link do canal automaticamente
    invite_link = await _gerar_link_canal(expire_horas=48)

    # Calcula vencimento do plano
    from datetime import timedelta
    plan_days = {"dolar_mensal": 30, "dolar_semestral": 180, "6months": 180, "lifetime": None, "dolar_teste": 1}
    days = plan_days.get(plan_key)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=days) if days else None

    # Atualiza AccessRequest
    if req:
        req.payment_status      = "paid"
        req.status              = "approved"
        req.payment_id          = payment_id
        req.channel_invite_link = invite_link
        req.resolved_at         = now
    await db.commit()

    # Cria ou atualiza TelegramUser
    user_result = await db.execute(
        select(TelegramUser).where(TelegramUser.username == username)
    )
    user = user_result.scalar_one_or_none()
    if user:
        user.is_active  = True
        user.plan       = plan_key
        user.expires_at = expires_at
    else:
        import random as _rnd
        user = TelegramUser(
            telegram_id = -_rnd.randint(10**9, 10**12),
            username    = username,
            first_name  = payment.get("payer", {}).get("first_name", username),
            is_active   = True,
            plan        = plan_key,
            expires_at  = expires_at,
        )
        db.add(user)
    await db.commit()

    # Notifica admins
    msg_admin = (
        f"✅ *Pagamento aprovado automaticamente!*\n\n"
        f"Nome: {payment.get('payer', {}).get('first_name', '?')}\n"
        f"Telegram: @{username}\n"
        f"Plano: {plan.get('label', plan_key)}\n"
        f"Valor: R$ {payment.get('transaction_amount', 0):.2f}\n"
        f"Vence: {expires_at.strftime('%d/%m/%Y') if expires_at else 'Vitalício'}\n\n"
        f"Link enviado para o cliente via página de pagamento."
    )
    for admin_id in ADMIN_IDS:
        await _notify_telegram(admin_id, msg_admin)

    return {"ok": True}


@router.get("/status/{payment_id}")
async def payment_status(payment_id: str, db: AsyncSession = Depends(get_db)):
    """Polling do status do pagamento — usado pela landing page."""
    result = await db.execute(
        select(AccessRequest).where(AccessRequest.payment_id == payment_id)
    )
    req = result.scalar_one_or_none()
    if not req:
        return {"status": "not_found"}
    return {
        "status":       req.payment_status,
        "request_status": req.status,
        "invite_link":  req.channel_invite_link or "",
    }


@router.get("/expiring")
async def expiring_soon(days: int = 5, db: AsyncSession = Depends(get_db)):
    """Lista assinantes que vencem nos proximos N dias."""
    from datetime import timedelta
    now  = datetime.now(timezone.utc)
    lim  = now + timedelta(days=days)
    result = await db.execute(
        select(TelegramUser).where(
            TelegramUser.is_active == True,
            TelegramUser.expires_at != None,
            TelegramUser.expires_at >= now,
            TelegramUser.expires_at <= lim,
        ).order_by(TelegramUser.expires_at)
    )
    users = result.scalars().all()
    return [
        {
            "telegram_id": u.telegram_id,
            "username":    u.username,
            "first_name":  u.first_name,
            "plan":        u.plan,
            "expires_at":  u.expires_at.strftime("%d/%m/%Y %H:%M") if u.expires_at else None,
        }
        for u in users
    ]


@router.post("/process-expired")
async def process_expired(db: AsyncSession = Depends(get_db)):
    """Remove do canal e desativa usuários com plano vencido."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(TelegramUser).where(
            TelegramUser.is_active == True,
            TelegramUser.expires_at != None,
            TelegramUser.expires_at < now,
        )
    )
    expired = result.scalars().all()
    removidos = []
    for u in expired:
        if u.telegram_id and u.telegram_id > 0:
            await _remover_do_canal(u.telegram_id)
        u.is_active = False
        removidos.append(u.username or str(u.telegram_id))
    if expired:
        await db.commit()
    return {"removidos": removidos, "total": len(removidos)}
