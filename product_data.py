import re
from configparser import ConfigParser
from itertools import zip_longest
from pathlib import Path
from string import Template

from bs4 import BeautifulSoup, NavigableString
from requests import Response

config = ConfigParser()
if not Path("./config.ini").exists():
    raise FileNotFoundError("config.ini file is missing!")
config.read("config.ini")
SITE = config["General"]["site"]


class ProductData:
    def __init__(self, page: Response) -> None:
        self._page = BeautifulSoup(page.content, "lxml")
        self._body = self._page.find(
            "div", id="component_projector_longdescription_not"
        )
        if self._body is None:
            raise AttributeError

        self._gen_sku()
        self._gen_net()
        self._gen_srp()
        self._gen_qty()

        self._gen_headers()
        self._gen_description_text(self._body)
        self._gen_image_list()
        self._gen_contents()
        self._gen_specification()

    def _gen_sku(self):
        self.sku = self._page.find("div", itemprop="productID").text

    def _gen_net(self):
        self.net = (
            self._page.find("span", id="price_net_val")
            .get_text()
            .strip(" PLN")
            .replace(" ", "")
        )

    def _gen_srp(self):
        self.srp = (
            self._page.find("span", id="srp_val")
            .get_text()
            .strip(" PLN")
            .replace(" ", "")
        )

    def _gen_qty(self) -> None:
        self.qty = (
            self._page.find("div", class_="projector_avail")
            .get_text()
            .replace("szt.", "")
            .strip()
        )

    def _gen_headers(self) -> None:
        try:
            self.headers = list(
                {
                    title.get_text(strip=True): ""
                    for title in self._body.find_all(header_filter)
                    if not title.find("span", style=re.compile(r"12pt;|10pt;"))
                    and title.get_text(strip=True)
                }
            )

        except AttributeError:
            self.headers = []

        for header in reversed(self.headers):
            if re.match(
                r"specyfikacja.{0,5}$|^.{0,10}zestaw.{0,5}$",
                header,
                flags=re.IGNORECASE,
            ):
                self.headers.pop()

    def _gen_description_text(self, element: BeautifulSoup) -> list[str]:
        try:
            description_items = [
                section.get_text(strip=True)
                for section in element
                if section.get_text(strip=True)
                and section.name not in ["style", "ul", "table"]
                and "iai_bottom" not in section.get_attribute_list("class")
                and "table-wrapper" not in section.get_attribute_list("class")
            ]
        except AttributeError:
            self.description_text = []
            return
        except TypeError:
            description_items = []

        if not description_items:
            for child in element.contents:
                if child.get_text(strip=True) and child.name != "style":
                    description_items = self._gen_description_text(child)

        if not self.headers:
            self._gen_headers()

        self.description_text = [
            item
            for item in description_items
            if item not in self.headers
            and not re.match(
                r"specyfikacja.{0,5}$|^.{0,10}zestaw.{0,5}$", item, flags=re.IGNORECASE
            )
            and not re.match(
                r"Marka .+ jest częścią ekosystemu Xiaomi", item, flags=re.IGNORECASE
            )
        ]
        return self.description_text

    def _gen_image_list(self) -> None:
        self.images = list(
            {
                ("" if "http" in image.get("src") else SITE) + image.get("src"): ""
                for image in self._body.find_all("img")
                if not re.match(
                r".*xiaomi_logo", image.get("src"), flags=re.IGNORECASE
                )
            }
        )

    def _gen_contents(self) -> None:
        try:
            content = self._body.find("ul")
        except AttributeError:
            content = None

        if content is None:
            self.contents = ""
            return

        list = ""
        for sibling in content.previous_siblings:
            if sibling.name == "h3":
                header = sibling.get_text(strip=True)
                list = "<h2>" + header + ("" if ":" in header else ":") + "</h2>\n"
                break

        self.contents = list + str(content)

    def _gen_specification(self) -> None:
        try:
            spec = self._body.find_all("tbody")
        except AttributeError:
            self.specification = ""
        else:
            if not spec:
                self.specification = ""
                return
            spec_str = ""
            for table in spec:
                spec_str += str(table) + "\n"
            regex = {
                "": re.compile(
                    r"(\s?style=\"[^\>]+\")|(</?span[^>]*>)|(</?td[^>]*>)|<br>|<p>"
                ),
                "ul": re.compile("tbody"),
                "<\g<1>li>": re.compile(r"<(/?)tr[^>]*>"),
                "<\g<1>\g<2>b>": re.compile(r"<(/?)th[^>]*>|<(/?)strong[^>]*>"),
                "; ": re.compile(r"</p>"),
            }

            for substitute, regex in regex.items():
                spec_str = regex.sub(substitute, spec_str)

            self.specification = "<h2>Specyfikacja:</h2>\n" + spec_str

    def assemble_description(self) -> None:
        style_template_text = Template(
            """<section class="section">
                        <div class="item item-12">
                            <section class="text-item">
                                <h2>$title</h2><p>$section</p>
                            </section>
                        </div>
                    </section>\n"""
        )

        style_template_img = Template(
            """<section class="section">
                    <div class="item item-12">
                        <section class="image-item">
                            <img src="$img" />
                        </section>
                    </div>
                </section>\n"""
        )

        # pierwsza sekcja specyfikacja + zawartość
        description = ""

        if self.specification or self.contents:
            description += """<section class="section">
                            <div class="item item-12">
                                <section class="text-item">
                                    {}
                                </section>
                            </div>
                        </section>\n""".format(
                "\n".join([self.specification, self.contents])
            )

        # kolejne sekcje nagłówek+opis / zdjęcie naprzemiennie
        for t, i, d in zip_longest(
            self.headers, self.images, self.description_text, fillvalue=""
        ):
            description = (
                description
                + style_template_text.substitute(img=i, title=t, section=d)
                + style_template_img.substitute(img=i, title=t, section=d)
            )

        self.description = description


def header_filter(title):
    if title.name in [
        "h1",
        "h2",
        "h3",
    ] or title.find("span", style=re.compile("font-size: 14pt;")):
        return True
