@echo off
setlocal enabledelayedexpansion
title CTF AI Orchestrator — 1-Click Automated Launcher
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
echo          1-Click Automated Setup & Launch Command Center (v2.6)
echo ========================================================================
echo.

:: 1. Verify Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Ensure "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo [1/6] Python Environment: %PY_VER% (OK)

:: 2. Auto-initialize .env if missing
if not exist ".env" (
    if exist ".env.example" (
        echo [2/6] Creating .env from .env.example...
        copy /y ".env.example" ".env" >nul
        echo       .env file created! (Configure your GROQ_API_KEY if needed).
    ) else (
        echo [2/6] Creating default .env configuration...
        (
            echo LLM_PROVIDER=groq
            echo GROQ_API_KEY=
            echo GROQ_MODEL=qwen/qwen3.8-27b
            echo ANTHROPIC_API_KEY=
            echo CLAUDE_MODEL=claude-3-5-sonnet-20241022
            echo DASHBOARD_PORT=8080
            echo HF_VECTOR_URL=https://outstandingom-vector.hf.space
            echo HF_KNOWLEDGE_URL=https://outstandingom-knowledge-graph-env.hf.space
            echo MCP_SERVER_URL=https://mcp-server-2sl7.onrender.com
            echo MCP_API_KEY=outstandingom_mcp_2026hjfbechjbdhjjfbnkqjkj
            echo SUPABASE_URL=https://vtlmgubzcktztkuymtir.supabase.co
            echo SUPABASE_ANON_KEY=sb_publishable_0Qoicwxg64tkFReoDSKJ3g_dOSZJPCE
        ) > ".env"
    )
) else (
    echo [2/6] Environment File: .env found (OK)
)

:: 3. Auto-clone Companion Forensic Engine if missing
set "FORENSIC_FOUND=0"
if exist "..\forensic\forensic_engine" set "FORENSIC_FOUND=1"
if exist "forensic\forensic_engine" set "FORENSIC_FOUND=1"
if exist "C:\Users\SGI\Downloads\forensic\forensic_engine" set "FORENSIC_FOUND=1"

if "%FORENSIC_FOUND%"=="0" (
    echo [3/6] Companion Forensic Engine not detected. Checking git...
    git --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo       Auto-cloning Forensic Engine into ..\forensic ...
        git clone --depth 1 https://github.com/outstandingom/forensic.git "..\forensic"
        if %errorlevel% equ 0 (
            echo       Forensic Engine cloned successfully!
        ) else (
            echo       [WARNING] Could not clone forensic engine automatically.
        )
    ) else (
        echo       [WARNING] Git is not installed. Forensic engine must be manually placed at ..\forensic
    )
) else (
    echo [3/6] Forensic Engine: Repository present (OK)
)

:: 4. Auto-clone Companion REA Reversing Engine if missing
set "REA_FOUND=0"
if exist "..\rea" set "REA_FOUND=1"
if exist "rea" set "REA_FOUND=1"
if exist "C:\Users\SGI\Downloads\rea" set "REA_FOUND=1"

if "%REA_FOUND%"=="0" (
    echo [4/6] REA Reverse Engineering Engine not detected. Checking git...
    git --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo       Auto-cloning REA into ..\rea ...
        git clone --depth 1 https://github.com/morluto/rea.git "..\rea"
        if %errorlevel% equ 0 (
            echo       REA cloned successfully!
        ) else (
            echo       [WARNING] Could not clone REA automatically.
        )
    )
) else (
    echo [4/6] REA Engine: Repository present (OK)
)

:: 5. Init git submodules (jailbreaks, etc.)
echo [5/7] Initializing git submodules...
git submodule update --init --recursive >nul 2>&1
if %errorlevel% equ 0 (
    echo       Submodules ready! (OK)
) else (
    echo       [WARNING] Could not init submodules. Run: git submodule update --init --recursive
)

:: 6. Verify & Install Python Dependencies and Playwright Chromium
echo [6/7] Verifying dependencies from requirements.txt...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo       [WARNING] Some packages failed to install. Running verbose install...
    python -m pip install -r requirements.txt
) else (
    echo       Python dependencies verified! (OK)
)

echo       Verifying Playwright Chromium headless browser...
python -m playwright install chromium --quiet >nul 2>&1
echo       Playwright browser ready! (OK)

:: 7. Launch Dashboard & Server
echo [7/7] Starting Command Center on port 8080...
echo.
echo ========================================================================
echo   CTF AI Orchestrator Command Center Live!
echo   Dashboard URL : http://localhost:8080/
echo   API Docs      : http://localhost:8080/docs
echo   Quantum Vault : http://localhost:8088/
echo   Apex Gauntlet : http://localhost:8099/
echo ========================================================================
echo.

:: Automatically open browser
start http://localhost:8080/

:: Start the FastAPI / Uvicorn server
python -m uvicorn server:app --host 127.0.0.1 --port 8080

endlocal
