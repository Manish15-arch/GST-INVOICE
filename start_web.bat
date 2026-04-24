@echo off
echo =================================================
echo   GST Billing Suite - Web UI Launcher
echo =================================================
echo.

:: Check if frontend is built
if not exist "%~dp0web\dist\index.html" (
    echo [!] Frontend not built. Building now...
    cd /d "%~dp0web"
    call npm run build
    cd /d "%~dp0"
    echo.
)

echo  Starting GST Billing Suite...
echo  URL: http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo.
echo  Close this window to stop the server.
echo =================================================

:: Open browser after 2 second delay
start /b cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:8000"

:: Start the server (production mode - single server)
cd /d "%~dp0"
python -m uvicorn api:app --host 127.0.0.1 --port 8000
