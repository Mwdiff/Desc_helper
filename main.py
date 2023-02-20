#!C:\Users\hande\Documents\Python scripts\Desc_helper-master\desc_helper_venv\Scripts\python

from time import sleep

from get_html import WebConnection
from gui_root import MainWindow
from product_data import ProductData
from write_file import *

config = ConfigParser()
config.read("config.ini")

# todo GUI


def main():
    window = MainWindow()
    window.mainloop()

    # while session:
    #     url = input("Podaj adres www dostawy: ")
    #     if not url:
    #         print("Zakończono")
    #         return

    #     filename = check_duplicate_name(input("Podaj nazwę pliku: "))

    #     if "," in url:
    #         sku_list = [prod.strip("rcRC ").zfill(6) for prod in url.split(",")]
    #         list_loop(session, sku_list, filename)
    #     else:
    #         product_loop(session, url, filename)


def product_loop(session: WebConnection, url: str, filename: str = ""):
    if not filename:
        filename = generate_filename(url)

    with WriteSpreadsheet(filename) as sheet:
        row = 1
        for product_page in session.generate_product_pages(url):
            try:
                product = ProductData(product_page)
            except AttributeError:
                continue
            product.assemble_description()

            sheet.write_row(
                row,
                0,
                [
                    product.sku,
                    product.net,
                    product.srp,
                    product.qty,
                    product.description,
                ]
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

            try:
                product = ProductData(product_page)
            except AttributeError:
                continue

            product.assemble_description()

            sheet.write_row(
                row,
                0,
                [
                    product.sku,
                    product.net,
                    product.srp,
                    product.qty,
                    product.description,
                ]
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


if __name__ == "__main__":
    main()
