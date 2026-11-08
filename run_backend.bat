@echo off
title TRASCO Threat Intelligence Backend
echo ===================================================
echo   TRASCO - AI Cyber Threat Intelligence Backend
echo ===================================================
echo [INFO] Menjalankan backend server pada http://127.0.0.1:8000 ...
cd apps\backend
python -m app.flask_app
pause

