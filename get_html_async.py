import re
from asyncio import AbstractEventLoop, sleep
from configparser import ConfigParser
from datetime import datetime
from os import getcwd
from pathlib import Path
from shutil import copyfileobj

# from requests import Response, Session
from aiohttp import ClientResponse, ClientSession
from bs4 import BeautifulSoup

from get_js_enabled import BrowserRequest
from write_file import write_log

config = ConfigParser()
if not Path("./config.ini").exists():
    raise FileNotFoundError("config.ini file is missing!")
config.read("config.ini")
SITE = config["General"]["site"]


class WebConnection:
    """Login and create session"""

    def __init__(
        self,
        login_url: str = "",
        login_data: dict[str:str] = {},
        async_loop: AbstractEventLoop = None,
    ) -> None:
        self._session = ClientSession(loop=async_loop)
        self._login_url = login_url
        self._login_data = login_data

    async def __aenter__(self) -> "WebConnection":
        await self.login(self._login_url, self._login_data)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_trace) -> None:
        await self._session.close()
        if exc_type:
            write_log(exc_type, exc_value, exc_trace)
        await sleep(0)

    async def login(
        self,
        login_url: str,
        login_data: dict[str:str],
    ):
        await self._session.post(login_url, data=login_data)

    async def close(self):
        await self._session.close()
        await sleep(0)

    async def generate_product_pages(self, url: str) -> str:
        """Generates individual product html pages from supplied URL"""

        self.producent = ""

        async with self._session.get(url, allow_redirects=True) as page:
            if "product-" in url or re.search(
                r"search\.php\?text=\d{5,13}", url, flags=re.IGNORECASE
            ):
                self.product_number = 1
                yield page
                return

            content = await page.content.read()
            souped_page = BeautifulSoup(content, "lxml")
            products = souped_page.find_all("div", class_="search_list__product")

            for page_number in range(1, 10):
                async with self._session.get(
                    url + f"&counter={page_number}", allow_redirects=True
                ) as newpage:
                    if newpage.status == 404:
                        break
                    new_souped_page = BeautifulSoup(
                        await newpage.content.read(), "lxml"
                    )
                    more_products = new_souped_page.find_all(
                        "div", class_="search_list__product"
                    )
                    products += more_products

            self.product_number = len(products)
            try:
                self.producent = souped_page.find(
                    class_="filter_list_remove btn-regular"
                ).get_text()
            except AttributeError:
                pass

            for product in products:
                product_url = (
                    ""
                    if "http"
                    in product.find("a", class_="search_top__name").get("href")
                    else SITE
                ) + product.find("a", class_="search_top__name").get("href")
                async with self._session.get(product_url) as product_page:
                    yield product_page

    async def generate_from_list(self, product_list: list[str]) -> ClientResponse:
        """Generates individual product html pages from supplied URL list"""

        self.product_number = len(product_list)
        for product in product_list:
            product_url = (
                "" if "http" in product else SITE + "/search.php?text="
            ) + product.strip("rcRC ").zfill(6)
            async with self._session.get(
                product_url, allow_redirects=True
            ) as product_page:
                yield product_page

    async def get_news_list(self) -> list[dict[str]]:
        """Generate list of first page news with dates and urls"""
        async with BrowserRequest() as br:
            newspage = await br.get_content_longwait(
                SITE + "/Ostatnia-dostawa-cinfo-pol-77.html"
            )
            souped_page = BeautifulSoup(newspage, "lxml")
        news_list = []

        for news_item in souped_page.find_all(class_="col-12 product_link"):
            news = {}
            news["title"] = (
                news_item.find("span", class_="producer__name")
                .get_text()
                .replace("marki", "marki ")
            )
            news["url"] = SITE + news_item.get("href")
            date = news_item.find("div", class_="product__date").get_text()
            news["date"] = datetime.strptime(date, "%d.%m.%Y").strftime("%d-%m")
            news["icon"] = (
                news_item.find(class_="product__icon_2").contents[0].get("src")
            )
            if "http" not in news["icon"]:
                news["icon"] = SITE + news["icon"]
            news_list.append(news)
        return news_list

    async def get_article_image(self, url: str) -> str:
        filename = url.split("/")[-1].strip("_1.webp")
        async with self._session.get(url, stream=True) as r:
            if r.status_code == 200:
                with open(f"{getcwd()}\{filename}.jpg", "wb") as f:
                    r.raw.decode_content = True
                    copyfileobj(r.raw, f)
            return f"{getcwd()}\{filename}.jpg"

    async def get_image_binary(self, url: str) -> bytes:
        async with self._session.get(url) as r:
            if r.status == 200:
                # r.raw.decode_content = True
                return await r.content.read()
