@echo off
title Trading Intelligence Dashboard
echo Starting Trading Intelligence Dashboard...

:: Force UTF-8 encoding for console output and python subprocess pipelines
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
chcp 65001 > nul

:: Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo [OK] Virtual environment found. Activating...
    call .venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment .venv not found.
    echo Please run 'python install.py' first to set up the environment.
    pause
    exit /b 1
)

:: Run Flask App
echo [OK] Starting Flask server on Port 5050...
echo Access the dashboard at: http://localhost:5050
echo Press Ctrl+C in this window to stop the server.
echo.

python dashboard/app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERR] Dashboard exited with error code %errorlevel%
    pause
)
