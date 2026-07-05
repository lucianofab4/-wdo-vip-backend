GAME_EMOJI = {
    "bacbo": "🎴",
    "dadinho": "🎲",
    "crash": "🚀",
}

GAME_NAME = {
    "bacbo": "Bac Bo",
    "dadinho": "Dadinho",
    "crash": "Crash",
}

ENTRY_EMOJI = {
    "PLAYER": "🔵",
    "BANKER": "🔴",
    "HIGH": "⬆️",
    "LOW": "⬇️",
}


def signal_message(game: str, table_id: str, entry: str, gale_level: int, strategy: str) -> str:
    emoji = GAME_EMOJI.get(game, "🎯")
    name = GAME_NAME.get(game, game.upper())
    entry_emoji = ENTRY_EMOJI.get(entry.split("x")[0].upper(), "🎯")

    gale_text = ""
    if gale_level > 0:
        gale_text = f"\n🔁 *Gale {gale_level}*"

    return (
        f"{emoji} *ENTRADA CONFIRMADA*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 Jogo: *{name}*\n"
        f"🏓 Mesa: `{table_id}`\n"
        f"{entry_emoji} Entrar em: *{entry}*\n"
        f"📊 Estratégia: `{strategy}`"
        f"{gale_text}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ _Próxima rodada_"
    )


def result_win_message(game: str, entry: str, gale_level: int) -> str:
    emoji = GAME_EMOJI.get(game, "🎯")
    return (
        f"✅ *WIN* {emoji}\n"
        f"Entrada: *{entry}*"
        + (f" | Gale {gale_level}" if gale_level > 0 else "")
    )


def result_loss_message(game: str, entry: str) -> str:
    emoji = GAME_EMOJI.get(game, "🎯")
    return f"❌ *LOSS* {emoji}\nEntrada: *{entry}* não confirmada."


def stats_message(stats: dict) -> str:
    lines = ["📊 *Estatísticas do Sistema*\n━━━━━━━━━━━━━━━━━━━"]
    for game, data in stats.items():
        name = GAME_NAME.get(game, game)
        emoji = GAME_EMOJI.get(game, "🎮")
        total = data.get("total", 0)
        wins = data.get("wins", 0)
        losses = data.get("losses", 0)
        rate = data.get("win_rate", 0)
        lines.append(
            f"\n{emoji} *{name}*\n"
            f"   ✅ Wins: {wins} | ❌ Losses: {losses}\n"
            f"   📈 Total: {total} | 🎯 Taxa: {rate:.1f}%"
        )
    return "\n".join(lines)


WELCOME_MESSAGE = (
    "👋 *Bem-vindo ao Signal Bot!*\n\n"
    "Receba sinais automáticos de Bac Bo (Betou).\n\n"
    "Comandos:\n"
    "/stop — Parar sinais\n"
    "/start — Reativar sinais"
)
