import asyncio
from configparser import ConfigParser
from os import rename
from time import perf_counter

from requests import Response
from xlsxwriter import worksheet

from get_html import WebConnection
from product_data import ProductData
from write_file import (
    OUTPUT_PATH,
    WriteSpreadsheet,
    backup_text_file,
    check_duplicate_name,
    generate_filename,
)

config = ConfigParser()
config.read("config.ini")


async def generate_data(
    session: WebConnection,
    url: str = "",
    list: list[str] = [],
    filename: str = "",
    progress_function=None,
    mode: str = "product",
) -> str:
    t_start = perf_counter()

    match mode:
        case "product":
            generate = session.generate_product_pages(url)
        case "list":
            generate = session.generate_from_list(list)

    with WriteSpreadsheet("temp") as sheet:
        row = 1
        await asyncio.sleep(0)
        for product_page in generate:
            if "noproduct" in product_page.url:
                print(f"Brak produktu: {product_page.url}")
                row += 1
                continue

            await write_row(sheet, product_page, row, filename)

            if asyncio.current_task().cancelled():
                print("cancelled")
                return

            await progress_function(row, session.product_number)
            await asyncio.sleep(0)

            row += 1
    t_end = perf_counter()

    match mode:
        case "product":
            if not filename and session.producent:
                filename = session.producent
            filename = generate_filename(filename, url)
        case "list":
            if not filename:
                filename = "lista"
            filename = check_duplicate_name(filename)

    rename(OUTPUT_PATH + "temp.xlsx", OUTPUT_PATH + f"{filename}.xlsx")

    print(f"Wykonano w czasie: {t_end-t_start}")
    return filename + ".xlsx"


# async def list_loop(
#     session: WebConnection,
#     lista: list[str],
#     filename: str = "",
#     progress_function=None,
# ) -> str:
#     t_start = perf_counter()
#     if not filename:
#         filename = "lista"
#     filename = check_duplicate_name(filename)

#     with WriteSpreadsheet(filename) as sheet:
#         row = 1
#         await asyncio.sleep(0)
#         for product_page in session.generate_from_list(lista):
#             if "noproduct" in product_page.url:
#                 print(f"Brak produktu: {product_page.url}")
#                 row += 1
#                 continue

#             await write_row(sheet, product_page, row, filename)

#             if asyncio.current_task().cancelled():
#                 print("cancelled")
#                 return

#             await progress_function(row, session.product_number)
#             await asyncio.sleep(0)

#             row += 1
#     t_end = perf_counter()
#     print(f"Wykonano w czasie: {t_end-t_start}")
#     return filename + ".xlsx"


async def write_row(
    sheet: worksheet, product_page: Response, row: int, filename: str
) -> None:
    try:
        product = ProductData(product_page)
    except AttributeError:
        return

    await asyncio.sleep(0)

    try:
        product.initialize_description()
    except AttributeError:
        pass
    else:
        product.assemble_description()

    await asyncio.sleep(0)

    sheet.write_row(
        row,
        0,
        [
            product.sku,
            product.net,
            product.srp,
            product.ean,
            product.qty,
            product.description,
        ]
        + product.images,
    )
    await asyncio.sleep(0)

    if config["General"]["generate_txt_file"] == "True":
        backup_text_file(product.sku, product.description, filename)
