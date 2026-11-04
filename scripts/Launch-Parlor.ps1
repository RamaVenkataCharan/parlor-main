<#
.SYNOPSIS
    Parlor Desktop Launcher
.DESCRIPTION
    Starts the Parlor multimodal AI assistant and opens the web application in the default browser.
    Ensures llama-server and FastAPI backend are fully initialized before opening the browser.
    Prevents duplicate instances if ports 8000 and 8081 are already active.
#>

[CmdletBinding()]
param (
    [int]$TimeoutSec = 240,
    [int]$PollIntervalSec = 2,
    [switch]$NoBrowser = $false
)

$ErrorActionPreference = "Continue"

# 1. Resolve project root directory dynamically (no hard-coded paths)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Test-Path (Join-Path $ScriptDir "start.ps1")) {
    $ProjectRoot = $ScriptDir
} elseif (Test-Path (Join-Path (Split-Path -Parent $ScriptDir) "start.ps1")) {
    $ProjectRoot = Split-Path -Parent $ScriptDir
} else {
    $ProjectRoot = $ScriptDir
}

$StartScript = Join-Path $ProjectRoot "start.ps1"
$PythonExe   = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$EnvFile     = Join-Path $ProjectRoot ".env"

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "               PARLOR -- DESKTOP APPLICATION LAUNCHER                      " -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "Project Root : $ProjectRoot"
Write-Host "App URL      : http://localhost:8000"
Write-Host "Inference URL: http://127.0.0.1:8081/health"
Write-Host "Timeout      : $TimeoutSec seconds (poll every $PollIntervalSec s)"
Write-Host "---------------------------------------------------------------------------"

function Pause-IfInteractive() {
    try {
        if ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
            Read-Host "Press Enter to exit..."
        }
    } catch {}
}

# Helper function: tests HTTP response cleanly with timeout using loopback IPv4
function Test-HttpEndpoint([string]$Url, [int]$TimeoutSeconds = 2) {
    try {
        $req = [System.Net.HttpWebRequest]::Create($Url)
        $req.Timeout = $TimeoutSeconds * 1000
        $req.Method = "GET"
        $resp = $req.GetResponse()
        $code = [int]$resp.StatusCode
        $resp.Close()
        return ($code -ge 200 -and $code -lt 400)
    } catch [System.Net.WebException] {
        if ($_.Response) {
            $code = [int]$_.Response.StatusCode
            $_.Response.Close()
            return ($code -ge 200 -and $code -lt 400)
        }
        return $false
    } catch {
        return $false
    }
}

# 2. Check if ports 8000 and 8081 already respond
$isAppRunning = (Test-HttpEndpoint "http://127.0.0.1:8000/" 2) -or (Test-HttpEndpoint "http://localhost:8000/" 2)
$isLlamaRunning = Test-HttpEndpoint "http://127.0.0.1:8081/health" 2

if ($isAppRunning -and $isLlamaRunning) {
    Write-Host "[ALREADY RUNNING] Parlor backend and llama-server are active." -ForegroundColor Green
    Write-Host "No second instance needed. Opening browser at http://localhost:8000..." -ForegroundColor Cyan
    if (-not $NoBrowser) {
        Start-Process "http://localhost:8000"
    }
    Start-Sleep -Seconds 1
    Exit 0
}

# 3. Pre-flight checks before cold start
if (-not (Test-Path $StartScript)) {
    Write-Host "[ERROR] Could not find start.ps1 at: $StartScript" -ForegroundColor Red
    Write-Host "Please ensure the project structure is intact." -ForegroundColor Yellow
    Pause-IfInteractive
    Exit 1
}

