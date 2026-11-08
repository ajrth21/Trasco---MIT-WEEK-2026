@echo off
title TRASCO - Complete Ecosystem Launcher
echo ===================================================
echo     TRASCO - AI Cyber Guardian Full Stack
echo ===================================================
echo [1/2] Menjalankan Threat Intelligence Backend Server...
start "TRASCO Backend Engine" cmd /k "cd apps\backend && python -m app.flask_app"

echo [2/2] Membuka Security Analytics Dashboard...
timeout /t 2 /nobreak >nul
start "" "%~dp0apps\dashboard\standalone_dashboard.html"

echo.
echo ===================================================
echo   TRASCO Ecosystem Siap!
echo   - Backend API: http://127.0.0.1:8000
echo   - Dashboard:   standalone_dashboard.html
echo   - Extension:   Muat folder apps\extension di chrome://extensions
echo ===================================================
timeout /t 5
exit

