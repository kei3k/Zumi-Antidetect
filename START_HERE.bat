@echo off
title Zumi Antidetect Dashboard - 60 Kênh YouTube
color 0A

echo =====================================================
echo   ZUMI ANTIDECTECT DASHBOARD - STARTING...
echo   60 Profile YouTube Automation
echo =====================================================
echo.

:: Start Backend (API Server)
echo [1/2] Starting Backend API Server...
start "Zumi Backend" cmd /k "cd /d D:\K\Zumi-Antidetect\scripts && python api_server.py"
timeout /t 3 /nobreak >nul

:: Start Frontend (React Dashboard)
echo [2/2] Starting Frontend Dashboard...
start "Zumi Dashboard" cmd /k "cd /d D:\K\Zumi-Antidetect\dashboard && npm run dev"

echo.
echo =====================================================
echo   Dashboard is running!
echo   Open: http://localhost:5173
echo   API: http://localhost:8001
echo =====================================================
echo.
echo Press any key to exit this window...
pause >nul
