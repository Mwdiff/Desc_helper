import re
from configparser import ConfigParser
from datetime import datetime
from os import getcwd
from pathlib import Path
from shutil import copyfileobj

from bs4 import BeautifulSoup
from requests import Response, Session

from get_js_enabled import BrowserRequest

config = ConfigParser()
if not Path("./config.ini").exists():
    raise FileNotFoundError("config.ini file is missing!")
config.read("config.ini")
SITE = config["General"]["site"]


class WebConnection:
    """Login and create session"""

    def __init__(
        self,
        login_url: str,
        login_data: dict[str:str],
    ) -> None:
        self._session = Session()
        self._login = self._session.post(login_url, data=login_data)

    def generate_product_pages(self, url: str) -> Response:
        """Generates individual product html pages from supplied URL"""

        self.producent = ""

        page = self._session.get(url, allow_redirects=True)
        if "product-" in url or re.search(
            r"search\.php\?text=\d{5,13}", url, flags=re.IGNORECASE
        ):
            self.product_number = 1
            yield page
            return

        souped_page = BeautifulSoup(page.content, "lxml")
        products = souped_page.find_all("div", class_="search_list__product")

        for page in range(1, 10):
            newpage = self._session.get(url + f"&counter={page}", allow_redirects=True)
            if newpage.status_code == 404:
                break
            new_souped_page = BeautifulSoup(newpage.content, "lxml")
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
                if "http" in product.find("a", class_="search_top__name").get("href")
                else SITE
            ) + product.find("a", class_="search_top__name").get("href")
            yield self._session.get(product_url)

    def generate_from_list(self, list: list[str]) -> Response:
        """Generates individual product html pages from supplied URL list"""

        self.product_number = len(list)
        for product in list:
            product_url = (
                "" if "http" in product else SITE + "/search.php?text="
            ) + product.strip("rcRC ").zfill(6)
            yield self._session.get(product_url, allow_redirects=True)

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
            news_list.append(news)
        return news_list

    def get_article_image(self, url: str) -> str:
        filename = url.split("/")[-1].strip("_1.webp")
        r = self._session.get(
            SITE + url,
            stream=True,
        )
        if r.status_code == 200:
            with open(f"{getcwd()}\{filename}.jpg", "wb") as f:
                r.raw.decode_content = True
                copyfileobj(r.raw, f)
        return f"{getcwd()}\{filename}.jpg"

    def get_image_binary(self, url: str) -> bytes:
        r = self._session.get(url, stream=True)
        if r.status_code == 200:
            # r.raw.decode_content = True
            return r.raw
