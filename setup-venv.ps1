# Create or refresh the Egress virtual environment.
# Run: .\setup-venv.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

function Find-Python {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return "py -3" }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python -and $python.Source -notmatch "WindowsApps") { return $python.Source }
    return $null
}

$python = Find-Python
if (-not $python) {
    Write-Host "Python not found." -ForegroundColor Red
    Write-Host "Install Python 3.12+ (e.g. winget install Python.Python.3.13) and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Python: $python" -ForegroundColor Cyan

if (Test-Path ".venv") {
    $cfg = Join-Path ".venv" "pyvenv.cfg"
    if (Test-Path $cfg) {
        $content = Get-Content $cfg -Raw
        if ($content -match "C:\\Users\\[^\\]+\\") {
            $homeUser = ([regex]::Match($content, "home = C:\\Users\\([^\\]+)")).Groups[1].Value
            if ($homeUser -and $homeUser -ne $env:USERNAME) {
                Write-Host "Removing .venv (was created for user '$homeUser', current user is '$env:USERNAME')." -ForegroundColor Yellow
                Remove-Item -Recurse -Force ".venv"
            }
        }
    }
    $venvPy = Join-Path ".venv" "Scripts\python.exe"
    if (-not (Test-Path $venvPy)) {
        Write-Host "Removing broken .venv..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force ".venv"
    }
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    if ($python -eq "py -3") {
        & py -3 -m venv .venv
    } else {
        & $python -m venv .venv
    }
}

$venvPython = Join-Path ".venv" "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Failed to create .venv" -ForegroundColor Red
    exit 1
}

Write-Host "Installing dependencies..." -ForegroundColor Green
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

Write-Host ""
Write-Host "Done. Launch with: .\run-egress.ps1" -ForegroundColor Green
& $venvPython --version