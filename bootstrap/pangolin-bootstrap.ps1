# Scaffold the SmartPangolin standardized secret locations (Windows/PowerShell).
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Bootstrapping SmartPangolin safe-zone in $(Get-Location) ..."
New-Item -ItemType Directory -Force -Path .secret\local, .secret\ci, .secret\data | Out-Null
if (-not (Test-Path .secret\README.md)) { Copy-Item "$here\templates\secret-README.md" .secret\README.md }
if (-not (Test-Path .pangolin.json))    { Copy-Item "$here\templates\pangolin.json" .pangolin.json }
if (-not (Test-Path .gitignore)) { New-Item -ItemType File .gitignore | Out-Null }
if (-not (Select-String -Path .gitignore -Pattern "SmartPangolin standardized secret locations" -Quiet)) {
  Get-Content "$here\templates\gitignore-additions.txt" | Add-Content .gitignore
  Write-Host "  + appended secret locations to .gitignore"
}
Write-Host "  + created .secret\{local,ci,data} and .pangolin.json"
Write-Host "Done. Move sensitive files into .secret\ and run:  sf-smartpangolin pack --dry-run"
