@echo off
title Ojas AI Platform
cd /d "%~dp0"

echo ========================================================
echo        Launching Ojas AI Development Platform
echo ========================================================
echo.

if not exist "runtime\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at runtime\venv!
    echo Please ensure the project runtime is installed.
    pause
    exit /b 1
)

set PYTHONUNBUFFERED=1
runtime\venv\Scripts\python.exe -u run_server.py
if errorlevel 1 (
    echo.
    echo [ERROR] Ojas server exited with error code %errorlevel%.
    pause
)
