import asyncio
from configparser import ConfigParser

import customtkinter as ctk

from get_html import WebConnection
from gui_list_module import ListModuleFrame
from gui_product_module import ProductModuleFrame

config = ConfigParser()
config.read("config.ini")


class MainWindow(ctk.CTk):
    def __init__(self, session: WebConnection):
        super().__init__()

        self.session = session
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.geometry("800x600")
        self.title("Generator opisów")
        self.minsize(470, 320)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # self.grid_rowconfigure(1, weight=1)

        ctk.set_appearance_mode(config["GUI"]["theme"])
        ctk.set_default_color_theme(config["GUI"]["color_theme"])

        self.tabs = MyTabView(self)
        self.tabs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # self.frame1 = ProductModuleFrame(self.session, self)
        # self.frame1.grid(row=1, column=0, padx=20, pady=10, sticky="new")

    async def show(self):
        self.open = True
        while self.open:
            self.update()
            await asyncio.sleep(0.05)

    def close(self):
        self.open = False


class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # create tabs
        self.add("Opisy z url")
        self.add("Opisy z listy")

        # add widgets on tabs
        self.frame1 = ProductModuleFrame(
            master.session,
            master=self.tab("Opisy z url"),
            width=800,
            height=600,
        )
        self.frame1.pack(padx=10, pady=10, expand=0, fill="both")

        self.frame2 = ListModuleFrame(
            master.session, master=self.tab("Opisy z listy"), width=800, height=600
        )
        self.frame2.pack(padx=10, pady=10, expand=0, fill="both")
