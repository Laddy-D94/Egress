@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found — running setup...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-venv.ps1"
    if errorlevel 1 (
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo ERROR: Could not activate .venv
    echo.
    pause
    exit /b 1
)

echo.
echo Running build_exe.py with venv Python...
python build_exe.py

echo.
echo Build finished. Check the dist folder.
pause
