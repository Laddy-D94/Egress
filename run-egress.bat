@echo off
cd /d "%~dp0"

set "VENV_PYTHON=.venv\Scripts\python.exe"

REM Prefer source when .venv exists (latest code + TTS fixes). Use dist\run-egress.bat for the packaged exe.
if exist "%VENV_PYTHON%" (
    echo Launching Egress from source in new window...
    start "Egress" /D "%~dp0" cmd /k ".venv\Scripts\python.exe -u egress.py & echo. & echo App exited. Press any key to close this window... & pause >nul"
    goto :eof
)

if exist "dist\Egress.exe" (
    echo Virtual environment not found — launching packaged Egress.exe instead...
    pushd dist
    Egress.exe
    echo.
    echo App exited. Press any key to close this window...
    pause >nul
    popd
    goto :eof
)

echo Virtual environment not found!
echo.
echo Set it up once:
echo   python -m venv .venv
echo   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo Or run the portable build:  dist\run-egress.bat
echo.
pause
exit /b 1
