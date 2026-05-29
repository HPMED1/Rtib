# Build both Rtib executables on Windows.
#
# Usage:
#     powershell -ExecutionPolicy Bypass -File scripts\build-dist.ps1
#
# Output:
#     dist\rtib.exe   (CLI, console)
#     dist\Rtib.exe   (GUI, windowed)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot
try {
    if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
        Write-Host "PyInstaller not found. Install dev deps: pip install -e .[dev]" -ForegroundColor Red
        exit 1
    }

    # Windows is case-insensitive, so rtib.exe and Rtib.exe would collide in
    # the same folder. Keep the GUI at dist/Rtib.exe (the main deliverable)
    # and put the CLI in dist/cli/ so the user can add that folder to PATH.

    Write-Host "Building dist/cli/rtib.exe (CLI, console)..." -ForegroundColor Cyan
    pyinstaller --noconfirm --distpath dist/cli packaging/rtib.spec
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host ""
    Write-Host "Building dist/Rtib.exe (GUI, windowed)..." -ForegroundColor Cyan
    pyinstaller --noconfirm packaging/rtib-gui.spec
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host ""
    Write-Host "Done. Artifacts:" -ForegroundColor Green
    Get-ChildItem dist -Recurse -Filter "*.exe" | Format-Table FullName, @{ Name = "Size (MB)"; Expression = { [math]::Round($_.Length / 1MB, 1) } }
} finally {
    Pop-Location
}
