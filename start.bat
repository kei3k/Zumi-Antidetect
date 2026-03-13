@echo off
title ZUMI ANTIDETECT v3.0
cd /d "%~dp0"

echo ============================================================
echo   ZUMI ANTIDETECT BROWSER MANAGER v3.0
echo   Starting Desktop App...
echo ============================================================

:: Check if customtkinter is installed
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo.
    echo [*] Installing dependencies...
    pip install -r requirements.txt
    echo.
)

python main_app.py
pause
