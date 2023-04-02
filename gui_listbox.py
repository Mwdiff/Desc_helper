from time import sleep
from tkinter import Listbox, StringVar
from typing import Callable

import customtkinter as ctk


class CTkListbox(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        item_list: list[str],
        on_select_function: Callable[[int], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)

        self.new = set()

        listbox_params = {
            "borderwidth": 5,
            "relief": "flat",
            "activestyle": "none",
            "font": "'Roboto' 13 normal",
        }

        listbox_style_dark = {
            "bg": "gray20",
            "fg": "gray84",
            "selectbackground": "#1f538d",
        }

        listbox_style_light = {
            "bg": "gray100",
            "fg": "gray14",
            "selectbackground": "#3a7ebf",
        }

        self.listbox_style = listbox_style_light
        if ctk.get_appearance_mode() == "Dark":
            self.listbox_style = listbox_style_dark

        self.items = item_list
        self.listbox = Listbox(
            self,
            height=len(item_list),
            listvariable=StringVar(value=self.items),
            width=int(master.cget("width")) - 20,
            **listbox_params,
            **self.listbox_style,
        )
        self.listbox.pack(padx=(10, 0))

        self.listbox.bind(
            "<<ListboxSelect>>",
            lambda e: on_select_function(self.listbox.curselection()),
        )

    def refresh(self, item_list, notify_function: Callable[[int], None] = None):
        new_added = set(item_list) - set(self.items)
        self.new = self.new | new_added
        self.items = item_list

        for article in new_added:
            notify_function(self.items.index(article))
            sleep(5)
        
        self.listbox.configure(
            **self.listbox_style, listvariable=StringVar(value=self.items)
        )
        for i, item in enumerate(self.items):
            if item in self.new:
                self.listbox.itemconfigure(i, background="#3a9c85")
            else:
                self.listbox.itemconfigure(i, **self.listbox_style)
