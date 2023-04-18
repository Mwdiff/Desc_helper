import asyncio
from configparser import ConfigParser
from datetime import datetime
from os import remove, startfile
from time import sleep

import customtkinter as ctk
from windows_toasts import (
    InteractableWindowsToaster,
    ToastActivatedEventArgs,
    ToastButton,
    ToastDisplayImage,
    ToastImageAndText1,
)

from desc_modules import generate_data
from get_html_async import WebConnection
from gui_listbox import CTkListbox
from write_file import OUTPUT_PATH

config = ConfigParser()
config.read("config.ini")


class ProductModuleFrame(ctk.CTkFrame):
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
        self.refresh_task = None
        self.news_list = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((3, 5), minsize=40, weight=1)
        self.grid_rowconfigure((1, 2, 4, 6), minsize=40, weight=1)
        self.grid_rowconfigure((0, 7), minsize=60, weight=1)

        self.label_font = ctk.CTkFont(size=15, weight="bold")
        self.label_font_light = ctk.CTkFont(size=13)

        self.load_elements()
        self.news_refresh()
        self.after(300000, self.auto_refresh)

    def load_elements(self):
        self.news_label = ctk.CTkLabel(
            self,
            font=self.label_font,
            text="Aktualności:",
        )
        self.news_label.grid(
            row=0, column=0, padx=20, pady=(20, 10), columnspan=2, sticky="nsw"
        )

        self.notification_toggle = ctk.CTkCheckBox(self, text="Powiadomienia", width=50)
        self.notification_toggle.select()
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

        self.news_list_listbox = CTkListbox(
            self, [], self.list_select, width=760, height=250
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
            command=self.run,
        )
        self.submit_button.grid(
            row=5, column=1, padx=(0, 20), pady=(0, 10), sticky="nswe"
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

    def run(self):
        self.output_field.configure(text="Pracuję...")
        self.progress_bar.set(0)
        url = self.url_input.get()
        filename = self.filename_input.get()

        async def generate_file():
            self.result = await generate_data(
                self.session,
                url=url,
                filename=filename,
                progress_function=self.update_progressbar,
                mode="product",
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
            remove(OUTPUT_PATH + "temp.xlsx")
            self.submit_button.configure(text="Generuj", command=self.run)

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

    def news_initialize(self):
        self.refresh_task = self.loop.create_task(self.session.get_news_list())
        self.after(1000, self.news_refresh)

    def news_refresh(self):
        if self.refresh_task is None:
            self.news_initialize()
            self.refresh_button.configure(state="disabled")
            self.output_field.configure(text=f"Aktualizuję newsy...")
            return

        if not self.refresh_task.done():
            self.after(1000, self.news_refresh)
            return
        else:
            try:
                self.news_list = self.refresh_task.result()
            except Exception:
                self.output_field.configure(
                    text="BŁĄD: nie udało się pobrać aktualizacji!"
                )
                self.refresh_button.configure(state="normal")
                self.refresh_task = None
                return
            self.refresh_task = None

        news_str = [f"{news['date']}   —   {news['title']}" for news in self.news_list]
        self.news_list_listbox.refresh(
            item_list=news_str, notify_function=self.toast_notification
        )
        self.output_field.configure(
            text=f"Zaktualizowano newsy: {datetime.now().strftime('%H:%M')}"
        )
        self.refresh_button.configure(state="normal")

    def auto_refresh(self):
        self.news_refresh()
        self.after(300000, self.auto_refresh)

    def toast_notification(self, index: int):
        if not self.notification_toggle.get():
            return
        toaster = InteractableWindowsToaster("Dostawa")
        newToast = ToastImageAndText1()
        title = self.news_list[index]["title"]
        url = self.news_list[index]["icon"]

        def activated_callback(activatedEventArgs: ToastActivatedEventArgs):
            if activatedEventArgs.arguments == "open":
                self.focus_force()

        newToast.SetBody(title)
        img = self.session.get_article_image(url)
        newToast.AddImage(
            ToastDisplayImage.fromPath(
                img,
                circleCrop=False,
                large=True,
            )
        )
        newToast.AddAction(ToastButton("Open", "open"))
        newToast.AddAction(ToastButton("Ok", "ok"))
        newToast.on_activated = activated_callback
        toaster.show_toast(newToast)
        self.after(1000, remove, img)
