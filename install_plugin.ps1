# Install Anim8 Pipeline into an Unreal project (PowerShell — use in Cursor terminal)
Set-Location $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 install_plugin.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python install_plugin.py
} else {
    Write-Host "Python not found. Install Python 3 or run install_plugin.bat from File Explorer."
    exit 1
}
if ($LASTEXITCODE -ne 0) { Read-Host "Press Enter to close" }
