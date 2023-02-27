import asyncio
from configparser import ConfigParser

import customtkinter as ctk

from desc_modules import product_loop
from get_html import WebConnection
from write_file import generate_filename

config = ConfigParser()
config.read("config.ini")


class ProductModuleFrame(ctk.CTkFrame):
    def __init__(
        self,
        web_session: WebConnection,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5), minsize=40, weight=1)

        self.label_font = ctk.CTkFont(size=15, weight="bold")
        self.label_font_light = ctk.CTkFont(size=13)

        self.input_label_1 = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Adres strony dostawy produktu lub wyszukiwania:",
        )
        self.input_label_1.grid(
            row=0, column=0, padx=20, pady=(20, 5), columnspan=2, sticky="nsw"
        )

        self.url_input = ctk.CTkEntry(self)
        self.url_input.grid(
            row=1, column=0, padx=20, pady=(0, 10), columnspan=2, sticky="nsew"
        )

        self.input_label_2 = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Nazwa pliku:",
        )
        self.input_label_2.grid(row=2, column=0, padx=20, pady=(0, 5), sticky="nsw")

        self.filename_label = ctk.CTkLabel(
            self,
            font=self.label_font_light,
            text="Domyślna nazwa: ",
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
            pady=(0, 20),
            columnspan=1,
            sticky="nswe",
        )

        self.submit_button = ctk.CTkButton(
            self,
            text="Generuj",
            width=120,
            font=self.label_font,
            command=lambda: asyncio.create_task(self.run()),
        )
        self.submit_button.grid(
            row=3, column=1, padx=(0, 20), pady=(0, 20), sticky="nsew"
        )

        self.progress_bar = ctk.CTkProgressBar(self, height=20)
        self.progress_bar.grid(
            row=4, column=0, padx=20, pady=(0, 20), columnspan=2, sticky="nsew"
        )
        self.progress_bar.set(0)

        self.output_field = ctk.CTkLabel(
            self, text_color="black", bg_color="gray", text=""
        )
        self.output_field.grid(
            row=5, column=0, padx=20, pady=(0, 20), columnspan=2, sticky="nsew"
        )
        self.session = web_session
        self.after(100, self.label_updater)

    async def run(self):
        self.output_field.configure(text="Pracuję...")
        self.progress_bar.set(0)
        url = self.url_input.get()
        filename = self.filename_input.get()
        result = await asyncio.to_thread(
            product_loop,
            self.session,
            url,
            filename,
            self.update_progressbar,
            asyncio.get_event_loop(),
        )

        self.output_field.configure(text=f"Utworzono plik {result}")
        self.after(100, self.label_updater)

    def label_updater(self):
        self.filename_label.configure(
            True,
            text=f"Domyślna nazwa: '{generate_filename(self.url_input.get())}'",
        )
        self.after(100, self.label_updater)

    async def update_progressbar(self, current, total):
        self.progress_bar.set(current / total)
        self.output_field.configure(text=f"Pracuję... {current}/{total}")
