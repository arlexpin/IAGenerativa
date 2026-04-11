param(
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"

$pythonLauncher = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonLauncher = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonLauncher = "py -3"
} else {
    throw "Python launcher not found. Install Python and retry."
}

Write-Host "[1/3] Creating virtual environment at $VenvPath"
Invoke-Expression "$pythonLauncher -m venv $VenvPath"

$pythonExe = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found at $pythonExe"
}

Write-Host "[2/3] Upgrading pip"
& $pythonExe -m pip install --upgrade pip

Write-Host "[3/3] Installing unified test dependencies"
& $pythonExe -m pip install -r requirements-test.txt
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed with exit code $LASTEXITCODE"
}

Write-Host "Done. Activate with: .\\$VenvPath\\Scripts\\Activate.ps1"
