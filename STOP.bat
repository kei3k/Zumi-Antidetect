@echo off
echo Stopping Zumi Antidetect Dashboard...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Zumi Backend*" 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Zumi Dashboard*" 2>nul
echo Done!
timeout /t 2 /nobreak >nul
