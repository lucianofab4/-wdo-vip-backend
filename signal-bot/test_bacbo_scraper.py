"""
Teste isolado do scraper Bac Bo - sem banco de dados, sem Redis.
Abre o Tipminer, le os ultimos resultados e imprime no terminal.
"""
import asyncio
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("TIPMINER_BACBO_URL", "https://www.tipminer.com/br/historico/betou/bac-bo")

OUTCOME_MAP = {
    "BANKER": "BANKER",
    "PLAYER": "PLAYER",
    "TIE": "TIE",
    "BANQUEIRO": "BANKER",
    "JOGADOR": "PLAYER",
    "EMPATE": "TIE",
}

LABEL = {"BANKER": "[BANKER]", "PLAYER": "[PLAYER]", "TIE": "[TIE]  "}

URL = os.environ["TIPMINER_BACBO_URL"]
CELL_SELECTOR = "[class*='bg-cell-banker'], [class*='bg-cell-player'], [class*='bg-cell-tie']"


async def main():
    from playwright.async_api import async_playwright

    print("\n=== Teste Scraper Bac Bo ===")
    print(f"URL: {URL}")
    print("Abrindo browser headless...\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        print("OK - Pagina carregada. Aguardando resultados no DOM...")

        try:
            await page.wait_for_selector(CELL_SELECTOR, timeout=20_000)
        except Exception:
            print("ERRO - Nenhum resultado encontrado. Verifique o seletor CSS.")
            await browser.close()
            return

        cells = await page.query_selector_all(CELL_SELECTOR)
        print(f"OK - {len(cells)} resultados encontrados no DOM\n")
        print("-" * 50)
        print(f"{'#':<4} {'Resultado':<12} {'Valor':<8} {'Horario'}")
        print("-" * 50)

        results = []
        for cell in cells:
            title = await cell.get_attribute("title") or ""
            parts = [p.strip() for p in title.split(" - ")]
            if len(parts) >= 2:
                outcome_raw = parts[0].upper()
                outcome = OUTCOME_MAP.get(outcome_raw)
                value = parts[1] if len(parts) > 1 else "-"
                time_str = parts[2] if len(parts) >= 3 else "-"
                if outcome:
                    results.append((outcome, value, time_str))

        for i, (outcome, value, time_str) in enumerate(results[-20:], 1):
            label = LABEL.get(outcome, outcome)
            print(f"{i:<4} {label:<12} {value:<8} {time_str}")

        print("-" * 50)
        print(f"\nTotal lido: {len(results)} resultados")

        # Monitora 30 segundos para detectar resultado novo
        print("\nMonitorando 30 segundos para detectar novo resultado...\n")
        seen = set()
        for cell in cells:
            t = await cell.get_attribute("title") or ""
            if t:
                seen.add(t)

        for tick in range(6):
            await asyncio.sleep(5)
            new_cells = await page.query_selector_all(CELL_SELECTOR)
            found_new = False
            for cell in new_cells:
                title = await cell.get_attribute("title") or ""
                if title and title not in seen:
                    seen.add(title)
                    parts = [p.strip() for p in title.split(" - ")]
                    outcome = OUTCOME_MAP.get(parts[0].upper(), "?") if parts else "?"
                    label = LABEL.get(outcome, outcome)
                    print(f">> NOVO RESULTADO: {label} | {title}")
                    found_new = True
            if not found_new:
                print(f"  [{tick+1}/6] Aguardando nova rodada...")

        print("\nTeste concluido.")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
