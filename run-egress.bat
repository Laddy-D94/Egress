@echo off
cd /d "%~dp0"

REM Prefer the packaged exe if it exists (for portable use)
if exist "dist\Egress.exe" (
    echo Launching packaged Egress.exe ...
    pushd dist
    Egress.exe
    echo.
    echo App exited. Press any key to close this window...
    pause >nul
    popd
    goto :eof
)

set "VENV_PYTHON=.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Virtual environment not found!
    echo.
    echo Please set it up once with these commands in PowerShell:
    echo   python -m venv .venv
    echo   .\.venv\Scripts\Activate.ps1
    echo   python -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Launching Egress from source in new window (errors will stay visible)...
start "Egress" /D "%~dp0" cmd /k ".venv\Scripts\python.exe -u egress.py & echo. & echo App exited. Press any key to close this window... & pause >nul"
