# Create an "Rtib" shortcut on the user's Desktop pointing at dist\Rtib.exe.
#
# Usage:
#     powershell -ExecutionPolicy Bypass -File scripts\install-shortcut.ps1
#
# Idempotent: re-running just updates the existing shortcut.

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$TargetExe = Join-Path $ProjectRoot "dist\Rtib.exe"
$IconPath = Join-Path $ProjectRoot "src\rtib\resources\icons\rtib.ico"

if (-not (Test-Path $TargetExe)) {
    Write-Host "Rtib.exe not found at $TargetExe" -ForegroundColor Red
    Write-Host "Build it first: powershell -ExecutionPolicy Bypass -File scripts\build-dist.ps1"
    exit 1
}

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Rtib.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetExe
$Shortcut.WorkingDirectory = Split-Path $TargetExe -Parent
$Shortcut.IconLocation = "$IconPath,0"
$Shortcut.Description = "Rtib - arrange messy text"
$Shortcut.Save()

Write-Host "Created shortcut at $ShortcutPath" -ForegroundColor Green
