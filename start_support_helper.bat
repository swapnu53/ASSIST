@echo off
title FXT Support Helper - Application Support Assistant
echo =====================================================================
echo          FXT SUPPORT HELPER (APS ASSISTANT) - LAUNCHER
echo     Strict Evidence-Based Assistant Grounded in Approved PDF Runbooks
echo =====================================================================
echo.
echo Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b %errorlevel%
)

echo.
echo Starting Support Helper Web Server on http://127.0.0.1:8055 ...
echo Open your browser and navigate to: http://127.0.0.1:8055
echo Press Ctrl+C in this window to stop the server.
echo.

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8055

pause
