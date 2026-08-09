# start.ps1 — Reliable Parlor Server Launcher
$ErrorActionPreference = "Continue"

$ProjectDir = $PSScriptRoot
Set-Location -Path $ProjectDir

Write-Host "Checking for stale processes..." -ForegroundColor Cyan
Stop-Process -Name python, llama-server -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host "Starting Parlor server on http://localhost:8000..." -ForegroundColor Green
& "$ProjectDir\.venv\Scripts\python.exe" -m parlor.server



