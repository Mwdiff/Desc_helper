from string import Template
from time import sleep

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook, load_workbook

from secret import secret

# auth https://docs.python-requests.org/en/latest/user/authentication/
# https://realpython.com/beautiful-soup-web-scraper-python/
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/


def ExtractProductList(url: str, s: requests.Session = requests.Session()) -> list:
    page = s.get(url)
    souped_page = BeautifulSoup(page.content, "lxml")
    products = souped_page.find_all("a", class_="product-name")
    product_list = [secret["site"] + product.get("href") for product in products]
    return product_list


def GetProductData(url: str, s: requests.Session = requests.Session()) -> dict:
    page = s.get(url)
    souped_page = BeautifulSoup(page.content, "lxml")

    product_data = {"opis": [], "img": [], "titles": []}

    producent = souped_page.find("a", class_="firmlogo").contents[0].get("title")
    product_data["producent"] = producent

    sku = souped_page.find("div", itemprop="productID").text
    product_data["sku"] = sku


    titles = souped_page.find(
        "div", id="component_projector_longdescription_not"
    ).find_all("h3")
    product_data["titles"] = [tit.text for tit in titles]

    desc = souped_page.find(
        "div", id="component_projector_longdescription_not"
    ).find_all("p")

    for element in desc:
        try:
            imgurl = element.contents[0].get("src")
            if not "http" in imgurl:
                imgurl = secret["site"] + element.contents[0].get("src")
            product_data["img"].append(imgurl)
        except:
            if not element.text.isspace():
                product_data["opis"].append(element.text)

    return product_data


# todo: specyfikacja i "w zestawie"


def CompileDescription(data: dict) -> str:
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
    desc = ""

    for i in range(min(len(data["opis"]), len(data["img"]))):
        desc = (
            desc
            + descpart[2]
            + descpart[i % 2].substitute(
                img=data["img"][i], title=data["titles"][i], section=data["opis"][i]
            )
            + descpart[(i + 1) % 2].substitute(
                img=data["img"][i], title=data["titles"][i], section=data["opis"][i]
            )
            + descpart[3]
        )
    return desc


def WriteToSheet(data: dict, file: str = "PlikDostawy") -> None:
    try:
        wb = load_workbook(f"./{file}.xlsx")
    except:
        wb = Workbook()

    ws = wb[wb.sheetnames[0]]
    row = ws.max_row + 1

    ws.cell(row, 1).value = data["sku"]
    ws.cell(row, 2).value = CompileDescription(data)

    for i in range(len(data["img"])):
        ws.cell(row, 3 + i).value = data["img"][i]

    wb.save(f"./{file}.xlsx")


URL = input("Podaj adres www dostawy: ")
plik = input("Podaj nazwę pliku: ")

with requests.Session() as s:
    p = s.post(secret["LOGIN_URL"], data=secret["payload"])

    products = ExtractProductList(URL, s)

    for product in products:
        data = GetProductData(product, s)
        WriteToSheet(data, plik)
        sleep(0.5)
