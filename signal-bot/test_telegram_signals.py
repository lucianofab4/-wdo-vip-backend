"""
Teste completo: Scraper Bac Bo + Estrategia Streak + Sinais no Telegram
Sem banco de dados, sem Redis. Roda direto no terminal.
"""
import asyncio
import sys
import httpx
from collections import deque
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── Configuracao ─────────────────────────────────────────────────────────────
TOKEN   = "8817817097:AAGIOtF61oGCSXfIfnwdH1haA3OdFQGYvD4"
CHAT_ID = 1191003457
URL     = "https://www.tipminer.com/br/historico/betou/bac-bo"
SELECTOR = "[class*='bg-cell-banker'], [class*='bg-cell-player'], [class*='bg-cell-tie']"

OUTCOME_MAP = {
    "BANKER": "BANKER", "PLAYER": "PLAYER", "TIE": "TIE",
    "BANQUEIRO": "BANKER", "JOGADOR": "PLAYER", "EMPATE": "TIE",
}

MIN_STREAK = 3
MAX_GALE   = 2

# ─── Telegram ─────────────────────────────────────────────────────────────────
TG_TIMEOUT = httpx.Timeout(connect=30.0, read=30.0, write=30.0, pool=30.0)

async def send(text: str):
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=TG_TIMEOUT) as client:
                await client.post(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
                )
            return
        except Exception as e:
            print(f"  [TG] Erro ao enviar (tentativa {attempt+1}/3): {e}")
            await asyncio.sleep(3)

# ─── Estrategia Streak ────────────────────────────────────────────────────────
OPPOSITE = {"PLAYER": "BANKER", "BANKER": "PLAYER"}

class StreakStrategy:
    def __init__(self):
        self.history: deque = deque(maxlen=50)

    def add(self, outcome: str):
        self.history.append(outcome)

    def streak_count(self) -> tuple[str | None, int]:
        if not self.history:
            return None, 0
        last = self.history[-1]
        count = 0
        for x in reversed(self.history):
            if x == last:
                count += 1
            else:
                break
        return last, count

    def check_entry(self) -> tuple[bool, str]:
        last, count = self.streak_count()
        if last in ("PLAYER", "BANKER") and count >= MIN_STREAK:
            return True, OPPOSITE[last]
        return False, ""

    def resolve(self, outcome: str, entry: str) -> str:
        if outcome == "TIE":
            return "pending"
        return "win" if outcome == entry else "loss"

# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    print("\n=== Signal Bot - Bac Bo -> Telegram ===")
    print(f"Chat ID: {CHAT_ID}")
    print(f"Estrategia: Streak {MIN_STREAK}+ | Gale max: {MAX_GALE}\n")

    await send(
        "*Signal Bot Iniciado!*\n"
        "Monitorando: Bac Bo (Betou)\n"
        "Estrategia: Streak (3+ iguais -> entra no oposto)\n"
        "Gale maximo: 2\n\n"
        "_Aguardando sinais..._"
    )
    print("OK - Mensagem de inicio enviada no Telegram")

    strategy = StreakStrategy()
    open_entry = None
    gale_level = 0

    print("Abrindo browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_selector(SELECTOR, timeout=20_000)
        await asyncio.sleep(2)

        # Carrega historico inicial sem disparar sinais
        cells = await page.query_selector_all(SELECTOR)
        seen: set[str] = set()
        for cell in cells:
            title = await cell.get_attribute("title") or ""
            if title:
                seen.add(title)
                parts = [x.strip() for x in title.split(" - ")]
                outcome = OUTCOME_MAP.get(parts[0].upper()) if parts else None
                if outcome and outcome != "TIE":
                    strategy.add(outcome)

        last, count = strategy.streak_count()
        print(f"OK - {len(cells)} resultados carregados | Streak atual: {count}x {last}")
        print("Monitorando em tempo real (Ctrl+C para parar)...\n")
        print(f"{'Horario':<8} {'Resultado':<10} {'Valor':<6} {'Streak'}")
        print("-" * 40)

        while True:
            await asyncio.sleep(4)
            try:
                new_cells = await page.query_selector_all(SELECTOR)
                for cell in new_cells:
                    title = await cell.get_attribute("title") or ""
                    if not title or title in seen:
                        continue
                    seen.add(title)

                    parts  = [x.strip() for x in title.split(" - ")]
                    outcome = OUTCOME_MAP.get(parts[0].upper()) if parts else None
                    value   = parts[1] if len(parts) > 1 else "?"
                    time_s  = parts[2] if len(parts) >= 3 else "?"

                    if not outcome:
                        continue

                    # Mostra no terminal
                    last, count = strategy.streak_count()
                    streak_info = f"{count+1}x {outcome}" if outcome == last else f"1x {outcome}"
                    print(f"[{time_s}]  {outcome:<10} {value:<6} {streak_info}")

                    # ── Resolve sinal aberto ──
                    if open_entry:
                        result = strategy.resolve(outcome, open_entry)

                        if result == "pending":
                            print(f"         -> TIE - mantendo sinal em {open_entry}")
                            strategy.add(outcome)
                            continue

                        if result == "win":
                            print(f"         -> WIN!")
                            await send(
                                f"*WIN!*\n"
                                f"Entrada: *{open_entry}*"
                                + (f" | Gale {gale_level}" if gale_level else "")
                            )
                            open_entry = None
                            gale_level = 0

                        elif result == "loss":
                            if gale_level < MAX_GALE:
                                gale_level += 1
                                print(f"         -> LOSS -> Gale {gale_level}")
                                await send(
                                    f"*LOSS - Gale {gale_level}*\n"
                                    f"Entrar novamente: *{open_entry}*\n"
                                    f"_Proxima rodada_"
                                )
                            else:
                                print(f"         -> LOSS final")
                                await send(
                                    f"*LOSS (encerrado)*\n"
                                    f"Entrada *{open_entry}* nao confirmada."
                                )
                                open_entry = None
                                gale_level = 0

                    strategy.add(outcome)

                    # ── Verifica nova entrada ──
                    if not open_entry and outcome != "TIE":
                        should, entry = strategy.check_entry()
                        if should:
                            last_r, streak = strategy.streak_count()
                            open_entry = entry
                            gale_level = 0
                            print(f"\n>>> SINAL: entrar em {entry} | {streak}x {last_r} seguidos\n")
                            cor = "AZUL (Player)" if entry == "PLAYER" else "VERMELHO (Banker)"
                            await send(
                                f"*ENTRADA CONFIRMADA*\n"
                                f"Jogo: *Bac Bo* (Betou)\n"
                                f"Entrar: *{cor}*\n"
                                f"Motivo: {streak}x {last_r} seguidos\n"
                                f"Gale max: {MAX_GALE}\n"
                                f"_Proxima rodada_"
                            )

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Erro: {e}")
                try:
                    await page.reload(wait_until="domcontentloaded", timeout=30_000)
                    await page.wait_for_selector(SELECTOR, timeout=15_000)
                except Exception:
                    pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado.")
