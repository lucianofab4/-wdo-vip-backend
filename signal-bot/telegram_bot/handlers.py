import os
from datetime import datetime, timezone, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from loguru import logger

from database.connection import AsyncSessionFactory
from database.models import TelegramUser, InviteCode, AccessRequest
from telegram_bot.messages import WELCOME_MESSAGE

router = Router()
ADMIN_IDS = [int(x) for x in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if x.strip()]
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "Quantico20k_bot").strip()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

_btn_solicitar = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="Solicitar Acesso", callback_data="request_access")
]])


async def _notify_admins(text: str, bot=None):
    """Notifica todos os admins no Telegram."""
    import httpx
    if not BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        for admin_id in ADMIN_IDS:
            try:
                await client.post(url, json={"chat_id": admin_id, "text": text, "parse_mode": "Markdown"})
            except Exception:
                pass


async def _get_user(telegram_id: int) -> TelegramUser | None:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


PLAN_DURATION = {"6months": 180, "lifetime": None, "dolar_mensal": 30, "dolar_semestral": 180, "dolar_teste": 1}


async def _create_user(
    telegram_id: int, username: str, first_name: str, is_admin: bool,
    plan: str = "free", expires_at=None,
) -> TelegramUser:
    async with AsyncSessionFactory() as session:
        user = TelegramUser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            is_active=True,
            is_admin=is_admin,
            plan=plan,
            expires_at=expires_at,
        )
        session.add(user)
        await session.commit()
    return user


@router.message(Command("start"))
async def cmd_start(message: Message):
    telegram_id = message.from_user.id
    is_admin = telegram_id in ADMIN_IDS

    args = message.text.split(maxsplit=1)
    code = args[1].strip() if len(args) > 1 else ""

    user = await _get_user(telegram_id)

    if is_admin:
        if not user:
            await _create_user(telegram_id, message.from_user.username, message.from_user.first_name, True)
        else:
            async with AsyncSessionFactory() as session:
                u = await session.get(TelegramUser, user.id)
                u.is_active = True
                await session.commit()
        await message.answer(WELCOME_MESSAGE, parse_mode="Markdown")
        return

    if user:
        async with AsyncSessionFactory() as session:
            u = await session.get(TelegramUser, user.id)
            u.is_active = True
            await session.commit()
        await message.answer(WELCOME_MESSAGE, parse_mode="Markdown")
        return

    # Novo usuário com código de convite
    if code:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(InviteCode).where(
                    InviteCode.code == code,
                    InviteCode.is_active == True,
                    InviteCode.used_by == None,
                )
            )
            invite = result.scalar_one_or_none()

            if not invite:
                await message.answer(
                    "*Codigo invalido ou ja utilizado.*\n\n"
                    "Solicite acesso ao administrador.",
                    parse_mode="Markdown",
                )
                return

            # Verifica se o convite é exclusivo para outro usuário
            if invite.target_telegram_id and invite.target_telegram_id != telegram_id:
                await message.answer(
                    "*Este convite nao e para voce.*\n\n"
                    "Solicite seu proprio acesso ao administrador.",
                    parse_mode="Markdown",
                )
                return

            invite.used_by = telegram_id
            invite.used_at = datetime.now(timezone.utc)
            invite.is_active = False

            # Marca solicitação como aprovada se existir e coleta dados do plano
            req_result = await session.execute(
                select(AccessRequest).where(AccessRequest.telegram_id == telegram_id)
            )
            req = req_result.scalar_one_or_none()
            invite_plan = "free"
            invite_expires = None
            if req:
                req.status = "approved"
                req.resolved_at = datetime.now(timezone.utc)
                if req.plan:
                    invite_plan = req.plan
                    days = PLAN_DURATION.get(req.plan)
                    if days is not None:
                        invite_expires = datetime.now(timezone.utc).replace(tzinfo=timezone.utc) + timedelta(days=days)

            await session.commit()

        await _create_user(
            telegram_id, message.from_user.username, message.from_user.first_name, False,
            plan=invite_plan, expires_at=invite_expires,
        )
        logger.info(f"Novo usuario registrado via convite: {telegram_id} (@{message.from_user.username})")
        await message.answer(WELCOME_MESSAGE, parse_mode="Markdown")
        return

    # Verifica se já pagou pelo @username (compra via landing page)
    tg_username = (message.from_user.username or "").lower().strip()
    if tg_username:
        async with AsyncSessionFactory() as session:
            paid_result = await session.execute(
                select(AccessRequest).where(
                    AccessRequest.username == tg_username,
                    AccessRequest.payment_status == "paid",
                    AccessRequest.status.in_(["pending", "approved"]),
                    AccessRequest.telegram_id == None,
                )
            )
            paid_req = paid_result.scalar_one_or_none()
            if paid_req:
                # Vincula o telegram_id à solicitação e ativa imediatamente
                paid_req.telegram_id = telegram_id
                paid_req.first_name = message.from_user.first_name
                paid_req.status = "approved"
                paid_req.resolved_at = paid_req.resolved_at or datetime.now(timezone.utc)

                code = InviteCode.generate()
                invite = InviteCode(
                    code=code,
                    created_by=0,
                    target_telegram_id=telegram_id,
                    used_by=telegram_id,
                    used_at=datetime.now(timezone.utc),
                    is_active=False,
                )
                session.add(invite)
                await session.commit()

                paid_plan = paid_req.plan or "free"
                paid_days = PLAN_DURATION.get(paid_plan)
                paid_expires = (datetime.now(timezone.utc) + timedelta(days=paid_days)) if paid_days else None
                await _create_user(
                    telegram_id, message.from_user.username, message.from_user.first_name, False,
                    plan=paid_plan, expires_at=paid_expires,
                )
                logger.info(f"Usuario ativado automaticamente via pagamento: {telegram_id} (@{tg_username})")
                await message.answer(WELCOME_MESSAGE, parse_mode="Markdown")
                return

    # Sem código e sem pagamento — mostra botão de solicitação
    await message.answer(
        "*Bot Privado*\n\n"
        "Este bot e exclusivo para membros autorizados.\n"
        "Clique abaixo para solicitar acesso ao administrador.",
        parse_mode="Markdown",
        reply_markup=_btn_solicitar,
    )


