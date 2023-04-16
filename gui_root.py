import asyncio
from configparser import ConfigParser

import customtkinter as ctk

from get_html import WebConnection
from get_js_enabled import BrowserRequest
from gui_list_module import ListModuleFrame
from gui_product_module import ProductModuleFrame

config = ConfigParser()
config.read("config.ini")


class MainWindow(ctk.CTk):
    def __init__(self, session: WebConnection):
        super().__init__()

        self.session = session
        self.loop = asyncio.get_event_loop_policy().new_event_loop()
        self.after(10, self.run_asyncio_loop)

        self.loop.create_task(BrowserRequest.create_browser_context())

        self.geometry("800x600")
        self.title("Generator opisów")
        self.minsize(470, 320)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # self.grid_rowconfigure(1, weight=1)

        ctk.set_appearance_mode(config["GUI"]["theme"])
        ctk.set_default_color_theme(config["GUI"]["color_theme"])

        self.tabs = MyTabView(self)
        self.tabs.grid(row=0, column=0, padx=10, pady=10, sticky="nswe")

    def run_asyncio_loop(self):
        # Run the event loop in non-blocking mode
        self.loop.run_until_complete(asyncio.sleep(0.1))
        self.after(20, self.run_asyncio_loop)


class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # create tabs
        self.add("  Opisy z url  ")
        self.add("  Opisy z listy  ")

        # add widgets on tabs
        self.frame1 = ProductModuleFrame(
            web_session=master.session,
            loop=master.loop,
            master=self.tab("  Opisy z url  "),
            width=800,
            height=600,
        )
        self.frame1.pack(padx=10, pady=10, expand=0, fill="both")

        self.frame2 = ListModuleFrame(
            web_session=master.session,
            loop=master.loop,
            master=self.tab("  Opisy z listy  "),
            width=800,
            height=600,
        )
        self.frame2.pack(padx=10, pady=10, expand=0, fill="both")
