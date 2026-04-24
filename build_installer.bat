@echo off
echo ============================================================
echo   GST Billing Suite - Build Installer
echo   This script creates a standalone Windows installer (.exe)
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.11+ first.
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Install Node.js 18+ first.
    pause
    exit /b 1
)

set ROOT=%~dp0
cd /d "%ROOT%"

echo.
echo [1/4] Installing Python dependencies...
pip install pyinstaller fastapi uvicorn python-multipart reportlab num2words Pillow
if errorlevel 1 (
    echo [ERROR] Failed to install Python packages.
    pause
    exit /b 1
)

echo.
echo [2/4] Building React frontend...
cd web
call npm install
call npm run build
cd ..
if not exist "web\dist\index.html" (
    echo [ERROR] Frontend build failed! web\dist\index.html not found.
    pause
    exit /b 1
)
echo      Frontend built successfully.

echo.
echo [3/4] Bundling with PyInstaller...

:: Clean previous builds
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

:: Run PyInstaller
pyinstaller ^
    --name "GSTBillingSuite" ^
    --console ^
    --noconfirm ^
    --add-data "web\dist;web\dist" ^
    --add-data "database.py;." ^
    --add-data "invoice_engine.py;." ^
    --add-data "pdf_exporter.py;." ^
    --add-data "tally_pdf.py;." ^
    --add-data "tally_exporter.py;." ^
    --add-data "excel_exporter.py;." ^
    --add-data "api.py;." ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.loops ^
    --hidden-import uvicorn.loops.auto ^
    --hidden-import uvicorn.protocols ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.http.h11_impl ^
    --hidden-import uvicorn.protocols.websockets ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    --hidden-import uvicorn.lifespan.off ^
    --hidden-import fastapi ^
    --hidden-import pydantic ^
    --hidden-import starlette ^
    --hidden-import reportlab ^
    --hidden-import num2words ^
    --hidden-import sqlite3 ^
    --hidden-import email.mime.multipart ^
    --collect-all uvicorn ^
    --collect-all fastapi ^
    --collect-all starlette ^
    --collect-submodules reportlab ^
    launcher.py

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

:: Copy data folder template
if not exist "dist\GSTBillingSuite\data" mkdir "dist\GSTBillingSuite\data"

echo      PyInstaller build complete.

echo.
echo [4/4] Build Complete!
echo.
echo ============================================================
echo   Output:  dist\GSTBillingSuite\GSTBillingSuite.exe
echo.
echo   To run:  double-click GSTBillingSuite.exe
echo   It will start the server and open your browser.
echo.
echo   To create an installer, install Inno Setup and compile:
echo     installer.iss
echo ============================================================
echo.
pause
