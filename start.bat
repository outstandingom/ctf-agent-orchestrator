@echo off
setlocal enabledelayedexpansion
title CTF AI Orchestrator — Automated Launcher & Setup Manager
color 0b

:: Change working directory to script location
cd /d "%~dp0"

echo ========================================================================
echo   __  ____  _____     _    ___    ___           _               _             
echo  / _ ^|_   _^|^|  ___^|   / \  ^|_ _^|  / _ \ _ __ ___^| ^|__   ___  ___^| ^|_ _ __ ___  
echo ^| ^|    ^| ^|  ^| ^|_     / _ \  ^| ^|  ^| ^| ^| ^| '__/ __^| '_ \ / _ \/ __^| __^| '__/ _ \ 
echo ^| ^|_   ^| ^|  ^|  _^|   / ___ \ ^| ^|  ^| ^|_^| ^| ^| ^| (__^| ^| ^| ^|  __/\__ \ ^|_^| ^| ^| (_) ^|
echo  \___^| ^|_^|  ^|_^|    /_/   \_\___^|  \___/^|_^|  \___^|_^| ^|_^|\___^|^|___/\__^|_^|  \___/ 
echo                                                                               
echo               Unified Autonomous Command Center (v2.0)
echo ========================================================================
echo.

:: 1. Check Python Availability
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python is not found in your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check Git Availability
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Git was not found in PATH.
    echo Repository cloning will be disabled until Git is installed.
    echo.
)

:: 3. Launch Interactive Python Setup & Launcher Wizard
if exist "scripts\setup_wizard.py" (
    python scripts\setup_wizard.py %*
) else (
    echo [INFO] Launching server directly on port 8080...
    python -m uvicorn server:app --host 0.0.0.0 --port 8080
)

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Process finished with exit code %errorlevel%.
)

endlocal
