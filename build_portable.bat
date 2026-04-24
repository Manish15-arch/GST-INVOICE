@echo off
setlocal
echo ============================================================
echo   GST Billing Suite - Portable Package Builder
echo   Creates a self-contained folder that works on ANY Windows PC
echo ============================================================
echo.

set ROOT=%~dp0
cd /d "%ROOT%"
set OUTDIR=%ROOT%GST-Billing-Suite-Portable

:: Clean
if exist "%OUTDIR%" rmdir /s /q "%OUTDIR%"
mkdir "%OUTDIR%"

echo [1/5] Downloading Python Embeddable...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%OUTDIR%\python-embed.zip'"
if errorlevel 1 (
    echo [ERROR] Download failed. Check internet connection.
    pause
    exit /b 1
)

echo [2/5] Extracting Python...
powershell -Command "Expand-Archive -Path '%OUTDIR%\python-embed.zip' -DestinationPath '%OUTDIR%\python' -Force"
del "%OUTDIR%\python-embed.zip"

:: Enable pip in embedded Python
powershell -Command "(Get-Content '%OUTDIR%\python\python311._pth') -replace '#import site','import site' | Set-Content '%OUTDIR%\python\python311._pth'"

:: Download get-pip.py
echo [3/5] Installing pip and packages...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%OUTDIR%\python\get-pip.py'"
"%OUTDIR%\python\python.exe" "%OUTDIR%\python\get-pip.py" --no-warn-script-location >nul 2>&1

:: Install dependencies
"%OUTDIR%\python\python.exe" -m pip install --no-warn-script-location fastapi uvicorn[standard] python-multipart reportlab num2words Pillow >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install Python packages.
    pause
    exit /b 1
)
echo      Python packages installed.

echo [4/5] Copying application files...
:: Copy app files
copy /y api.py "%OUTDIR%\" >nul
copy /y database.py "%OUTDIR%\" >nul
copy /y invoice_engine.py "%OUTDIR%\" >nul
copy /y pdf_exporter.py "%OUTDIR%\" >nul
copy /y tally_pdf.py "%OUTDIR%\" >nul
copy /y tally_exporter.py "%OUTDIR%\" >nul
copy /y excel_exporter.py "%OUTDIR%\" >nul
copy /y launcher.py "%OUTDIR%\" >nul

:: Copy ui module (needed by database.py and invoice_engine.py)
xcopy /e /i /y "ui" "%OUTDIR%\ui" >nul

:: Copy frontend
xcopy /e /i /y "web\dist" "%OUTDIR%\web\dist" >nul

:: Create data folder
if not exist "%OUTDIR%\data" mkdir "%OUTDIR%\data"

:: Copy existing database if it exists
if exist "data\billing.db" copy /y "data\billing.db" "%OUTDIR%\data\" >nul

echo [5/5] Creating launcher EXE with icon...

:: Compile GSTBillingSuite.exe with embedded icon
for /f "delims=" %%C in ('dir /s /b "C:\Windows\Microsoft.NET\Framework64\v4*\csc.exe" 2^>nul') do set CSC=%%C
if defined CSC (
    "%CSC%" /target:exe /out:"%OUTDIR%\GSTBillingSuite.exe" /win32icon:assets\app.ico Launcher.cs >nul 2>&1
    if exist "%OUTDIR%\GSTBillingSuite.exe" (
        echo      Launcher EXE compiled with icon.
    ) else (
        echo      [WARN] EXE compilation failed, creating batch launcher instead.
        goto :makebat
    )
) else (
    echo      [WARN] .NET compiler not found, creating batch launcher instead.
    :makebat
    (
    echo @echo off
    echo setlocal
    echo set ROOT=%%~dp0
    echo cd /d "%%ROOT%%"
    echo echo   GST Billing Suite v3.0
    echo start "" "http://localhost:8000"
    echo "%%ROOT%%python\python.exe" -m uvicorn api:app --host 127.0.0.1 --port 8000
    ) > "%OUTDIR%\Start GST Suite.bat"
)

echo.
echo ============================================================
echo   BUILD COMPLETE!
echo.

:: Show size
for /f %%A in ('powershell -Command "(Get-ChildItem '%OUTDIR%' -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"') do set SIZE=%%A
echo   Output: %OUTDIR%
echo   Size:   ~%SIZE% MB
echo.
echo   HOW TO USE:
echo   1. Copy "GST-Billing-Suite-Portable" folder to any PC
echo   2. Double-click "GSTBillingSuite.exe"
echo   3. Browser opens automatically at http://localhost:8000
echo.
echo   No Python, Node.js, or internet needed on target PC!
echo ============================================================
pause
