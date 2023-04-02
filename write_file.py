import re
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path, PurePath
from traceback import print_exception
from types import TracebackType

from xlsxwriter import Workbook, worksheet

config = ConfigParser()
if not Path("./config.ini").exists():
    raise FileNotFoundError("config.ini file is missing!")
config.read("config.ini")
OUTPUT_PATH = str(Path.expanduser(PurePath(config["General"]["output_path"]))) + "/"


class WriteSpreadsheet:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

    def __enter__(self) -> worksheet:
        self.workbook = Workbook(f"{OUTPUT_PATH}{self.filename}.xlsx")
        self.worksheet = self.workbook.add_worksheet(self.filename)
        self.worksheet.write_row(
            0, 0, ["sku", "Zakup netto", "SRP", "EAN", "Ilość", "Opis", "Zdjęcia ->"]
        )
        return self.worksheet

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        self.workbook.close()
        if exc_type:
            write_log(exc_type, exc_value, exc_trace)


def generate_filename(filename: str, url: str = "") -> str:
    if not filename:
        filename = "arkusz"
    if url:
        try:
            for match in re.search(
                r"-(?:oferty|produktow)-(?>marki-)?([\w-]+)-blog|search\.php\?text=([\w\-\+]+)|product-pol-\d+-(.{20})",
                filename,
            ).group(1, 2, 3):
                if match is not None:
                    filename = match.replace("+", "-")
                    continue
        except AttributeError:
            pass

    filename += "-" + datetime.today().strftime("%d-%m")

    filename = check_duplicate_name(filename)

    return filename


def check_duplicate_name(
    filename: str, path: str = OUTPUT_PATH, extension: str = "xlsx"
) -> str:
    if not filename:
        return ""
    if Path(f"{path}{filename}.{extension}").exists():
        count = 1
        while Path(f"{path}{filename}({count}).{extension}").exists():
            count += 1
        filename += f"({count})"
    return filename


def backup_text_file(sku: str, description: str, filename: str) -> None:
    with open(f"{OUTPUT_PATH}{filename}_opis.txt", "a", encoding="utf8") as txtfile:
        print("-" * 100, file=txtfile)
        print("SKU: " + sku, file=txtfile, end="\n\n")
        print(description, file=txtfile, end="\n\n")


def write_log(
    exc_type: Exception, exc_value: Exception = None, exc_trace: TracebackType = None
):
    with open("./error_log.txt", "a") as log:
        print("-" * 50, file=log, end="\n")
        print(datetime.today().strftime("%d-%m-%Y, %H:%M:%S"), file=log, end="\n\n")
        # print(exc_type, f"({exc_value})", file=log, end="\n")
        print_exception(exc_type, exc_value, exc_trace, file=log)
