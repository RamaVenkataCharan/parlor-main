# stop.ps1 — Reliable Parlor Server Shutdown
$ErrorActionPreference = "Continue"

$ProjectDir = $PSScriptRoot
Set-Location -Path $ProjectDir

Write-Host "Stopping Parlor server..." -ForegroundColor Cyan
Stop-Process -Name python, llama-server -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1
Write-Host "Parlor server stopped." -ForegroundColor Green

