import asyncio
import os
from datetime import datetime
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select
from database.connection import AsyncSessionFactory
from database.models import TelegramUser, Signal
from telegram_bot.handlers import router

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()
dp.include_router(router)

GAME_EMOJI = {"bacbo": "🎴", "dadinho": "🎲", "crash": "🚀"}
ENTRY_COLOR = {
    "PLAYER": "AZUL (Player)",
    "BANKER": "VERMELHO (Banker)",
    "HIGH":   "ALTO",
    "LOW":    "BAIXO",
}

_last_checked_signal_id: int = 0


async def get_active_users() -> list[int]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(TelegramUser.telegram_id).where(TelegramUser.is_active == True)
        )
        return [row[0] for row in result.fetchall()]


async def broadcast(text: str):
    users = await get_active_users()
    for telegram_id in users:
        try:
            await bot.send_message(telegram_id, text)
        except Exception as e:
            logger.debug(f"Falha ao enviar para {telegram_id}: {e}")


async def poll_signals():
    """Monitora a tabela signals a cada 3s e envia mensagens para os usuários."""
    global _last_checked_signal_id
    logger.info("Bot: iniciando monitoramento de sinais no banco...")

    # Começa do último ID existente e marca todos os sinais atuais como já notificados
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Signal.id).order_by(Signal.id.desc()).limit(1))
        row = result.scalar_one_or_none()
        if row:
            _last_checked_signal_id = row

        # Marca todos os sinais já resolvidos como notificados para não reenviar no restart
        resolved = await session.execute(
            select(Signal.id).where(Signal.status.in_(["win", "loss", "cancelled"]))
        )
        for (sid,) in resolved.fetchall():
            _notified_results.add(sid)

    logger.info(f"Bot: monitorando a partir do sinal ID {_last_checked_signal_id}. {len(_notified_results)} sinais antigos ignorados.")

    while True:
        await asyncio.sleep(3)
        try:
            await _check_new_signals()
            await _check_resolved_signals()
        except Exception as e:
            logger.error(f"Erro no poll de sinais: {e}")


async def _check_new_signals():
    global _last_checked_signal_id
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Signal).where(
                Signal.id > _last_checked_signal_id,
                Signal.status == "pending",
            ).order_by(Signal.id)
        )
        signals = result.scalars().all()

    for signal in signals:
        _last_checked_signal_id = max(_last_checked_signal_id, signal.id)
        emoji = GAME_EMOJI.get(signal.game, "🎯")
        entry_label = ENTRY_COLOR.get(signal.entry, signal.entry)
        game_name = signal.game.upper()

        gale_text = f"\n🔁 *Gale {signal.gale_level}*" if signal.gale_level > 0 else ""

        msg = (
            f"{emoji} *ENTRADA CONFIRMADA*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🎮 Jogo: *{game_name}*\n"
            f"Entrar: *{entry_label}*\n"
            f"📊 Estratégia: `{signal.strategy}`"
            f"{gale_text}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ _Próxima rodada_"
        )
        await broadcast(msg)
        logger.info(f"Sinal enviado: {signal.game} | {signal.entry}")


_notified_results: set[int] = set()


async def _check_resolved_signals():
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Signal).where(
                Signal.status.in_(["win", "loss"]),
                Signal.resolved_at != None,
            ).order_by(Signal.resolved_at.desc()).limit(20)
        )
        signals = result.scalars().all()

    for signal in signals:
        if signal.id in _notified_results:
            continue

        # Só notifica loss definitivo (último gale) ou win
        if signal.status == "loss":
            # Verifica se tem sinal subsequente com gale (significa que ainda tem gale)
            async with AsyncSessionFactory() as session:
                next_gale = await session.execute(
                    select(Signal).where(
                        Signal.game == signal.game,
                        Signal.strategy == signal.strategy,
                        Signal.gale_level == signal.gale_level + 1,
                        Signal.id > signal.id,
                    ).limit(1)
                )
                if next_gale.scalar_one_or_none():
                    _notified_results.add(signal.id)
                    continue

        _notified_results.add(signal.id)
        entry_label = ENTRY_COLOR.get(signal.entry, signal.entry)

        if signal.status == "win":
            msg = (
                f"✅ *WIN!*\n"
                f"Entrada: *{entry_label}*"
                + (f" | Gale {signal.gale_level}" if signal.gale_level else "")
            )
        else:
            msg = (
                f"❌ *LOSS*\n"
                f"Entrada *{entry_label}* não confirmada."
            )
        await broadcast(msg)
