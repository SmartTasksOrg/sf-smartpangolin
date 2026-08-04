# Build every SmartPangolin package from source (Windows/PowerShell).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
Write-Host "== spec sync =="; python tools\export_policy.py
Write-Host "== PyPI =="; python -m build; python -m twine check dist\*
Write-Host "== Node =="; Push-Location ports\node; npm pack; Pop-Location
Write-Host "== Go =="; Push-Location ports\go; go build -o pangolin-check.exe .; Pop-Location
Write-Host "== Java =="; Push-Location ports\java; New-Item -ItemType Directory -Force out | Out-Null; javac -d out src\*.java; "Main-Class: Main" | Out-File -Encoding ascii out\manifest.txt; jar cfm pangolin-check.jar out\manifest.txt -C out .; Pop-Location
Write-Host "== PHP =="; php -l ports\php\pangolin-check.php
Write-Host "ALL BUILDS DONE"
