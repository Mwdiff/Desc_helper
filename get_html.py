from configparser import ConfigParser

from bs4 import BeautifulSoup
from requests import Response, Session

config = ConfigParser()
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

        page = self._session.get(url)
        if "product-" in url:
            self.product_number = 1
            yield page

        souped_page = BeautifulSoup(page.content, "lxml")
        products = souped_page.find_all("a", class_="product-name")
        self.product_number = len(products)
        for product in products:
            product_url = ("" if "http" in product.get("href") else SITE) + product.get(
                "href"
            )
            yield self._session.get(product_url)
