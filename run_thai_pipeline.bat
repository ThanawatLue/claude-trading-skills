@echo off
setlocal
cd /d "%~dp0"

echo =========================================================
echo Starting Thai Market Daily Routine Pipeline
echo =========================================================

if exist .venv\Scripts\python.exe (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" scripts\run_thai_market_daily.py %*
pause
