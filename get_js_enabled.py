from asyncio import create_task, run
from configparser import ConfigParser
from pathlib import Path

from playwright.async_api import async_playwright

from write_file import write_log

config = ConfigParser()
config.read("config.ini")
SITE = config["General"]["site"]
HEADERS = {
    "Accept-Language": "pl,en-US;q=0.7,en;q=0.3",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
}

class BrowserRequest:
    """Creates async context manager for Playwright chromium browser. Use obj.goto(url, wait_until="networkidle")"""

    browser_context_path = "logged_in.json"

    def __init__(self):
        self.acm = async_playwright()

    async def __aenter__(self):
        self.playwright = await self.acm.__aenter__()

        self.browser = await self.playwright.chromium.launch()

        if not Path(self.browser_context_path).exists():
            await self._context_login(self.browser)

        self.context = await self.browser.new_context(storage_state="logged_in.json")
        self.page = await self.context.new_page()

        return self

    async def __aexit__(self, exc_type, exc_value, exc_trace) -> None:
        await self.context.close()
        await self.browser.close()
        await self.acm.__aexit__(exc_type, exc_value, exc_trace)
        if exc_type:
            write_log(exc_type, exc_value, exc_trace)

    async def get_content_longwait(self, url: str):
        await self.page.goto(url, timeout=100000, wait_until="networkidle")
        html = await self.page.content()
        return html

    @classmethod
    async def _context_login(cls, browser):
        context = await browser.new_context(extra_http_headers=HEADERS)

        page = await context.new_page()
        await page.goto(SITE + "/signin.php")
        await page.get_by_label("Login / Nr karty stałego klienta / E-mail").fill(
            config["Login_data"]["login"]
        )
        await page.get_by_label("Hasło / Pin karty stałego klienta").fill(
            config["Login_data"]["password"]
        )
        await page.get_by_role("button", name="Przejdź dalej").click()

        await context.storage_state(path=cls.browser_context_path)

        await context.close()

    @classmethod
    async def create_browser_context(cls) -> None:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            await cls._context_login(browser=browser)

            await browser.close()
