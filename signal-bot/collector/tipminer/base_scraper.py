import asyncio
import os
from abc import ABC, abstractmethod
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

LOGIN_URL = "https://www.tipminer.com/br/login"
SESSION_FILE = os.path.join(os.path.dirname(__file__), "tipminer_session.json")


class TipminerBaseScraper(ABC):
    """
    Scraper base para o Tipminer.
    Abre a página via Playwright, faz login se necessário,
    lê os resultados do DOM e detecta novas rodadas.
    """

    game_name: str = ""
    tipminer_url: str = ""
    cell_selector: str = "[class*='bg-cell-']"

    def __init__(self):
        self._seen: set[str] = set()
        self._last_title: str = ""
        self.running = False

    @abstractmethod
    async def parse_cell(self, title: str, text: str) -> dict | None:
        ...

    @abstractmethod
    async def on_result(self, result: dict):
        ...

    async def _do_login(self, page) -> bool:
        """Faz login no Tipminer. Retorna True se bem-sucedido."""
        email = os.getenv("TIPMINER_EMAIL", "")
        password = os.getenv("TIPMINER_PASSWORD", "")
        if not email or not password:
            logger.warning(f"[{self.game_name}] Credenciais do Tipminer nao configuradas.")
            return False

        logger.info(f"[{self.game_name}] Fazendo login no Tipminer...")
        try:
            await page.goto(LOGIN_URL, wait_until="networkidle", timeout=60_000)
            await asyncio.sleep(2)

            email_selector = "input[type='email'], input[name='email'], input[placeholder*='mail'], input[placeholder*='Email'], input[placeholder*='email']"
            try:
                await page.wait_for_selector(email_selector, timeout=30_000)
            except Exception:
                logger.error(f"[{self.game_name}] Campo de email nao apareceu. URL: {page.url} | Titulo: {await page.title()}")
                return False

            # Preenche email
            await page.fill(email_selector, email)
            await asyncio.sleep(0.5)

            # Preenche senha
            await page.wait_for_selector("input[type='password']", timeout=10_000)
            await page.fill("input[type='password']", password)
            await asyncio.sleep(0.5)

            # Clica no botão de login
            await page.click("button[type='submit']")
            await asyncio.sleep(5)

            # Verifica se o login foi bem-sucedido (URL mudou)
            current_url = page.url
            if "login" in current_url:
                logger.error(f"[{self.game_name}] Login falhou — ainda na pagina de login.")
                return False

            logger.info(f"[{self.game_name}] Login OK. URL atual: {current_url}")

            # Salva o estado da sessão (cookies) para reuso
            state = await page.context.storage_state()
            import json
            with open(SESSION_FILE, "w") as f:
                json.dump(state, f)
            logger.info(f"[{self.game_name}] Sessao salva em {SESSION_FILE}")
            return True

        except Exception as e:
            logger.error(f"[{self.game_name}] Erro no login: {e}")
            return False

    @retry(stop=stop_after_attempt(20), wait=wait_exponential(min=3, max=60))
    async def start(self):
        from playwright.async_api import async_playwright
        import json

        logger.info(f"[{self.game_name}] Iniciando scraper Tipminer: {self.tipminer_url}")
        self.running = True

        async with async_playwright() as p:
            # Carrega sessão salva se existir
            storage_state = None
            if os.path.exists(SESSION_FILE):
                try:
                    with open(SESSION_FILE) as f:
                        storage_state = json.load(f)
                    logger.debug(f"[{self.game_name}] Sessao carregada de {SESSION_FILE}")
                except Exception:
                    storage_state = None

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            ctx_kwargs = dict(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="pt-BR",
                java_script_enabled=True,
            )
            if storage_state:
                ctx_kwargs["storage_state"] = storage_state

            context = await browser.new_context(**ctx_kwargs)
            page = await context.new_page()

            # Aplica stealth para evitar detecção Cloudflare
            try:
                from playwright_stealth import stealth_async
                await stealth_async(page)
                logger.debug(f"[{self.game_name}] Stealth aplicado.")
            except ImportError:
                pass

            # Oculta navigator.webdriver manualmente como fallback
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            logger.info(f"[{self.game_name}] Abrindo {self.tipminer_url}")
            await page.goto(self.tipminer_url, wait_until="domcontentloaded", timeout=60_000)
            await asyncio.sleep(3)

            # Se redirecionou para login, faz o login
            if "login" in page.url:
                logger.info(f"[{self.game_name}] Redirecionado para login. Autenticando...")
                ok = await self._do_login(page)
                if not ok:
                    raise RuntimeError(f"[{self.game_name}] Nao foi possivel fazer login.")
                # Volta para a URL do jogo
                await page.goto(self.tipminer_url, wait_until="domcontentloaded", timeout=60_000)
                await asyncio.sleep(3)

            # Se ainda não autenticado (sem redirect mas sem dados), tenta login direto
            if "login" not in page.url:
                try:
                    await page.wait_for_selector(self.cell_selector, timeout=15_000)
                except Exception:
                    logger.warning(f"[{self.game_name}] Dados nao encontrados em 15s — tentando login. URL: {page.url}")
                    ok = await self._do_login(page)
                    if not ok:
                        raise RuntimeError(f"[{self.game_name}] Login falhou.")
                    await page.goto(self.tipminer_url, wait_until="domcontentloaded", timeout=60_000)
                    await asyncio.sleep(3)

            # Aguarda os resultados aparecerem no DOM
            try:
                await page.wait_for_selector(self.cell_selector, timeout=30_000)
            except Exception:
                logger.warning(f"[{self.game_name}] Selector nao encontrado em 30s. URL: {page.url}")
                raise

            await asyncio.sleep(2)

            # Carrega o estado inicial sem disparar sinais
            await self._snapshot_current(page)
            logger.info(f"[{self.game_name}] Pronto. Monitorando...")

            while self.running:
                try:
                    await self._check_new_results(page)
                    await asyncio.sleep(int(os.getenv("SCRAPER_INTERVAL_SECONDS", "4")))
                except Exception as e:
                    logger.warning(f"[{self.game_name}] Erro no loop: {e}")
                    try:
                        await page.reload(wait_until="domcontentloaded", timeout=30_000)
                        await page.wait_for_selector(self.cell_selector, timeout=20_000)
                        await self._snapshot_current(page)
                    except Exception as reload_err:
                        logger.error(f"[{self.game_name}] Falha ao recarregar: {reload_err}")
                        raise

            await browser.close()

    async def _get_cells(self, page) -> list[dict]:
        cells = await page.query_selector_all(self.cell_selector)
        results = []
        for cell in cells:
            title = await cell.get_attribute("title") or ""
            text = (await cell.inner_text()).strip()
            if title:
                results.append({"title": title, "text": text})
        return results

    async def _snapshot_current(self, page):
        cells = await self._get_cells(page)
        for cell in cells:
            self._seen.add(cell["title"])
        if cells:
            self._last_title = cells[-1]["title"]
        logger.debug(f"[{self.game_name}] Snapshot: {len(self._seen)} resultados existentes.")

    async def _check_new_results(self, page):
        cells = await self._get_cells(page)
        if not cells:
            return

        new_cells = [c for c in cells if c["title"] not in self._seen]

        for cell in new_cells:
            self._seen.add(cell["title"])
            result = await self.parse_cell(cell["title"], cell["text"])
            if result:
                logger.info(f"[{self.game_name}] Novo resultado: {cell['title']}")
                await self.on_result(result)

    def stop(self):
        self.running = False
