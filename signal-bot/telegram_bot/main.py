import asyncio
import os
from loguru import logger
from dotenv import load_dotenv

load_dotenv(dotenv_path="C:/Users/Game-PC/signal-bot/.env", override=True)

from telegram_bot.bot import bot, dp, poll_signals

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
PORT = int(os.getenv("PORT", "8080"))


async def _run_webhook():
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    webhook_url = f"https://{WEBHOOK_HOST}/webhook"
    logger.info(f"[Bot] Modo webhook: {webhook_url}")

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)

    app = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"[Bot] Webhook ativo na porta {PORT}")

    await poll_signals()


async def main():
    logger.info("Telegram Bot iniciando...")

    if WEBHOOK_HOST:
        await _run_webhook()
    else:
        logger.info("[Bot] Modo polling (local)...")
        await asyncio.gather(
            dp.start_polling(bot, skip_updates=True),
            poll_signals(),
        )


if __name__ == "__main__":
    asyncio.run(main())
