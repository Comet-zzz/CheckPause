$ErrorActionPreference = "Stop"

& ".venv\Scripts\python.exe" -m pip install -r requirements-build.txt
& ".venv\Scripts\python.exe" -m PyInstaller CheckPause.spec --noconfirm

Write-Host ""
Write-Host "Build finished: dist\CheckPause\CheckPause.exe"
