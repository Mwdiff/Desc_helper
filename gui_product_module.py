import asyncio
from configparser import ConfigParser
from datetime import datetime
from os import remove, startfile

import customtkinter as ctk
from windows_toasts import (
    InteractableWindowsToaster,
    ToastButton,
    ToastDisplayImage,
    ToastImageAndText1,
)

from desc_modules import product_loop
from get_html import WebConnection
from gui_listbox import CTkListbox
from write_file import OUTPUT_PATH

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

        self.result = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((3, 5), minsize=40, weight=1)
        self.grid_rowconfigure((1, 2, 4, 6), minsize=40, weight=1)
        self.grid_rowconfigure((0, 7), minsize=60, weight=1)

        self.label_font = ctk.CTkFont(size=15, weight="bold")
        self.label_font_light = ctk.CTkFont(size=13)

        self.news_label = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Aktualności:",
        )
        self.news_label.grid(
            row=0, column=0, padx=20, pady=(20, 10), columnspan=2, sticky="nsw"
        )

        self.notification_toggle = ctk.CTkCheckBox(self, text="Powiadomienia", width=50)
        self.notification_toggle.grid(
            row=0, column=1, padx=(0, 130), pady=(20, 10), sticky="nse"
        )

        self.refresh_button = ctk.CTkButton(
            self,
            text="Odśwież",
            width=50,
            font=self.label_font,
            command=self.news_refresh,
        )
        self.refresh_button.grid(
            row=0, column=1, padx=(0, 20), pady=(20, 10), sticky="nse"
        )

        self.news_list = web_session.get_news_list()
        news_str = [f"{news['date']}   —   {news['title']}" for news in self.news_list]
        self.news_list_listbox = CTkListbox(
            self, news_str, self.list_select, width=760, height=250
        )
        self.news_list_listbox.grid(
            row=1, column=0, padx=20, pady=(0, 10), columnspan=2, sticky="nsew"
        )

        self.input_label_1 = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Adres strony dostawy produktu lub wyszukiwania:",
        )
        self.input_label_1.grid(
            row=2, column=0, padx=20, pady=(10, 5), columnspan=2, sticky="nsw"
        )

        self.url_input = ctk.CTkEntry(self)
        self.url_input.grid(
            row=3, column=0, padx=20, pady=(0, 10), columnspan=2, sticky="nsew"
        )

        self.input_label_2 = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Nazwa pliku:",
        )
        self.input_label_2.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="nsw")

        ##        self.filename_label = ctk.CTkLabel(
        ##            self,
        ##            font=self.label_font_light,
        ##            text="Domyślna nazwa",
        ##        )
        ##        self.filename_label.grid(
        ##            row=4, column=0, padx=(150, 20), pady=(0, 5), sticky="nse"
        ##        )

        self.filename_input = ctk.CTkEntry(
            self, placeholder_text="Pozostaw puste dla nazwy domyślnej"
        )
        self.filename_input.grid(
            row=5,
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
            command=lambda: asyncio.create_task(self.run()),
        )
        self.submit_button.grid(
            row=5, column=1, padx=(0, 20), pady=(0, 10), sticky="nsew"
        )

        self.progress_bar = ctk.CTkProgressBar(self, height=20)
        self.progress_bar.grid(
            row=6, column=0, padx=20, pady=(10, 10), columnspan=2, sticky="nsew"
        )
        self.progress_bar.set(0)

        self.output_field = ctk.CTkLabel(
            self, text_color="black", bg_color="gray", text=""
        )
        self.output_field.grid(
            row=7, column=0, padx=(20, 80), pady=(10, 20), columnspan=2, sticky="nsew"
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
            row=7, column=1, padx=(0, 20), pady=(10, 20), sticky="nse"
        )
        self.loop = asyncio.get_event_loop()
        self.session = web_session
        ##        self.after(100, self.label_updater)
        self.after(300000, self.auto_refresh)

    async def run(self):
        self.output_field.configure(text="Pracuję...")
        self.progress_bar.set(0)
        url = self.url_input.get()
        filename = self.filename_input.get()
        task = asyncio.create_task(
            product_loop(
                self.session,
                url,
                filename,
                self.update_progressbar,
            )
        )
        self.submit_button.configure(text="Anuluj", command=lambda: task.cancel())
        try:
            self.result = await task
        except asyncio.CancelledError:
            self.output_field.configure(text=f"Anulowano proces")
            remove(OUTPUT_PATH + "temp.xlsx")
            return
        finally:
            self.submit_button.configure(
                text="Generuj", command=lambda: asyncio.create_task(self.run())
            )
            self.progress_bar.set(0)

        self.open_button.configure(state="normal")
        self.output_field.configure(text=f"Utworzono plik {self.result}")

    ##        self.after(100, self.label_updater)

    ##    def label_updater(self):
    ##        self.filename_label.configure(
    ##            True,
    ##            text=f"Domyślna nazwa: '{generate_filename(self.url_input.get())}'",
    ##        )
    ##        self.after(100, self.label_updater)

    async def update_progressbar(self, current, total):
        self.progress_bar.set(current / total)
        self.output_field.configure(text=f"Pracuję... {current}/{total}")
        await asyncio.sleep(0)

    def open_file(self):
        filepath = OUTPUT_PATH
        startfile(f"{filepath}{self.result}")

    def list_select(self, selection: tuple[int]):
        self.url_input.delete(0, "end")
        self.url_input.insert(0, self.news_list[selection[0]]["url"])

    def news_refresh(self):
        self.news_list = self.session.get_news_list()
        news_str = [f"{news['date']}   —   {news['title']}" for news in self.news_list]
        self.news_list_listbox.refresh(
            item_list=news_str, notify_function=self.toast_notification
        )
        self.output_field.configure(
            text=f"Zaktualizowano newsy: {datetime.now().strftime('%H:%M')}"
        )

    def auto_refresh(self):
        self.news_refresh()
        self.after(300000, self.auto_refresh)

    def toast_notification(self, index: int):
        if not self.notification_toggle.get():
            return
        toaster = InteractableWindowsToaster("Dostawa")
        newToast = ToastImageAndText1()
        title = self.news_list[index]["title"]
        url = self.news_list[index]["url"]

        newToast.SetBody(title)
        img = self.session.get_article_image(url.split("-")[-1].strip(".html"))
        newToast.AddImage(
            ToastDisplayImage.fromPath(
                img,
                circleCrop=False,
                large=True,
            )
        )
        newToast.AddAction(ToastButton("Ok"))
        toaster.show_toast(newToast)
        self.after(1000, remove, img)
