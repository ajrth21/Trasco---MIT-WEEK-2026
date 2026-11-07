# TRASCO Full Ecosystem Launcher (PowerShell)
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    TRASCO - AI Cyber Guardian Full Stack" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# 1. Launch Backend
Write-Host "[1/2] Menjalankan Threat Intelligence Backend Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\apps\backend'; python -m app.flask_app"

# 2. Wait and open Dashboard
Start-Sleep -Seconds 2
Write-Host "[2/2] Membuka Security Analytics Dashboard..." -ForegroundColor Green
$dashboardPath = Join-Path $PSScriptRoot "apps\dashboard\standalone_dashboard.html"
Start-Process $dashboardPath

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  TRASCO Ecosystem Aktif!" -ForegroundColor Green
Write-Host "  - Backend API: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  - Dashboard:   standalone_dashboard.html" -ForegroundColor White
Write-Host "  - Extension:   Muat apps\extension di chrome://extensions" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan

