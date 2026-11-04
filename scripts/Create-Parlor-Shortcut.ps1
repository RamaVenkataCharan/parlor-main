<#
.SYNOPSIS
    Creates Parlor Desktop Shortcuts (.lnk) with custom icons.
.DESCRIPTION
    1. Ensures multi-size icon assets (.ico) exist in scripts/.
    2. Creates 'Parlor.lnk' on the user's Desktop pointing to scripts/Launch-Parlor.ps1.
    3. Creates 'Stop Parlor.lnk' on the user's Desktop pointing to scripts/Stop-Parlor.ps1.
#>

[CmdletBinding()]
param ()

$ErrorActionPreference = "Stop"

# 1. Resolve project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $ScriptDir "start.ps1")) {
    $ProjectRoot = $ScriptDir
} elseif (Test-Path (Join-Path (Split-Path -Parent $ScriptDir) "start.ps1")) {
    $ProjectRoot = Split-Path -Parent $ScriptDir
} else {
    $ProjectRoot = $ScriptDir
}

$LaunchScript = Join-Path $ScriptDir "Launch-Parlor.ps1"
$StopScript   = Join-Path $ScriptDir "Stop-Parlor.ps1"
$IconPath     = Join-Path $ScriptDir "parlor.ico"
$StopIconPath = Join-Path $ScriptDir "parlor-stop.ico"
$IconGenPy    = Join-Path $ScriptDir "generate_icons.py"

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "             PARLOR -- DESKTOP SHORTCUT CREATOR                            " -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "Project Root  : $ProjectRoot"
Write-Host "Launch Script : $LaunchScript"
Write-Host "Stop Script   : $StopScript"
Write-Host "---------------------------------------------------------------------------"

# 2. Generate or refresh icons if missing
if ((-not (Test-Path $IconPath)) -or (-not (Test-Path $StopIconPath))) {
    Write-Host "[ICONS] Generating high-resolution multi-size Windows icon files..." -ForegroundColor Yellow
    if (Test-Path (Join-Path $ProjectRoot ".venv\Scripts\python.exe")) {
        & "$ProjectRoot\.venv\Scripts\python.exe" "$IconGenPy"
    } else {
        uv run python "$IconGenPy"
    }
}

if (-not (Test-Path $IconPath)) {
    Write-Host "[ERROR] Could not find or generate $IconPath" -ForegroundColor Red
    Exit 1
}

Write-Host "[ICONS] Found verified icon: $IconPath ($((Get-Item $IconPath).Length) bytes)" -ForegroundColor Green
if (Test-Path $StopIconPath) {
    Write-Host "[ICONS] Found verified stop icon: $StopIconPath ($((Get-Item $StopIconPath).Length) bytes)" -ForegroundColor Green
}

# 3. Locate Desktop
$DesktopPath = [Environment]::GetFolderPath("Desktop")
if (-not $DesktopPath -or -not (Test-Path $DesktopPath)) {
    $DesktopPath = Join-Path $env:USERPROFILE "Desktop"
}
Write-Host "[DESKTOP] Target directory: $DesktopPath" -ForegroundColor Cyan

# 4. Create WScript.Shell COM Object
$WshShell = New-Object -ComObject WScript.Shell

# 5. Create 'Parlor.lnk'
$ParlorLnkPath = Join-Path $DesktopPath "Parlor.lnk"
Write-Host "[SHORTCUT] Creating 'Parlor.lnk'..." -ForegroundColor Yellow
$Shortcut = $WshShell.CreateShortcut($ParlorLnkPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -File `"$LaunchScript`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.IconLocation = "$IconPath,0"
$Shortcut.Description = "Parlor - On-Device Multimodal AI Wellness Assistant"
$Shortcut.Save()
Write-Host "  -> Created: $ParlorLnkPath" -ForegroundColor Green
Write-Host "     Target : powershell.exe"
Write-Host "     Args   : -NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -File `"$LaunchScript`""
Write-Host "     WorkDir: $ProjectRoot"
Write-Host "     Icon   : $IconPath,0"

# 6. Create 'Stop Parlor.lnk'
$StopLnkPath = Join-Path $DesktopPath "Stop Parlor.lnk"
Write-Host "[SHORTCUT] Creating 'Stop Parlor.lnk'..." -ForegroundColor Yellow
$StopShortcut = $WshShell.CreateShortcut($StopLnkPath)
$StopShortcut.TargetPath = "powershell.exe"
$StopShortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$StopScript`""
$StopShortcut.WorkingDirectory = $ProjectRoot
$StopIconToUse = if (Test-Path $StopIconPath) { $StopIconPath } else { $IconPath }
$StopShortcut.IconLocation = "$StopIconToUse,0"
$StopShortcut.Description = "Stop Parlor Services (Ports 8000 and 8081)"
$StopShortcut.Save()
Write-Host "  -> Created: $StopLnkPath" -ForegroundColor Green
Write-Host "     Target : powershell.exe"
Write-Host "     Args   : -NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -File `"$StopScript`""
Write-Host "     WorkDir: $ProjectRoot"
Write-Host "     Icon   : $StopIconToUse,0"

Write-Host "---------------------------------------------------------------------------"
Write-Host "[SUCCESS] Desktop shortcuts created successfully!" -ForegroundColor Green
Write-Host "You can now double-click 'Parlor' on your Desktop to start the application." -ForegroundColor Cyan
