@echo off
REM Run this from the project folder (the one that contains desktop.py).
if not exist .venv (
  py -3.12 -m venv .venv || py -3 -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Optional: put an app.ico in this folder and it becomes the exe icon.
set ICON=
if exist app.ico set ICON=--icon app.ico

pyinstaller --noconfirm --clean --windowed --onedir --name DevOpsTracker ^
  --add-data "templates;templates" --add-data "static;static" %ICON% desktop.py

echo.
echo Done. Your app is in dist\DevOpsTracker\DevOpsTracker.exe
pause
