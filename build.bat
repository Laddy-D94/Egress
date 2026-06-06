@echo off
cd /d "%~dp0"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo ERROR: Could not activate .venv
    echo Make sure you have run:
    echo   python -m venv .venv
    echo   .\.venv\Scripts\Activate.ps1
    echo   python -m pip install -r requirements.txt
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
