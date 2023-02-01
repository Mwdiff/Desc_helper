#!C:\Users\hande\Documents\Python scripts\Desc_helper-master\desc_helper_venv\Scripts\python

from time import sleep

from get_html import WebConnection
from product_data import ProductData
from write_file import *

config = ConfigParser()
config.read("config.ini")

# todo GUI


def main():
    session = WebConnection(config["Login"]["login_url"], dict(config["Login_data"]))

    lista = [
        # "https://b2b.innpro.pl/search.php?text=029447",
        # "https://b2b.innpro.pl/search.php?text=040687",
        # "https://b2b.innpro.pl/search.php?text=027050",
        # "https://b2b.innpro.pl/search.php?text=029472",
        # "https://b2b.innpro.pl/search.php?text=040810",
        # "https://b2b.innpro.pl/search.php?text=026431",
        # "https://b2b.innpro.pl/search.php?text=027077",
        # "https://b2b.innpro.pl/search.php?text=040240",
        # "https://b2b.innpro.pl/search.php?text=040235",
        # "https://b2b.innpro.pl/search.php?text=040689",
        # "https://b2b.innpro.pl/search.php?text=038517",
        # "https://b2b.innpro.pl/search.php?text=026647",
        # "https://b2b.innpro.pl/search.php?text=037131",
        # "https://b2b.innpro.pl/search.php?text=043272",
        "https://b2b.innpro.pl/search.php?text=030598",
        "https://b2b.innpro.pl/search.php?text=032284",
        "https://b2b.innpro.pl/search.php?text=032271",
        "https://b2b.innpro.pl/search.php?text=032263",
    ]

    while session:
        url = input("Podaj adres www dostawy: ")
        if not url:
            print("Zakończono")
            return

        filename = check_duplicate_name(input("Podaj nazwę pliku: "))

        if "," in url:
            sku_list = [prod.strip("rcRC ").zfill(6) for prod in url.split(",")]
            list_loop(session, sku_list, filename)
        elif isinstance(url, str):
            product_loop(session, url, filename)


def product_loop(session: WebConnection, url: str, filename: str = ""):
    if not filename:
        filename = generate_filename(url)

    with WriteSpreadsheet(filename) as sheet:
        row = 1
        for product_page in session.generate_product_pages(url):
            product = ProductData(product_page)
            product.assemble_description()

            sheet.write_row(
                row,
                0,
                [product.sku, product.net, product.srp, product.description]
                + product.images,
            )

            if config["General"]["generate_txt_file"] == "True":
                backup_text_file(product.sku, product.description, filename)

            print(
                "Zrobione: {}/{}".format(row, session.product_number),
                end="\t\t\r",
            )
            row += 1
            sleep(0.5)
        print("\nGotowe!\n")


def list_loop(session: WebConnection, lista: list[str], filename: str = ""):
    if not filename:
        filename = check_duplicate_name("lista")

    with WriteSpreadsheet(filename) as sheet:
        row = 1

        for product_page in session.generate_from_list(lista):
            if "noproduct" in product_page.url:
                print(f"Brak produktu: {product_page.url}")
                row += 1
                continue

            product = ProductData(product_page)
            product.assemble_description()

            sheet.write_row(
                row,
                0,
                [product.sku, product.net, product.srp, product.description]
                + product.images,
            )

            if config["General"]["generate_txt_file"] == "True":
                backup_text_file(product.sku, product.description, filename)

            print(
                "Zrobione: {}/{}".format(row, session.product_number),
                end="\t\t\r",
            )
            row += 1
            sleep(2)
        print("\nGotowe!\n")


if __name__ == "__main__":
    main()
