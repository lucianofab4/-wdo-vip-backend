import asyncio
import os
from abc import ABC, abstractmethod
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class BaseCollector(ABC):
    """Classe base para todos os coletores de jogos."""

    game_name: str = ""
    ws_url_pattern: str = ""

    def __init__(self):
        self.running = False
        self.casino_url = os.getenv("CASINO_URL", "")
        self.casino_email = os.getenv("CASINO_EMAIL", "")
        self.casino_password = os.getenv("CASINO_PASSWORD", "")

    @abstractmethod
    async def parse_message(self, message: str | bytes) -> dict | None:
        """Parseia uma mensagem do WebSocket e retorna o resultado estruturado."""
        ...

    @abstractmethod
    async def on_result(self, result: dict):
        """Chamado quando um resultado válido é detectado."""
        ...

    @retry(stop=stop_after_attempt(10), wait=wait_exponential(min=2, max=60))
    async def start(self):
        from playwright.async_api import async_playwright

        logger.info(f"[{self.game_name}] Iniciando coletor...")
        self.running = True

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            page = await context.new_page()
            ws_queue: asyncio.Queue = asyncio.Queue()

            page.on("websocket", lambda ws: self._attach_ws_handler(ws, ws_queue))

            logger.info(f"[{self.game_name}] Navegando para {self.casino_url}")
            await page.goto(self.casino_url, wait_until="domcontentloaded", timeout=60_000)

            await self._do_login(page)
            await self._navigate_to_table(page)

            logger.info(f"[{self.game_name}] Aguardando mensagens WebSocket...")

            while self.running:
                try:
                    msg = await asyncio.wait_for(ws_queue.get(), timeout=30)
                    result = await self.parse_message(msg)
                    if result:
                        await self.on_result(result)
                except asyncio.TimeoutError:
                    logger.debug(f"[{self.game_name}] Nenhuma mensagem em 30s, verificando conexão...")
                    if not await self._is_page_alive(page):
                        raise ConnectionError("Página perdida, reconectando...")

            await browser.close()

    def _attach_ws_handler(self, ws, queue: asyncio.Queue):
        url = ws.url
        if self.ws_url_pattern and self.ws_url_pattern not in url:
            return
        logger.debug(f"[{self.game_name}] WebSocket capturado: {url}")
        ws.on("framereceived", lambda payload: asyncio.create_task(queue.put(payload["payload"])))

    async def _do_login(self, page):
        """Override para implementar login específico do cassino."""
        pass

    async def _navigate_to_table(self, page):
        """Override para navegar até a mesa do jogo."""
        pass

    async def _is_page_alive(self, page) -> bool:
        try:
            await page.evaluate("1+1")
            return True
        except Exception:
            return False

    def stop(self):
        self.running = False
        logger.info(f"[{self.game_name}] Coletor parado.")
