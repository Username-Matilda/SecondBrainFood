@echo off
REM Second Brain Food - Start Capture Server
REM Run this to start the capture server

cd /d "%~dp0"
echo.
echo ========================================
echo   Tab Capture Server
echo ========================================
echo.
echo Server running. Minimize this window.
echo Press Ctrl+C to stop.
echo.
python capture_server.py
pause
