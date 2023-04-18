#!C:\Users\hande\Documents\Python scripts\Desc_helper-master\desc_helper_venv\Scripts\python

from asyncio import sleep

from gui_root import MainWindow
from write_file import *

config = ConfigParser()
config.read("config.ini")


def main():
    window = MainWindow()

    window.mainloop()

    window.loop.run_until_complete(window.session.close())
    window.loop.run_until_complete(sleep(0))
    window.loop.close()


if __name__ == "__main__":
    main()
