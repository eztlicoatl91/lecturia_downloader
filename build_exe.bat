@echo off
echo ========================================================
echo   Compilando Lecturia Downloader a ejecutable .EXE
echo ========================================================

call .venv\Scripts\activate.bat
pyinstaller --name "LecturiaDownloader" --onefile --collect-all ebooklib --collect-all bs4 --collect-all PIL app_local.py

echo.
echo ========================================================
echo   Compilacion finalizada!
echo   El ejecutable se encuentra en: dist\LecturiaDownloader.exe
echo ========================================================
pause
