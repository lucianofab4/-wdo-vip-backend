import os
from loguru import logger
from collector.base_collector import BaseCollector
from collector.crash.parser import parse_crash_message
from collector.crash.strategy_feed import CrashStrategyFeed


class CrashCollector(BaseCollector):
    game_name = "crash"
    ws_url_pattern = os.getenv("CRASH_WS_PATTERN", "")

    def __init__(self):
        super().__init__()
        self.feed = CrashStrategyFeed()
        self.table_url = os.getenv("CRASH_TABLE_URL", self.casino_url)

    async def parse_message(self, message: str | bytes) -> dict | None:
        return parse_crash_message(message)

    async def on_result(self, result: dict):
        logger.info(f"[Crash] Multiplicador: {result['multiplier']}x | Mesa: {result['table_id']}")
        await self.feed.process(result)

    async def _navigate_to_table(self, page):
        if self.table_url and self.table_url != self.casino_url:
            await page.goto(self.table_url, wait_until="domcontentloaded", timeout=60_000)
