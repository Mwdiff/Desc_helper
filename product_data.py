import re
from asyncio import run
from configparser import ConfigParser
from itertools import zip_longest
from pathlib import Path
from string import Template

from bs4 import BeautifulSoup

from img_replace import ReplaceImg

config = ConfigParser()
if not Path("./config.ini").exists():
    raise FileNotFoundError("config.ini file is missing!")
config.read("config.ini")
SITE = config["General"]["site"]


class ProductData:
    def __init__(self, page_content: bytes) -> None:
        self._page = BeautifulSoup(page_content, "lxml")
        self._body = self._page.find("section", id="projector_longdescription")
        self._gen_sku()
        self._gen_ean()
        self._gen_net()
        self._gen_srp()
        self._gen_qty()
        self._gen_prodno()

    def _gen_sku(self):
        self.sku = (
            self._page.find("div", class_="product_codes")
            .find(text="SKU")
            .parent.next_sibling.get_text()
        )

    def _gen_ean(self):
        self.ean = (
            self._page.find("div", class_="product_codes")
            .find(text="Kod EAN")
            .parent.next_sibling.get_text()
        )

    def _gen_net(self):
        self.net = (
            self._page.find("div", class_="projector_prices")
            .find(class_="projector_prices__srp netto")
            .get_text()
            .strip("\t\n ()")
            .replace("PLNnetto", "")
            .replace(".", ",")
        )

    def _gen_srp(self):
        self.srp = (
            self._page.find(class_="projector_prices__srp black mr-1")
            .get_text()
            .strip("PLN")
            .replace(".", ",")
        )

    def _gen_qty(self) -> None:
        self.qty = (
            self._page.find(class_="search_versions__status_amount_mw big_avail")
            .get_text()
            .strip(" szt.")
        )

    def _gen_prodno(self) -> None:
        self.prodno = (
            self._page.find("div", class_="product_codes")
            .find(text="Kod producenta")
            .parent.next_sibling.get_text()
        )

    def initialize_description(self):
        if self._body is None:
            self.description = "BRAK"
            self.images = []
            raise AttributeError
        self._gen_headers()
        self._gen_description_text(self._body)
        self._gen_image_list()
        self._gen_contents()
        self._gen_specification()

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
        images = [
            re.sub(r"\?v=\d+", "", image.get("src").strip(SITE))
            for image in self._body.find_all("img")
            if image.get("src")
            and not re.match(r".*xiaomi_logo", image.get("src"), flags=re.IGNORECASE)
        ]
        print(images) #test
        print("\n\n")
        img_replace = ReplaceImg.replaceimg(self.ean, images)
        print(images) #test
        print("\n\n")
        for i, img in enumerate(images):
            if img in img_replace:
                images[i] = img_replace[img]
        print(images) #test
        print("\n\n")
        self.images = images

    def _gen_contents(self) -> None:
        try:
            content = self._body.find("ul")
        except AttributeError:
            content = None

        if content is None:
            self.contents = ""
            return

        cont_list = ""
        for sibling in content.previous_siblings:
            if sibling.name == "h3":
                header = sibling.get_text(strip=True)
                cont_list = "<h2>" + header + ("" if ":" in header else ":") + "</h2>\n"
                break

        self.contents = cont_list + str(content).replace(
            ' class="list-disc pl-5"', ""
        ).replace(' style="text-align:justify"', "")

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
                    r"(\s?style=\"[^\>]+\")|(</?span[^>]*>)|(</?td[^>]*>)|\
                        <br>|<p>|<tr><th>\s*</th>\s*(<td></td>)?</tr>"
                ),
                "ul": re.compile("tbody"),
                r"<\g<1>li>": re.compile(r"<(/?)tr[^>]*>"),
                r"<\g<1>\g<2>b>": re.compile(r"<(/?)th[^>]*>|<(/?)strong[^>]*>"),
                "; ": re.compile(r"</p>"),
                r": </b>": re.compile(r"\s*:?\s*</b>"),
            }

            for substitute, regex in regex.items():
                spec_str = regex.sub(substitute, spec_str)

            self.specification = "<h2>Specyfikacja:</h2>\n" + spec_str

    def assemble_description(self) -> None:
        style_template_text = Template(
            """[iai:allegro_description_section_text-begin]
                                <h2>$title</h2><p>$section</p>
            [iai:allegro_description_section_text-end]\n"""
        )

        style_template_img = Template(
            """[iai:allegro_description_section_photo_list-begin]
                            [iai:photo_url($img)]
               [iai:allegro_description_section_photo_list-end]\n"""
        )

        description_header = """[iai:allegro_description_section_text-end]
                            [iai:allegro_description_section_text_and_photo-begin]
                            <h1>[iai:product_name_auction]</h1>[iai:product_photos_large_1]
                            [iai:allegro_description_section_text_and_photo-end]"""

        description_foot = """[iai:allegro_description_section_photo_list-begin]
                            [iai:product_photos_large_1]
                            [iai:allegro_description_section_photo_list-end]
                            [iai:allegro_description_section_text-begin]"""

        # pierwsza sekcja specyfikacja + zawartość
        # description = ""

        # if self.specification or self.contents:
        #    description += """[iai:allegro_description_section_text-begin]
        #                            {}
        #                      [iai:allegro_description_section_text-end]\n""".format(
        #        "\n".join([self.specification, self.contents])
        #    )

        # if self.specification or self.contents:
        description = """[iai:allegro_description_section_text_and_photo-begin]
                            <p><b>Producent:</b> [iai:product_producer_name]</p>
                            <p><b>Kod Produktu:</b> [iai:product_code_producer]</p>
                                {}
                            [iai:product_photos_large_1]
                          [iai:allegro_description_section_text_and_photo-end]\n""".format(
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

        self.description = (
            description_header
            + re.sub(
                r"\[iai\:photo_url\(assets[^)]*\)\]",
                "[iai:product_photos_large_1]",
                description,
            )
            + description_foot
        )


def header_filter(title):
    if title.name in [
        "h1",
        "h2",
        "h3",
    ] or title.find("span", style=re.compile("font-size: 14pt;")):
        return True
