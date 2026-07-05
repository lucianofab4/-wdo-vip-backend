import os
from loguru import logger
from collector.tipminer.base_scraper import TipminerBaseScraper
from collector.dadinho.strategy_feed import DadinhoStrategyFeed

# title="HIGH - 9 - 11:28"  ou  "LOW - 5 - 11:29"  ou  "EQUAL - 7 - 11:30"
# Ajustar conforme o formato real do Tipminer para Dadinho/Double
OUTCOME_MAP = {
    "HIGH": "HIGH",
    "LOW": "LOW",
    "EQUAL": "EQUAL",
    "ALTO": "HIGH",
    "BAIXO": "LOW",
    "IGUAL": "EQUAL",
    # Para Double (vermelho/preto/branco)
    "RED": "RED",
    "BLACK": "BLACK",
    "WHITE": "WHITE",
    "VERMELHO": "RED",
    "PRETO": "BLACK",
    "BRANCO": "WHITE",
}

TYPE_TO_RESULT = {
    "RED": "HIGH",
    "BLACK": "LOW",
    "WHITE": "EQUAL",
    "VERMELHO": "HIGH",
    "PRETO": "LOW",
    "BRANCO": "EQUAL",
}


class DadinhoTipminerScraper(TipminerBaseScraper):
    game_name = "dadinho"
    tipminer_url = os.getenv(
        "TIPMINER_DADINHO_URL",
        "https://www.tipminer.com/br/historico/betou/double",
    )
    cell_selector = "[class*='bg-cell-']"

    def __init__(self):
        super().__init__()
        self.feed = DadinhoStrategyFeed()

    async def parse_cell(self, title: str, text: str) -> dict | None:
        try:
            parts = [p.strip() for p in title.split(" - ")]
            if len(parts) < 2:
                return None

            outcome_raw = parts[0].upper()
            value_str = parts[1] if len(parts) > 1 else "0"
            time_str = parts[2] if len(parts) >= 3 else ""

            # Normaliza para HIGH/LOW/EQUAL
            result_type = TYPE_TO_RESULT.get(outcome_raw) or OUTCOME_MAP.get(outcome_raw)
            if not result_type:
                return None

            value = int(value_str) if value_str.isdigit() else 0

            # Para Dadinho (dados) tenta inferir die1/die2
            # se value representar soma de 2 dados (2-12)
            die1 = value // 2 if value > 0 else 0
            die2 = value - die1 if value > 0 else 0

            return {
                "table_id": "tipminer_betou",
                "die1": die1,
                "die2": die2,
                "total": value,
                "result_type": result_type,
                "is_double": die1 == die2,
                "time": time_str,
                "raw_title": title,
            }
        except Exception as e:
            logger.debug(f"[Dadinho] Erro ao parsear '{title}': {e}")
            return None

    async def on_result(self, result: dict):
        logger.info(
            f"[Dadinho] {result['result_type']} | total={result['total']} | {result['time']}"
        )
        await self.feed.process(result)
