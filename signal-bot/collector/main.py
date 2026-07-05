import asyncio
import os
from loguru import logger
from dotenv import load_dotenv

load_dotenv(dotenv_path="C:/Users/Game-PC/signal-bot/.env", override=True)

from collector.tipminer.bacbo_scraper import BacBoTipminerScraper
from collector.tipminer.dadinho_scraper import DadinhoTipminerScraper
from collector.tipminer.crash_scraper import CrashTipminerScraper


async def main():
    scrapers = []

    if os.getenv("GAME_BACBO_ENABLED", "true").lower() == "true":
        scrapers.append(BacBoTipminerScraper())
        logger.info("Bac Bo: ATIVO")

    if os.getenv("GAME_DADINHO_ENABLED", "true").lower() == "true":
        scrapers.append(DadinhoTipminerScraper())
        logger.info("Dadinho: ATIVO")

    if os.getenv("GAME_CRASH_ENABLED", "true").lower() == "true":
        scrapers.append(CrashTipminerScraper())
        logger.info("Crash: ATIVO")

    if not scrapers:
        logger.warning("Nenhum jogo ativo.")
        return

    logger.info(f"{len(scrapers)} coletor(es) iniciando...")
    await asyncio.gather(*[s.start() for s in scrapers])


if __name__ == "__main__":
    asyncio.run(main())
