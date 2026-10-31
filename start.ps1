# start.ps1 — Reliable Parlor Server Launcher
$ErrorActionPreference = "Continue"

$ProjectDir = $PSScriptRoot
Set-Location -Path $ProjectDir

Write-Host "Checking for stale processes on Parlor ports (8000, 8081)..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8000, 8081 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object {
        try {
            $p = Get-Process -Id $_ -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "Stopping process $($p.ProcessName) (PID: $_) listening on port..." -ForegroundColor Yellow
                Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
            }
        } catch {}
    }
Stop-Process -Name llama-server -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host "Starting Parlor server on http://localhost:8000..." -ForegroundColor Green
& "$ProjectDir\.venv\Scripts\python.exe" -m parlor.server



