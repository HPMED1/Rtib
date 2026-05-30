# Build the Rtib Windows installer.
#
# Usage:
#     powershell -ExecutionPolicy Bypass -File scripts\build-installer.ps1
#
# Output:
#     dist\installer\Rtib-<version>-setup.exe
#
# Requires Inno Setup 6 (winget install JRSoftware.InnoSetup).

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot
try {
    # 1. Locate ISCC.exe (Inno Setup compiler).
    $iscc = $null
    $cmd = Get-Command iscc -ErrorAction SilentlyContinue
    if ($cmd) {
        $iscc = $cmd.Source
    } else {
        $candidates = @(
            "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
        )
        foreach ($c in $candidates) {
            if (Test-Path $c) { $iscc = $c; break }
        }
    }
    if (-not $iscc) {
        Write-Host "Inno Setup 6 not found." -ForegroundColor Red
        Write-Host "Install it with: winget install JRSoftware.InnoSetup"
        exit 1
    }
    Write-Host "Using compiler: $iscc" -ForegroundColor Cyan

    # 2. Make sure the .exes are in dist/ -- build them if missing.
    $needsBuild = -not (Test-Path "dist\Rtib.exe") -or -not (Test-Path "dist\cli\rtib.exe")
    if ($needsBuild) {
        Write-Host "dist/ is missing or stale -- running build-dist.ps1 first..." -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\build-dist.ps1"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } else {
        Write-Host "Reusing existing dist/Rtib.exe and dist/cli/rtib.exe."
    }

    # 3. Compile the installer.
    if (-not (Test-Path "dist\installer")) {
        New-Item -ItemType Directory "dist\installer" | Out-Null
    }
    Write-Host ""
    Write-Host "Compiling installer..." -ForegroundColor Cyan
    & $iscc "packaging\rtib.iss"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Inno Setup compilation failed (exit $LASTEXITCODE)." -ForegroundColor Red
        exit $LASTEXITCODE
    }

    Write-Host ""
    Write-Host "Done. Installer at:" -ForegroundColor Green
    $sizeCol = @{ Name = "Size (MB)"; Expression = { [math]::Round($_.Length / 1MB, 1) } }
    Get-ChildItem dist\installer -Filter "*.exe" | Format-Table Name, $sizeCol
} finally {
    Pop-Location
}
