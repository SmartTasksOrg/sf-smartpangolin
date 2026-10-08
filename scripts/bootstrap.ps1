# Create a local venv and install SmartPangolin (dev extras) on Windows PowerShell.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$venv = if ($env:VENV_DIR) { $env:VENV_DIR } else { ".venv" }
if (-not (Test-Path $venv)) {
    Write-Host "[bootstrap] creating venv at $venv"
    python -m venv $venv
}
& "$venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip | Out-Null
Write-Host "[bootstrap] installing SmartPangolin (editable, dev extras)"
pip install -e ".[dev]"
Write-Host ""
Write-Host "[bootstrap] done. Activate with:  $venv\Scripts\Activate.ps1"
sf-smartpangolin --version
