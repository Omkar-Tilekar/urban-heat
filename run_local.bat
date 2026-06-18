@echo off
title ISRO Heat Mitigation System Launcher
echo =======================================================
echo     ISRO Urban Heat Island Mitigation Platform
echo =======================================================
echo.

echo [1/3] Launching Backend GIS Server (Port 8000)...
start "UHI GIS Engine" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo.
echo [2/3] Launching AI LLM/RAG Server (Port 8001)...
start "UHI AI Agent" cmd /k "cd ai && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"

echo.
echo [3/3] Launching Frontend React Client (Port 5173)...
start "UHI React Dashboard" cmd /k "cd frontend && npm run dev"

echo.
echo =======================================================
echo   System running!
echo   - GIS API: http://localhost:8000
echo   - AI API:  http://localhost:8001
echo   - App:     http://localhost:5173
echo =======================================================
echo Press any key to exit this launcher window (servers will continue running).
pause > nul
