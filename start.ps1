# Start Shop - Backend + Frontend
# Usage: right-click -> "Run with PowerShell" or run in terminal: .\start.ps1

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "============================" -ForegroundColor Cyan
Write-Host "   Shop - Local Dev Start   " -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

# --- Kill old processes on ports 3000 and 8000 ---
foreach ($port in @(3000, 8000)) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        foreach ($c in $conn) {
            Write-Host "[*] Killing old process on port $port (PID $($c.OwningProcess))..." -ForegroundColor Yellow
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Milliseconds 500
    }
}

# --- Check Node.js (add to PATH if installed but missing) ---
$nodeExists = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeExists) {
    $nodePaths = @(
        "C:\Program Files\nodejs",
        "$env:LOCALAPPDATA\fnm_multishells\*",
        "$env:APPDATA\nvm\*"
    )
    foreach ($p in $nodePaths) {
        $resolved = Resolve-Path $p -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($resolved -and (Test-Path (Join-Path $resolved.Path "node.exe"))) {
            $env:Path = "$($resolved.Path);$env:Path"
            $nodeExists = Get-Command node -ErrorAction SilentlyContinue
            Write-Host "[*] Found Node.js at $($resolved.Path)" -ForegroundColor Yellow
            break
        }
    }
}
if (-not $nodeExists) {
    Write-Host "[!] Node.js not found. Install from https://nodejs.org" -ForegroundColor Red
    Write-Host "    Frontend will NOT start." -ForegroundColor Red
    Write-Host ""
}

# --- Check frontend node_modules ---
$frontendDir = Join-Path $root "frontend"
$nodeModules = Join-Path $frontendDir "node_modules"
if ($nodeExists -and -not (Test-Path $nodeModules)) {
    Write-Host "[*] Installing frontend dependencies..." -ForegroundColor Yellow
    $npmCmd = (Get-Command npm).Source
    Start-Process -Wait -NoNewWindow -FilePath "cmd.exe" -ArgumentList "/c", "`"$npmCmd`"", "install" -WorkingDirectory $frontendDir
    Write-Host "[+] Dependencies installed." -ForegroundColor Green
    Write-Host ""
}

# --- Check backend venv ---
$venvPython = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[!] Python venv not found at venv\Scripts\python.exe" -ForegroundColor Red
    Write-Host "    Create it: python -m venv venv" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# --- Check backend DB ---
$dbFile = Join-Path $root "backend\shop.db"
if (-not (Test-Path $dbFile)) {
    Write-Host "[*] Database not found. Running init_db.py..." -ForegroundColor Yellow
    Push-Location (Join-Path $root "backend")
    & $venvPython init_db.py
    Pop-Location
    Write-Host "[+] Database initialized." -ForegroundColor Green
    Write-Host ""
}

# --- Start Backend FIRST and wait for it ---
Write-Host "[*] Starting Backend on http://localhost:8000 ..." -ForegroundColor Green
$backendJob = Start-Process -PassThru -NoNewWindow -FilePath $venvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory (Join-Path $root "backend")

# Wait for backend to be ready (up to 15 seconds)
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $null = [System.Net.Sockets.TcpClient]::new("127.0.0.1", 8000)
        $ready = $true
        break
    } catch {}
}
if ($ready) {
    Write-Host "[+] Backend is ready!" -ForegroundColor Green
} else {
    Write-Host "[!] Backend taking long to start, continuing anyway..." -ForegroundColor Yellow
}

# --- Start Frontend ---
$frontendJob = $null
if ($nodeExists) {
    Write-Host "[*] Starting Frontend on http://localhost:3000 ..." -ForegroundColor Green
    $nodeBin = (Get-Command node).Source
    $viteBin = Join-Path $frontendDir "node_modules\vite\bin\vite.js"
    $frontendJob = Start-Process -PassThru -NoNewWindow -FilePath $nodeBin -ArgumentList "`"$viteBin`"" -WorkingDirectory $frontendDir
}

Write-Host ""
Write-Host "============================" -ForegroundColor Cyan
Write-Host "   All services running!    " -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host "  Swagger Docs:  http://localhost:8000/docs" -ForegroundColor White
if ($nodeExists) {
    Write-Host "  Frontend:      http://localhost:3000" -ForegroundColor White
}
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# --- Wait and cleanup on exit ---
try {
    while ($true) {
        if ($backendJob.HasExited) {
            Write-Host "[!] Backend stopped unexpectedly." -ForegroundColor Red
            break
        }
        if ($frontendJob -and $frontendJob.HasExited) {
            Write-Host "[!] Frontend stopped unexpectedly." -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    Write-Host ""
    Write-Host "[*] Stopping services..." -ForegroundColor Yellow
    if (-not $backendJob.HasExited) {
        Stop-Process -Id $backendJob.Id -Force -ErrorAction SilentlyContinue
        Get-Process -Name python -ErrorAction SilentlyContinue |
            Where-Object { $_.StartTime -ge $backendJob.StartTime } |
            Stop-Process -Force -ErrorAction SilentlyContinue
    }
    if ($frontendJob -and -not $frontendJob.HasExited) {
        Stop-Process -Id $frontendJob.Id -Force -ErrorAction SilentlyContinue
        Get-Process -Name node -ErrorAction SilentlyContinue |
            Where-Object { $_.StartTime -ge $frontendJob.StartTime } |
            Stop-Process -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[+] All services stopped." -ForegroundColor Green
}
