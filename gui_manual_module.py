import asyncio
from configparser import ConfigParser
from os import startfile
from pathlib import Path
from string import Template

import customtkinter as ctk

from product_data import ProductData
from write_file import OUTPUT_PATH, WriteSpreadsheet, check_duplicate_name

config = ConfigParser()
config.read("config.ini")

DUMMY_HTML = Template("""<html><body>
<div class="product_codes">
    <span>SKU</span><span>$sku</span>
    <span>Kod EAN</span><span>$ean</span>
    <span>Kod producenta</span><span>$prodno</span>
</div>
<div class="projector_prices">
    <span class="projector_prices__srp netto">$net</span>
    <span class="projector_prices__srp black mr-1">$srp</span>
</div>
<span class="search_versions__status_amount_mw big_avail">$qty</span>
<a class="firm_logo" href="/firm-pol-0-$brand.html"></a>
<section id="projector_longdescription">
    $description
</section>
</body></html>""")


class ManualModuleFrame(ctk.CTkFrame):
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.result = ""
        self.loop = loop
        self.products: list[ProductData] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure((0, 2, 3, 4, 5, 6), weight=0)

        self.label_font = ctk.CTkFont(size=15, weight="bold")
        self.label_font_light = ctk.CTkFont(size=13)

        self.load_elements()

    def load_elements(self):
        self.input_label_1 = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Opis produktu (HTML):",
        )
        self.input_label_1.grid(
            row=0, column=0, padx=20, pady=(20, 5), columnspan=2, sticky="nsw"
        )

        self.description_input = ctk.CTkTextbox(self, height=250, border_width=2)
        self.description_input.grid(
            row=1, column=0, padx=20, pady=(0, 10), columnspan=2, sticky="nsew"
        )

        self.brand_label = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Marka:",
        )
        self.brand_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="nsw")

        self.new_template_toggle = ctk.CTkCheckBox(self, text="Nowy szablon", width=50)
        if config.get("General", "new_template", fallback=False):
            self.new_template_toggle.select()
        self.new_template_toggle.grid(
            row=2, column=1, padx=(0, 20), pady=(10, 10), sticky="nse"
        )

        self.brand_input = ctk.CTkEntry(self, placeholder_text="Nazwa marki")
        self.brand_input.grid(
            row=3, column=0, padx=20, pady=(0, 10), sticky="nswe"
        )

        # EAN + Product code + Filename row
        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.grid(
            row=4, column=0, padx=20, pady=(0, 10), columnspan=2, sticky="nswe"
        )
        self.details_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.ean_label = ctk.CTkLabel(
            self.details_frame, font=self.label_font_light, text="EAN:"
        )
        self.ean_label.grid(row=0, column=0, sticky="w")
        self.ean_input = ctk.CTkEntry(
            self.details_frame, placeholder_text="(opcjonalnie)"
        )
        self.ean_input.grid(row=1, column=0, padx=(0, 5), sticky="we")

        self.prodno_label = ctk.CTkLabel(
            self.details_frame, font=self.label_font_light, text="Kod producenta:"
        )
        self.prodno_label.grid(row=0, column=1, sticky="w")
        self.prodno_input = ctk.CTkEntry(
            self.details_frame, placeholder_text="(opcjonalnie)"
        )
        self.prodno_input.grid(row=1, column=1, padx=5, sticky="we")

        self.filename_label = ctk.CTkLabel(
            self.details_frame, font=self.label_font_light, text="Nazwa pliku:"
        )
        self.filename_label.grid(row=0, column=2, sticky="w")
        self.filename_input = ctk.CTkEntry(
            self.details_frame, placeholder_text="(opcjonalnie)"
        )
        self.filename_input.grid(row=1, column=2, padx=(5, 0), sticky="we")

        # Buttons row
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.grid(
            row=3, column=1, padx=(0, 20), pady=(0, 10), sticky="nse"
        )

        self.copy_button = ctk.CTkButton(
            self.buttons_frame,
            text="Kopiuj opis",
            width=100,
            font=self.label_font,
            command=self.generate_and_copy,
        )
        self.copy_button.pack(side="left", padx=(5, 5))

        self.add_button = ctk.CTkButton(
            self.buttons_frame,
            text="Dodaj",
            width=80,
            font=self.label_font,
            command=self.add_to_list,
        )
        self.add_button.pack(side="left", padx=(0, 0))

        # Bottom row
        self.queue_label = ctk.CTkLabel(
            self,
            font=self.label_font_light,
            text="W kolejce: 0",
        )
        self.queue_label.grid(
            row=5, column=0, padx=20, pady=(10, 20), sticky="nsw"
        )

        self.clear_button = ctk.CTkButton(
            self,
            text="Wyczyść",
            width=80,
            font=self.label_font_light,
            command=self.clear_list,
        )
        self.clear_button.grid(
            row=5, column=0, padx=(120, 0), pady=(10, 20), sticky="nsw"
        )

        self.spreadsheet_button = ctk.CTkButton(
            self,
            text="Generuj arkusz",
            width=140,
            font=self.label_font,
            command=self.generate_spreadsheet,
        )
        self.spreadsheet_button.grid(
            row=5, column=1, padx=(0, 20), pady=(10, 20), sticky="nse"
        )

        self.output_field = ctk.CTkLabel(
            self, text_color="black", bg_color="gray", text=""
        )
        self.output_field.grid(
            row=6, column=0, padx=(20, 80), pady=(0, 20), columnspan=2, sticky="nsew"
        )

        self.open_button = ctk.CTkButton(
            self,
            text="Otwórz ",
            width=42,
            font=self.label_font,
            corner_radius=0,
            command=self.open_file,
            state="disabled",
        )
        self.open_button.grid(
            row=6, column=1, padx=(0, 50), pady=(0, 20), sticky="nse"
        )

        self.open_folder_button = ctk.CTkButton(
            self,
            text="📂",
            width=25,
            font=self.label_font,
            corner_radius=0,
            command=self.open_folder,
        )
        self.open_folder_button.grid(
            row=6, column=1, padx=(0, 20), pady=(0, 20), sticky="nse"
        )

    def _build_product(self) -> ProductData | None:
        raw_desc = self.description_input.get("0.0", "end").strip()
        if not raw_desc:
            return None

        html = DUMMY_HTML.substitute(
            sku="",
            ean=self.ean_input.get().strip(),
            prodno=self.prodno_input.get().strip(),
            net="",
            srp="",
            qty="",
            brand=self.brand_input.get().strip(),
            description=raw_desc,
        )

        product = ProductData(html.encode("utf-8"))
        try:
            product.initialize_description()
        except AttributeError:
            pass
        else:
            if self.new_template_toggle.get():
                product.assemble_description_new()
            else:
                product.assemble_description()

        return product

    def _clear_inputs(self):
        self.description_input.delete("0.0", "end")
        self.ean_input.delete(0, "end")
        self.prodno_input.delete(0, "end")

    def _update_queue_label(self):
        self.queue_label.configure(text=f"W kolejce: {len(self.products)}")

    def add_to_list(self):
        product = self._build_product()
        if not product or not getattr(product, "description", ""):
            self.output_field.configure(text="Brak opisu do dodania!")
            return

        self.products.append(product)
        self._update_queue_label()
        self._clear_inputs()
        self.output_field.configure(text=f"Dodano opis ({len(self.products)} w kolejce)")

    def clear_list(self):
        self.products.clear()
        self._update_queue_label()
        self.output_field.configure(text="Wyczyszczono kolejkę")

    def generate_and_copy(self):
        product = self._build_product()
        if not product or not getattr(product, "description", ""):
            self.output_field.configure(text="Brak opisu do skopiowania!")
            return

        self.clipboard_clear()
        self.clipboard_append(product.description)
        self.output_field.configure(text="Skopiowano opis do schowka!")

    def generate_spreadsheet(self):
        # If there's a current description in the input, add it to the list first
        current = self._build_product()
        if current and getattr(current, "description", ""):
            self.products.append(current)

        if not self.products:
            self.output_field.configure(text="Brak opisów do wygenerowania!")
            return

        filename = self.filename_input.get().strip()
        if not filename:
            filename = self.brand_input.get().strip() or "reczny"
        filename = check_duplicate_name(filename)

        with WriteSpreadsheet(filename) as sheet:
            for row, product in enumerate(self.products, start=1):
                sheet.write_row(
                    row,
                    0,
                    [
                        product.ean,
                        product.net,
                        product.srp,
                        product.prodno,
                        product.brand,
                        product.qty,
                        product.description,
                        product.safety_file,
                    ],
                )

        self.result = f"{filename}.xlsx"
        count = len(self.products)
        self.products.clear()
        self._update_queue_label()
        self._clear_inputs()
        self.open_button.configure(state="normal")
        self.output_field.configure(
            text=f"Utworzono plik {self.result} ({count} opisów)"
        )

    def open_file(self):
        filepath = Path(OUTPUT_PATH)
        startfile(filepath / self.result)

    def open_folder(self):
        filepath = Path(OUTPUT_PATH)
        startfile(filepath)
