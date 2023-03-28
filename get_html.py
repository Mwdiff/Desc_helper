import re
from configparser import ConfigParser
from datetime import datetime
from os import getcwd
from pathlib import Path
from shutil import copyfileobj

from bs4 import BeautifulSoup
from requests import Response, Session

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

        page = self._session.get(url, allow_redirects=True)
        if "product-" in url or re.search(
            r"search\.php\?text=\d{5,13}", url, flags=re.IGNORECASE
        ):
            self.product_number = 1
            yield page
            return

        souped_page = BeautifulSoup(page.content, "lxml")
        products = souped_page.find_all("a", class_="product-name")
        self.product_number = len(products)
        for product in products:
            product_url = ("" if "http" in product.get("href") else SITE) + product.get(
                "href"
            )
            yield self._session.get(product_url)

    def generate_from_list(self, list: list[str]) -> Response:
        """Generates individual product html pages from supplied URL list"""

        self.product_number = len(list)
        for product in list:
            product_url = (
                "" if "http" in product else SITE + "/search.php?text="
            ) + product.strip("rcRC ").zfill(6)
            yield self._session.get(product_url, allow_redirects=True)

    def get_news_list(self) -> list[dict[str]]:
        """Generate list of first page news with dates and urls"""

        newspage = self._session.get(SITE + "/news-pol.phtml")
        souped_page = BeautifulSoup(newspage.content, "lxml")

        news_list = []

        for news_item in souped_page.find_all(class_="article_element_wrapper"):
            news = {}
            news["title"] = news_item.find(
                "h3", class_="article_name_wrapper"
            ).get_text()
            news["url"] = (
                news_item.find("h3", class_="article_name_wrapper")
                .contents[0]
                .get("href")
            )
            date = news_item.find("div", class_="date").get_text()
            news["date"] = datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m")
            news_list.append(news)

        return news_list

    def get_article_image(self, filename: str) -> str:
        r = self._session.get(
            SITE + f"/data/include/img/news/{filename}.jpg", stream=True
        )
        if r.status_code == 200:
            with open(f"./{filename}.jpg", "wb") as f:
                r.raw.decode_content = True
                copyfileobj(r.raw, f)
        return f"{getcwd()}\{filename}.jpg"

    def get_image_binary(self, url: str) -> bytes:
        r = self._session.get(url, stream=True)
        if r.status_code == 200:
            # r.raw.decode_content = True
            return r.raw
