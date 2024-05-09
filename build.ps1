$env:PLAYWRIGHT_BROWSERS_PATH="0"
python -m playwright install --with-deps chromium

python -m PyInstaller --clean --noconfirm --onedir -n DescHelper --add-data "config.ini;." --add-data "C:\Users\USER\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\customtkinter;.\customtkinter\" main.py