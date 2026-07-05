#!/bin/bash
set -e

echo "=== Signal Bot — Telegram Bot (Railway) ==="
echo "Iniciando Bot Telegram..."
exec python -m telegram_bot.main
