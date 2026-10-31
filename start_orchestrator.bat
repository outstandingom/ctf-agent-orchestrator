@echo off
title CTF AI Orchestrator - Local KeepAlive Runner
color 0a

cd /d "c:\Users\SGI\Downloads\ctf-agent-orchestrator"

:loop
echo =======================================================
echo [CTF AGENT] Starting Local Orchestrator on Port 8080...
echo [CTF AGENT] Access Dashboard at: http://localhost:8080
echo =======================================================

python -m uvicorn server:app --host 0.0.0.0 --port 8080

echo [WARNING] Server stopped or crashed. Restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
