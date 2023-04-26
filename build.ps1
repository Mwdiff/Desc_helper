$env:PLAYWRIGHT_BROWSERS_PATH="0"
playwright install --with-deps chromium

pyinstaller --clean --noconfirm --onedir -n DescHelper --add-data "config.ini;." --add-data "C:\Users\hande\AppData\Roaming\Python\Python311\site-packages\customtkinter;.\customtkinter\" main.py