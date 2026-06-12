# Egress Quick Launcher (PowerShell)
# Run: .\run-egress.ps1
# Opens in a new PowerShell window so errors stay visible.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found — running setup..." -ForegroundColor Yellow
    $setup = Join-Path $scriptDir "setup-venv.ps1"
    if (-not (Test-Path $setup)) {
        Write-Host "setup-venv.ps1 is missing. Run: python -m venv .venv && pip install -r requirements.txt" -ForegroundColor Red
        pause
        exit 1
    }
    & $setup
    if (-not (Test-Path $venvPython)) {
        pause
        exit 1
    }
}

Write-Host "Launching Egress in new PowerShell window..." -ForegroundColor Green

# Start a new PowerShell window, run the app, and keep the window open
$command = "& '$venvPython' '$scriptDir\egress.py'; Write-Host ''; Write-Host 'Press any key to close...'; `$null = `$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $command
