import asyncio
from configparser import ConfigParser
from os import remove, startfile

import customtkinter as ctk

from desc_modules import generate_data
from get_html_async import WebConnection
from write_file import OUTPUT_PATH, check_duplicate_name

config = ConfigParser()
config.read("config.ini")


class ListModuleFrame(ctk.CTkFrame):
    def __init__(
        self,
        web_session: WebConnection,
        loop: asyncio.AbstractEventLoop = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.result = ""
        self.loop = loop
        self.session = web_session
        self.task = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5), minsize=40, weight=1)

        self.label_font = ctk.CTkFont(size=15, weight="bold")
        self.label_font_light = ctk.CTkFont(size=13)

        self.load_elements()

    def load_elements(self):
        self.input_label_1 = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Lista produktów SKU lub EAN (separator ','):",
        )
        self.input_label_1.grid(
            row=0, column=0, padx=20, pady=(20, 5), columnspan=2, sticky="nsw"
        )

        self.list_input = ctk.CTkTextbox(self, height=95, border_width=2)
        self.list_input.grid(
            row=1, column=0, padx=20, pady=(0, 10), columnspan=2, sticky="nsew"
        )

        self.input_label_2 = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Nazwa pliku:",
        )
        self.input_label_2.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="nsw")

        self.filename_label = ctk.CTkLabel(
            self,
            font=self.label_font_light,
            text=f"Domyślna nazwa: '{check_duplicate_name('lista')}'",
        )
        self.filename_label.grid(
            row=2, column=0, padx=(150, 20), pady=(0, 5), sticky="nse"
        )

        self.filename_input = ctk.CTkEntry(
            self, placeholder_text="Pozostaw puste dla nazwy domyślnej"
        )
        self.filename_input.grid(
            row=3,
            column=0,
            padx=20,
            pady=(0, 10),
            columnspan=1,
            sticky="nswe",
        )

        self.submit_button = ctk.CTkButton(
            self,
            text="Generuj",
            width=120,
            font=self.label_font,
            command=self.run,
        )
        self.submit_button.grid(
            row=3, column=1, padx=(0, 20), pady=(0, 10), sticky="nsew"
        )

        self.progress_bar = ctk.CTkProgressBar(self, height=20)
        self.progress_bar.grid(
            row=4, column=0, padx=20, pady=(10, 10), columnspan=2, sticky="nsew"
        )
        self.progress_bar.set(0)

        self.output_field = ctk.CTkLabel(
            self, text_color="black", bg_color="gray", text=""
        )
        self.output_field.grid(
            row=5, column=0, padx=(20, 80), pady=(10, 20), columnspan=2, sticky="nsew"
        )

        self.open_button = ctk.CTkButton(
            self,
            text="Otwórz",
            width=40,
            font=self.label_font,
            corner_radius=0,
            command=self.open_file,
            state="disabled",
        )
        self.open_button.grid(
            row=5, column=1, padx=(0, 20), pady=(10, 20), sticky="nse"
        )

    def run(self):
        self.output_field.configure(text="Pracuję...")
        self.progress_bar.set(0)
        product_list = [
            prod.strip("rcRC ").zfill(6)
            for prod in self.list_input.get("0.0", "end").replace("\n", "").replace(",", ";").replace("|", ";").split(";")
            if prod
        ]
        filename = self.filename_input.get()

        async def generate_file():
            self.result = await generate_data(
                self.session,
                list=product_list,
                filename=filename,
                progress_function=self.update_progressbar,
                mode="list",
            )
            self.submit_button.configure(text="Generuj", command=self.run)
            self.progress_bar.set(0)
            self.open_button.configure(state="normal")
            self.output_field.configure(text=f"Utworzono plik {self.result}")

        self.submit_button.configure(text="Anuluj", command=self.cancel_run)
        self.task = self.loop.create_task(generate_file())

    def cancel_run(self):
        if self.task and not self.task.done():
            self.task.cancel()
            self.output_field.configure(text=f"Anulowano proces")
            self.progress_bar.set(0)
            self.submit_button.configure(text="Generuj", command=self.run)
            remove(OUTPUT_PATH + "temp.xlsx")
            

    async def update_progressbar(self, current, total):
        self.progress_bar.set(current / total)
        self.output_field.configure(text=f"Pracuję... {current}/{total}")
        await asyncio.sleep(0)

    def open_file(self):
        filepath = OUTPUT_PATH
        startfile(f"{filepath}{self.result}")
