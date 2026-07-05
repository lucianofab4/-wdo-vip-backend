import os
from loguru import logger
from collector.base_collector import BaseCollector
from collector.bacbo.parser import parse_bacbo_message
from collector.bacbo.strategy_feed import BacBoStrategyFeed


class BacBoCollector(BaseCollector):
    game_name = "bacbo"
    ws_url_pattern = os.getenv("BACBO_WS_PATTERN", "")

    def __init__(self):
        super().__init__()
        self.feed = BacBoStrategyFeed()
        self.table_url = os.getenv("BACBO_TABLE_URL", self.casino_url)

    async def parse_message(self, message: str | bytes) -> dict | None:
        return parse_bacbo_message(message)

    async def on_result(self, result: dict):
        logger.info(f"[BacBo] Resultado: {result['result']} | Mesa: {result['table_id']}")
        await self.feed.process(result)

    async def _navigate_to_table(self, page):
        if self.table_url and self.table_url != self.casino_url:
            logger.info(f"[BacBo] Navegando para mesa: {self.table_url}")
            await page.goto(self.table_url, wait_until="domcontentloaded", timeout=60_000)
