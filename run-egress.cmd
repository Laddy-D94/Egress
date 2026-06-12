@echo off
REM Launcher that bypasses PowerShell execution policy (no admin needed).
cd /d "%~dp0"
where pwsh >nul 2>&1
if %ERRORLEVEL%==0 (
    pwsh -ExecutionPolicy Bypass -NoProfile -File "%~dp0run-egress.ps1" %*
) else (
    powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0run-egress.ps1" %*
)
exit /b %ERRORLEVEL%