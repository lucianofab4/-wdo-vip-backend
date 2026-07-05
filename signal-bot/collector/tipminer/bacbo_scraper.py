import os
from loguru import logger
from collector.tipminer.base_scraper import TipminerBaseScraper
from collector.bacbo.strategy_feed import BacBoStrategyFeed

# title="BANKER - 8 - 11:28"  ou  "PLAYER - 11 - 11:29"  ou  "TIE - 0 - 11:30"
OUTCOME_MAP = {
    "BANKER": "BANKER",
    "PLAYER": "PLAYER",
    "TIE": "TIE",
    # suporte a variações em português caso o site mude idioma
    "BANQUEIRO": "BANKER",
    "JOGADOR": "PLAYER",
    "EMPATE": "TIE",
}


class BacBoTipminerScraper(TipminerBaseScraper):
    game_name = "bacbo"
    tipminer_url = os.getenv(
        "TIPMINER_BACBO_URL",
        "https://www.tipminer.com/br/historico/betou/bac-bo",
    )
    # Círculos do Bac Bo: bg-cell-banker / bg-cell-player / bg-cell-tie
    cell_selector = "[class*='bg-cell-banker'], [class*='bg-cell-player'], [class*='bg-cell-tie']"

    def __init__(self):
        super().__init__()
        self.feed = BacBoStrategyFeed()

    async def parse_cell(self, title: str, text: str) -> dict | None:
        """
        Parseia: "BANKER - 8 - 11:28"
        → {table_id, result, value, time}
        """
        try:
            parts = [p.strip() for p in title.split(" - ")]
            if len(parts) < 2:
                return None

            outcome_raw = parts[0].upper()
            outcome = OUTCOME_MAP.get(outcome_raw)
            if not outcome:
                return None

            value = int(parts[1]) if parts[1].isdigit() else 0
            time_str = parts[2] if len(parts) >= 3 else ""

            return {
                "table_id": "tipminer_betou",
                "result": outcome,
                "value": value,
                "time": time_str,
                "raw_title": title,
            }
        except Exception as e:
            logger.debug(f"[BacBo] Erro ao parsear título '{title}': {e}")
            return None

    async def on_result(self, result: dict):
        logger.info(
            f"[BacBo] {result['result']} | valor={result['value']} | {result['time']}"
        )
        await self.feed.process(result)
