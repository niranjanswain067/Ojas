@echo off
title Ojas AI Platform
cd /d "%~dp0"

echo ========================================================
echo        Launching Ojas AI Development Platform
echo ========================================================
echo.

if not exist "runtime\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at runtime\venv!
    pause
    exit /b 1
)

echo [INFO] Starting Ojas server at http://127.0.0.1:8000 ...
echo [INFO] Serving FastAPI Backend API and compiled React Frontend.
echo.

start http://127.0.0.1:8000
runtime\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
pause
