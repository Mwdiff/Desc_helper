from configparser import ConfigParser

import customtkinter as ctk

from get_html import WebConnection
from gui_list_module import ListModuleFrame
from gui_product_module import ProductModuleFrame

config = ConfigParser()
config.read("config.ini")

# def process_inputs(input1, input2, progress_fun):
#     count = 0
#     for i in range(int(input1), int(input2)):
#         progress_fun(i / (int(input2) - 1))
#         sleep(0.1)
#         count += 1
#     return f"The process finished successfully, count={count}"


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

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


class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.session = WebConnection(
            config["Login"]["login_url"], dict(config["Login_data"])
        )

        # create tabs
        self.add("Opisy z url")
        self.add("Opisy z listy")

        # add widgets on tabs
        self.frame1 = ProductModuleFrame(
            self.session, master=self.tab("Opisy z url"), width=800, height=600
        )
        self.frame1.pack(padx=10, pady=10, expand=0, fill="both")

        self.frame2 = ListModuleFrame(
            self.session, master=self.tab("Opisy z listy"), width=800, height=600
        )
        self.frame2.pack(padx=10, pady=10, expand=0, fill="both")