@router.callback_query(F.data == "request_access")
async def cb_request_access(callback: CallbackQuery):
    telegram_id = callback.from_user.id

    if telegram_id in ADMIN_IDS:
        await callback.answer("Voce ja e admin.", show_alert=False)
        return

    user = await _get_user(telegram_id)
    if user:
        await callback.answer("Voce ja tem acesso! Use /start.", show_alert=True)
        return

    async with AsyncSessionFactory() as session:
        existing = await session.execute(
            select(AccessRequest).where(AccessRequest.telegram_id == telegram_id)
        )
        req = existing.scalar_one_or_none()

        if req:
            if req.status == "pending":
                await callback.answer("Sua solicitacao ja esta em analise. Aguarde.", show_alert=True)
                return
            elif req.status == "rejected":
                req.status = "pending"
                req.requested_at = datetime.now(timezone.utc)
                req.resolved_at = None
                await session.commit()
            elif req.status == "approved":
                # Busca o código de convite não utilizado para reenviar
                invite_result = await session.execute(
                    select(InviteCode).where(
                        InviteCode.target_telegram_id == telegram_id,
                        InviteCode.is_active == True,
                        InviteCode.used_by == None,
                    )
                )
                invite = invite_result.scalar_one_or_none()
                if invite:
                    link = f"https://t.me/{BOT_USERNAME}?start={invite.code}"
                    await callback.answer("Reenviando seu link de acesso...", show_alert=False)
                    await callback.message.answer(
                        f"✅ <b>Seu acesso já foi aprovado!</b>\n\n"
                        f"Clique no link abaixo para entrar:\n{link}\n\n"
                        f"<i>Este link é exclusivo para você.</i>",
                        parse_mode="HTML",
                    )
                else:
                    await callback.answer("Acesso ja aprovado. Use /start para entrar.", show_alert=True)
                return
        else:
            new_req = AccessRequest(
                telegram_id=telegram_id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                status="pending",
            )
            session.add(new_req)
            await session.commit()

    logger.info(f"Solicitacao de acesso: {telegram_id} (@{callback.from_user.username})")

    name = callback.from_user.first_name or callback.from_user.username or str(telegram_id)
    username_str = f"@{callback.from_user.username}" if callback.from_user.username else "sem username"
    await _notify_admins(
        f"*Nova solicitacao de acesso!*\n\n"
        f"Nome: {name}\n"
        f"Telegram: {username_str}\n"
        f"ID: `{telegram_id}`\n\n"
        f"Acesse o painel para aprovar ou recusar."
    )

    await callback.message.edit_text(
        "*Solicitacao enviada!*\n\n"
        "O administrador vai analisar seu pedido.\n"
        "Voce recebera o link de acesso aqui quando aprovado.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(Command("stop"))
async def cmd_stop(message: Message):
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.is_active = False
            await session.commit()
    await message.answer("Sinais pausados. Use /start para reativar.", parse_mode="Markdown")


@router.message(Command("status"))
async def cmd_status(message: Message):
    await message.answer(
        "*Sistema Online*\n"
        "Bac Bo (Betou): Monitorando",
        parse_mode="Markdown",
    )


# ─── Comandos Admin ───────────────────────────────────────────────────────────

@router.message(Command("gencode"))
async def cmd_gencode(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    args = message.text.split(maxsplit=1)
    try:
        quantidade = int(args[1]) if len(args) > 1 else 1
        quantidade = min(quantidade, 20)
    except ValueError:
        quantidade = 1

    codes = []
    async with AsyncSessionFactory() as session:
        for _ in range(quantidade):
            code = InviteCode.generate()
            invite = InviteCode(code=code, created_by=message.from_user.id)
            session.add(invite)
            codes.append(code)
        await session.commit()

    lines = [f"*{quantidade} codigo(s) gerado(s):*\n"]
    for code in codes:
        link = f"https://t.me/{BOT_USERNAME}?start={code}"
        lines.append(f"`{code}`\n{link}\n")

    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("revoke"))
async def cmd_revoke(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Uso: /revoke <telegram_id>")
        return

    try:
        target_id = int(args[1].strip())
    except ValueError:
        await message.answer("ID invalido.")
        return

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == target_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("Usuario nao encontrado.")
            return
        user.is_active = False
        await session.commit()

    await message.answer(f"Usuario `{target_id}` removido do bot.", parse_mode="Markdown")


@router.message(Command("users"))
async def cmd_users(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(TelegramUser).where(TelegramUser.is_active == True)
        )
        users = result.scalars().all()

    if not users:
        await message.answer("Nenhum usuario ativo.")
        return

    lines = [f"*{len(users)} usuario(s) ativo(s):*\n"]
    for u in users:
        name = f"@{u.username}" if u.username else u.first_name or "?"
        lines.append(f"- {name} (`{u.telegram_id}`)")

    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message()
async def cmd_unknown(message: Message):
    """Responde qualquer mensagem que não seja um comando reconhecido."""
    user = await _get_user(message.from_user.id)
    if user and user.is_active:
        await message.answer(
            "Este bot envia sinais automaticamente.\n\n"
            "Comandos disponíveis:\n"
            "/stop — Pausar sinais\n"
            "/start — Reativar sinais",
            parse_mode="Markdown",
        )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("Uso: /broadcast <mensagem>")
        return

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(TelegramUser).where(TelegramUser.is_active == True)
        )
        users = result.scalars().all()

    bot = message.bot
    count = 0
    for user in users:
        try:
            await bot.send_message(user.telegram_id, f"{text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass

    await message.answer(f"Mensagem enviada para {count} usuarios.")
