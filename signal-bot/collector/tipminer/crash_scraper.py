import os
import re
from loguru import logger
from collector.tipminer.base_scraper import TipminerBaseScraper
from collector.crash.strategy_feed import CrashStrategyFeed

# title="2.45x - 11:28"  ou  "CRASH 1.00x - 11:29"  ou  "1.50 - 11:30"


class CrashTipminerScraper(TipminerBaseScraper):
    game_name = "crash"
    tipminer_url = os.getenv(
        "TIPMINER_CRASH_URL",
        "https://www.tipminer.com/br/historico/betou/crash",
    )
    cell_selector = "[class*='bg-cell-']"

    def __init__(self):
        super().__init__()
        self.feed = CrashStrategyFeed()

    async def parse_cell(self, title: str, text: str) -> dict | None:
        try:
            # Extrai qualquer número decimal do título (ex: "2.45x", "1.00", "CRASH 3.21x")
            match = re.search(r"(\d+[\.,]\d+)", title)
            if not match:
                # Tenta pegar só inteiro (ex: "2x", "1x")
                match = re.search(r"(\d+)x?", title)
                if not match:
                    return None

            multiplier = float(match.group(1).replace(",", "."))
            if multiplier < 1.0:
                return None

            # Extrai horário — padrão HH:MM ou HH:MM:SS
            time_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", title)
            time_str = time_match.group(1) if time_match else ""

            return {
                "table_id": "tipminer_betou",
                "multiplier": multiplier,
                "time": time_str,
                "raw_title": title,
            }
        except Exception as e:
            logger.debug(f"[Crash] Erro ao parsear '{title}': {e}")
            return None

    async def on_result(self, result: dict):
        logger.info(
            f"[Crash] {result['multiplier']}x | {result['time']}"
        )
        await self.feed.process(result)