# Check llama-server availability
$llamaCmd = Get-Command "llama-server" -ErrorAction SilentlyContinue
$llamaAlt = Get-Command "llama" -ErrorAction SilentlyContinue
if (-not $llamaCmd -and -not $llamaAlt) {
    Write-Host "[ERROR] Neither 'llama-server' nor 'llama' was found on your system PATH." -ForegroundColor Red
    Write-Host "Parlor requires llama.cpp to run local inference." -ForegroundColor Yellow
    Write-Host "Please install llama.cpp or add its directory to your PATH environment variable." -ForegroundColor Yellow
    Pause-IfInteractive
    Exit 1
}

# 4. Start start.ps1 in its own detached visible window via Windows Shell
Write-Host "[STARTING] Launching start.ps1 in a dedicated server window..." -ForegroundColor Yellow
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "powershell.exe"
$psi.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$StartScript`""
$psi.WorkingDirectory = $ProjectRoot
$psi.UseShellExecute = $true
$procInfo = [System.Diagnostics.Process]::Start($psi)

if (-not $procInfo) {
    Write-Host "[ERROR] Failed to spawn start.ps1 server process." -ForegroundColor Red
    Pause-IfInteractive
    Exit 1
}

Write-Host "Server console launched (PID: $($procInfo.Id))." -ForegroundColor Cyan
Write-Host "Waiting for inference engine and web server to initialize..." -ForegroundColor Cyan
Write-Host "Note: Model weights (Gemma 4 E2B) loading may take 15 to 45 seconds on GPU/VRAM." -ForegroundColor DarkGray
Write-Host "---------------------------------------------------------------------------"

# 5. Polling loop with clear progress reporting
$startTime = [System.Diagnostics.Stopwatch]::StartNew()
$ready = $false

while ($startTime.Elapsed.TotalSeconds -lt $TimeoutSec) {
    Start-Sleep -Seconds $PollIntervalSec
    $elapsed = [int]$startTime.Elapsed.TotalSeconds

    # Check if server process crashed immediately
    if ($procInfo.HasExited) {
        Write-Host ""
        Write-Host "[ERROR] Server launcher window exited unexpectedly with code $($procInfo.ExitCode)." -ForegroundColor Red
        Write-Host "Please check the server console window for error messages." -ForegroundColor Yellow
        Pause-IfInteractive
        Exit 1
    }

    $llamaOk = Test-HttpEndpoint "http://127.0.0.1:8081/health" 1
    $appOk   = (Test-HttpEndpoint "http://127.0.0.1:8000/" 1) -or (Test-HttpEndpoint "http://localhost:8000/" 1)

    $llamaStatus = if ($llamaOk) { "READY" } else { "loading..." }
    $appStatus   = if ($appOk)   { "READY" } else { "waiting..." }

    Write-Host ("[{0,3}s / {1}s] llama-server (8081): {2,-11} | web app (8000): {3,-11}" -f $elapsed, $TimeoutSec, $llamaStatus, $appStatus)

    if ($llamaOk -and $appOk) {
        $ready = $true
        break
    }
}

$startTime.Stop()

# 6. Result handling
if ($ready) {
    Write-Host "---------------------------------------------------------------------------"
    Write-Host "[SUCCESS] Parlor is fully operational in $($startTime.Elapsed.TotalSeconds.ToString('F1')) seconds!" -ForegroundColor Green
    Write-Host "Opening application at http://localhost:8000..." -ForegroundColor Cyan
    if (-not $NoBrowser) {
        Start-Process "http://localhost:8000"
    }
    Start-Sleep -Seconds 2
    Exit 0
} else {
    Write-Host "---------------------------------------------------------------------------"
    Write-Host "[TIMEOUT] Server did not become ready within $TimeoutSec seconds." -ForegroundColor Red
    Write-Host "llama-server health : $(Test-HttpEndpoint 'http://127.0.0.1:8081/health' 1)" -ForegroundColor Yellow
    Write-Host "web app status      : $(Test-HttpEndpoint 'http://127.0.0.1:8000/' 1)" -ForegroundColor Yellow
    Write-Host "Please inspect the server window for stack traces or resource errors." -ForegroundColor Yellow
    Pause-IfInteractive
    Exit 1
}
