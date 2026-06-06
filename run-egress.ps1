# Egress Quick Launcher (PowerShell)
# Run: .\run-egress.ps1
# Opens in a new PowerShell window so errors stay visible.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set it up once with these commands:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "  python -m pip install -r requirements.txt" -ForegroundColor Cyan
    Write-Host ""
    pause
    exit 1
}

Write-Host "Launching Egress in new PowerShell window..." -ForegroundColor Green

# Start a new PowerShell window, run the app, and keep the window open
$command = "& '$venvPython' '$scriptDir\egress.py'; Write-Host ''; Write-Host 'Press any key to close...'; `$null = `$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $command
