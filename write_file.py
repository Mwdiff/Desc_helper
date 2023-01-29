import re
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path

from xlsxwriter import Workbook, worksheet

config = ConfigParser()
config.read("config.ini")
OUTPUT_PATH = config["General"]["output_path"]


class WriteSpreadsheet:
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def __enter__(self) -> worksheet:
        self.workbook = Workbook(f"{OUTPUT_PATH}{self.filename}.xlsx")
        self.worksheet = self.workbook.add_worksheet(self.filename)
        self.worksheet.write_row(
            0, 0, ["sku", "Zakup netto", "SRP", "Opis", "Zdjęcia ->"]
        )
        return self.worksheet

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        self.workbook.close()


def generate_filename(url: str) -> str:
    filename = "arkusz"
    for match in re.search(
        r"-marki-(\w+)-|search\.php\?text=(\w+)|product-pol-\d+-(.{20})", url
    ).group(1, 2, 3):
        if match is not None:
            filename = match.replace("+", "-")

    filename += "-" + datetime.today().strftime("%d-%m")

    if Path(f"{OUTPUT_PATH}{filename}.xlsx").exists():
        count = 1
        while Path(f"{OUTPUT_PATH}{filename}({count}).xlsx").exists():
            count += 1
        filename = filename + f"({count})"

    return filename


def backup_text_file(sku: str, description: str, filename: str) -> None:
    with open(f"{OUTPUT_PATH}{filename}_opis.txt", "a", encoding="utf8") as txtfile:
        print("-" * 100, file=txtfile)
        print("SKU: " + sku, file=txtfile, end="\n\n")
        print(description, file=txtfile, end="\n\n")
