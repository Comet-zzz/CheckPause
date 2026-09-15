$ErrorActionPreference = "Stop"

# Builds the portable folder (dist\CheckPause\) and then a single-file installer.
# Requires Inno Setup 6: https://jrsoftware.org/isdl.php  (or: winget install JRSoftware.InnoSetup)
# This file is intentionally ASCII-only: Windows PowerShell 5.1 reads .ps1 files
# without a BOM using the system code page, which corrupts non-ASCII text.

function Get-IsccPath {
    $command = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }

    $bases = @("${env:ProgramFiles(x86)}", $env:ProgramFiles) | Where-Object { $_ }
    if ($env:LOCALAPPDATA) {
        $bases += (Join-Path $env:LOCALAPPDATA "Programs")
    }
    foreach ($base in $bases) {
        $candidate = Join-Path $base "Inno Setup 6\ISCC.exe"
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Virtual environment not found: $python`nCreate .venv and install requirements first."
}

Push-Location -LiteralPath $root
try {
    Write-Host "==> Installing build requirements" -ForegroundColor Cyan
    & $python -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install build requirements (exit code $LASTEXITCODE)."
    }

    Write-Host "==> Running PyInstaller" -ForegroundColor Cyan
    & $python -m PyInstaller CheckPause.spec --noconfirm
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed (exit code $LASTEXITCODE)."
    }

    $version = [regex]::Match(
        (Get-Content -LiteralPath "checkpause\__init__.py" -Raw),
        'APP_VERSION\s*=\s*"([^"]+)"'
    ).Groups[1].Value
    if (-not $version) {
        throw "Could not read APP_VERSION from checkpause\__init__.py."
    }
    Write-Host "==> Version $version" -ForegroundColor Cyan

    if ((Get-Content -LiteralPath "version_info.txt" -Raw) -notmatch [regex]::Escape($version)) {
        Write-Warning "version_info.txt does not mention $version - keep the two in sync."
    }

    $iscc = Get-IsccPath
    if (-not $iscc) {
        throw "ISCC.exe not found. Install Inno Setup 6: https://jrsoftware.org/isdl.php"
    }

    Write-Host "==> Compiling installer with Inno Setup" -ForegroundColor Cyan
    # Drop installers from previous versions so an outdated one cannot be shipped by mistake.
    Get-ChildItem -LiteralPath "dist" -Filter "CheckPause_Setup_*.exe" -File -ErrorAction SilentlyContinue |
        Remove-Item -Force

    $isccArgs = @("/DAppVersion=$version")
    if (Test-Path -LiteralPath (Join-Path $root "installer\languages\ChineseSimplified.isl")) {
        $isccArgs += "/DChineseIslBundled=1"
    }
    elseif (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $iscc) "Languages\ChineseSimplified.isl")) {
        $isccArgs += "/DChineseIslCompiler=1"
    }
    else {
        Write-Warning "ChineseSimplified.isl not found - the installer UI will be English only."
    }
    $isccArgs += (Join-Path $root "installer\CheckPause.iss")

    & $iscc @isccArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed (exit code $LASTEXITCODE)."
    }

    Write-Host ""
    Write-Host "Build finished:" -ForegroundColor Green
    Write-Host "  Ship this     : dist\CheckPause_Setup_$version.exe"
    Write-Host "  Portable build: dist\CheckPause\CheckPause.exe"
}
finally {
    Pop-Location
}
