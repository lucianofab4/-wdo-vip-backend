import os
from loguru import logger
from collector.base_collector import BaseCollector
from collector.dadinho.parser import parse_dadinho_message
from collector.dadinho.strategy_feed import DadinhoStrategyFeed


class DadinhoCollector(BaseCollector):
    game_name = "dadinho"
    ws_url_pattern = os.getenv("DADINHO_WS_PATTERN", "")

    def __init__(self):
        super().__init__()
        self.feed = DadinhoStrategyFeed()
        self.table_url = os.getenv("DADINHO_TABLE_URL", self.casino_url)

    async def parse_message(self, message: str | bytes) -> dict | None:
        return parse_dadinho_message(message)

    async def on_result(self, result: dict):
        logger.info(f"[Dadinho] {result['die1']}+{result['die2']}={result['total']} ({result['result_type']}) | Mesa: {result['table_id']}")
        await self.feed.process(result)

    async def _navigate_to_table(self, page):
        if self.table_url and self.table_url != self.casino_url:
            await page.goto(self.table_url, wait_until="domcontentloaded", timeout=60_000)
