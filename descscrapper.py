from itertools import zip_longest
from pathlib import Path
from string import Template
from time import sleep

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook, load_workbook

from secret import secret


def GetWebpage(url: str, s: requests.Session = requests.Session()) -> "Response":
    page = s.get(url)
    return page


def ExtractProductList(page: "Response") -> list:
    souped_page = BeautifulSoup(page.content, "lxml")
    products = souped_page.find_all("a", class_="product-name")
    product_list = [secret["site"] + product.get("href") for product in products]
    return product_list


def GetProductData(page: "Response") -> dict:
    souped_page = BeautifulSoup(page.content, "lxml")

    product_data = {"opis": [], "img": [], "titles": []}

    # Znajduje producenta produktu
    producent = souped_page.find("a", class_="firmlogo").contents[0].get("title")
    product_data["producent"] = producent

    # Znajduje SKU produktu
    sku = souped_page.find("div", itemprop="productID").text
    product_data["sku"] = sku

    # Cena zakupu netto
    net_price = souped_page.find("span", id="price_net_val")
    product_data["net"] = net_price.get_text().strip(" PLN")

    # Cena SRP
    srp_price = souped_page.find("span", id="srp_val")
    product_data["srp"] = srp_price.get_text().strip(" PLN")

    description = souped_page.find("div", id="component_projector_longdescription_not")

    # Tworzy listę nagłówków z opisu
    product_data["titles"] = [
        tit.get_text(strip=True) for tit in description.find_all("h3")
    ]

    # Tworzy listę akapitów z opisu
    product_data["opis"] = [
        d.get_text(strip=True)
        for d in description.find_all("p")
        if d.get_text(strip=True)
    ]

    # Tworzy listę adresów zdjęć z opisu
    for img in description.find_all("img"):
        imgurl = img.get("src")
        if not "http" in imgurl:
            imgurl = secret["site"] + imgurl
        product_data["img"].append(imgurl)

    # Specyfikacja
    specification = description.find("tbody")
    try:
        spec = str(specification)
        reps = {"tbody": "ul", "tr>": "li>", "th>": "b>", "<td>": "", "</td>": ""}
        for o, n in reps.items():
            spec = spec.replace(o, n)

        product_data["spec"] = "<h2>Specyfikacja:</h2>\n" + spec
    except:
        product_data["spec"] = ""

    # W zestawie
    content = description.find("ul")
    if content != None:
        for sibling in content.previous_siblings:
            if sibling.name == "h3":
                list = "<h2>" + sibling.string + ":</h2>\n"
                break

        product_data["set"] = list + str(content)

    return product_data


def CompileDescription(data: dict) -> str:
    # szablon sekcji opisu
    descpart = []
    descpart.append(
        Template(
            """<div class="item item-6">
                    <section class="image-item">
                        <img src="$img" />
                    </section>
                </div>\n"""
        )
    )
    descpart.append(
        Template(
            """<div class="item item-6">
                    <section class="text-item">
                        <h1>$title</h1><p>$section</p>
                    </section>
                </div>\n"""
        )
    )
    descpart.append('<section class="section">\n')
    descpart.append("</section>\n")

    # pierwsza sekcja specyfikacja + zawartość
    firstsection = data["spec"]
    if "set" in data:
        firstsection += "\n" + data["set"]

    desc = """<section class="section">
                    <div class="item item-6">
                        <section class="text-item">
                            {}
                        </section>
                    </div>
                </section>\n""".format(
        firstsection
    )

    # kolejne sekcje nagłówek/opis + zdjęcie naprzemiennie
    for i, (imgu, t, d) in enumerate(
        zip_longest(data["img"], data["titles"], data["opis"], fillvalue="None")
    ):
        desc = (
            desc
            + descpart[2]
            + descpart[i % 2].substitute(img=imgu, title=t, section=d)
            + descpart[(i + 1) % 2].substitute(img=imgu, title=t, section=d)
            + descpart[3]
        )
    return desc


def WriteToSheet(data: dict, file: str = "PlikDostawy") -> None:
    try:
        wb = load_workbook(f"./output/{file}.xlsx")
    except:
        wb = Workbook()
        ws = wb.create_sheet(file, 0)
        header = ("sku", "Zakup netto", "SRP", "Opis", "Zdjęcia ->")
        for i, tag in enumerate(header, start=1):
            ws.cell(1, i).value = tag
        Path("./output/").mkdir(exist_ok=True)

    ws = wb.active
    row = ws.max_row + 1

    ws.cell(row, 1).value = data["sku"]
    ws.cell(row, 2).value = data["net"]
    ws.cell(row, 3).value = data["srp"]
    ws.cell(row, 4).value = CompileDescription(data)

    for i, img in enumerate(data["img"], start=5):
        ws.cell(row, i).value = img

    wb.save(f"./output/{file}.xlsx")


def ScrapeDelivery(
    URL: str, plik: str, s: requests.Session = requests.Session()
) -> None:
    p = s.post(secret["LOGIN_URL"], data=secret["payload"])

    products = ExtractProductList(GetWebpage(URL, s))

    for product in products:
        data = GetProductData(GetWebpage(product, s))
        WriteToSheet(data, plik)
        sleep(0.2)


if __name__ == "__main__":

    URL = input("Podaj adres www dostawy: ")
    plik = input("Podaj nazwę pliku: ")

    with requests.Session() as session:
        p = session.post(secret["LOGIN_URL"], data=secret["payload"])

        ScrapeDelivery(URL, plik, session)
