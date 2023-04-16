#!C:\Users\hande\Documents\Python scripts\Desc_helper-master\desc_helper_venv\Scripts\python

from get_html import WebConnection
from gui_root import MainWindow
from write_file import *

config = ConfigParser()
config.read("config.ini")


def main():
    session = WebConnection(config["Login"]["login_url"], dict(config["Login_data"]))

    window = MainWindow(session)

    window.mainloop()

    window.loop.close()


if __name__ == "__main__":
    main()
