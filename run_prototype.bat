@echo off
title Ojas AI CLI Prototype
cd /d "%~dp0"

echo ========================================================
echo               Launching Ojas CLI Prototype
echo ========================================================
echo.

if not exist "runtime\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at runtime\venv!
    pause
    exit /b 1
)

runtime\venv\Scripts\python.exe prototype_cli.py
pause

