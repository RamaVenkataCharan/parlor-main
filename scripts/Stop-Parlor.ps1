<#
.SYNOPSIS
    Stop Parlor Services
.DESCRIPTION
    Safely terminates Parlor application server and llama-server inference engine.
    Stops only the processes listening on ports 8000 and 8081, and confirms they are freed.
#>

[CmdletBinding()]
param (
    [switch]$Force = $false
)

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $ScriptDir "start.ps1")) {
    $ProjectRoot = $ScriptDir
} elseif (Test-Path (Join-Path (Split-Path -Parent $ScriptDir) "start.ps1")) {
    $ProjectRoot = Split-Path -Parent $ScriptDir
} else {
    $ProjectRoot = $ScriptDir
}

Write-Host "===========================================================================" -ForegroundColor Yellow
Write-Host "                     STOPPING PARLOR SERVICES                              " -ForegroundColor Yellow
Write-Host "===========================================================================" -ForegroundColor Yellow
Write-Host "Target Ports : 8000 (FastAPI), 8081 (llama-server)"
Write-Host "Target Procs : python (Parlor), llama-server"
Write-Host "---------------------------------------------------------------------------"

$stoppedCount = 0

# 1. Identify and stop processes listening on ports 8000 and 8081
$activeConnections = Get-NetTCPConnection -LocalPort 8000, 8081 -State Listen -ErrorAction SilentlyContinue
if ($activeConnections) {
    $pidsToStop = $activeConnections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pidsToStop) {
        try {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "Terminating $($p.ProcessName) (PID: $procId) listening on port..." -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                $stoppedCount++
            }
        } catch {
            Write-Host "Notice: Process $procId had already terminated." -ForegroundColor DarkGray
        }
    }
} else {
    Write-Host "No active listening connections found on ports 8000 or 8081." -ForegroundColor DarkGray
}

# 2. Terminate any lingering llama-server processes
$llamaProcs = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue
if ($llamaProcs) {
    foreach ($lp in $llamaProcs) {
        Write-Host "Terminating orphaned llama-server (PID: $($lp.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $lp.Id -Force -ErrorAction SilentlyContinue
        $stoppedCount++
    }
}

Start-Sleep -Seconds 1

# 3. Verification check
$remConn8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
$remConn8081 = Get-NetTCPConnection -LocalPort 8081 -State Listen -ErrorAction SilentlyContinue
$remLlama    = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue

Write-Host "---------------------------------------------------------------------------"
if (-not $remConn8000 -and -not $remConn8081 -and -not $remLlama) {
    Write-Host "[SUCCESS] Parlor is completely stopped." -ForegroundColor Green
    Write-Host " - Port 8000 (Web App)     : FREE" -ForegroundColor Green
    Write-Host " - Port 8081 (llama-server): FREE" -ForegroundColor Green
    Write-Host " - Process llama-server    : NONE RUNNING" -ForegroundColor Green
    Write-Host "Total processes stopped: $stoppedCount"
    Start-Sleep -Seconds 2
    Exit 0
} else {
    Write-Host "[WARNING] Stale processes or ports remain active:" -ForegroundColor Red
    if ($remConn8000) { Write-Host " - Port 8000 is still held by PID $($remConn8000.OwningProcess)" -ForegroundColor Red }
    if ($remConn8081) { Write-Host " - Port 8081 is still held by PID $($remConn8081.OwningProcess)" -ForegroundColor Red }
    if ($remLlama)    { Write-Host " - llama-server is still running (PID $($remLlama.Id))" -ForegroundColor Red }
    Read-Host "Press Enter to exit..."
    Exit 1
}

