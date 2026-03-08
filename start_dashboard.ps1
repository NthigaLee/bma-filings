# BMA Filings Dashboard - Remote Access Launcher
# Starts Python HTTP server + localtunnel for public URL

$PORT = 8001
$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  BMA FILINGS DASHBOARD - REMOTE LAUNCHER  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Kill any existing process on port 8001
$existing = netstat -ano | Select-String ":$PORT " | Select-Object -First 1
if ($existing) {
    $pid_match = ($existing -split '\s+')[-1]
    Write-Host "Clearing port $PORT (PID $pid_match)..." -ForegroundColor Yellow
    Stop-Process -Id $pid_match -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# Start Python HTTP server in background
Write-Host "Starting Python server on port $PORT..." -ForegroundColor Green
$pythonServer = Start-Process -FilePath "python" -ArgumentList "-m", "http.server", "$PORT" `
    -WorkingDirectory $DIR -WindowStyle Hidden -PassThru

Write-Host "Server PID: $($pythonServer.Id)" -ForegroundColor Gray
Write-Host "Local URL:  http://localhost:$PORT/dashboard.html" -ForegroundColor White
Write-Host ""
Write-Host "Starting localtunnel for remote access..." -ForegroundColor Green
Write-Host ""

# Run localtunnel (tries bma-dashboard subdomain for a consistent URL)
try {
    npx localtunnel --port $PORT --subdomain bma-dashboard 2>&1
} catch {
    Write-Host "Note: subdomain bma-dashboard may be taken, trying random..." -ForegroundColor Yellow
    npx localtunnel --port $PORT 2>&1
}

# Cleanup on exit
Write-Host ""
Write-Host "Stopping server (PID $($pythonServer.Id))..." -ForegroundColor Yellow
Stop-Process -Id $pythonServer.Id -Force -ErrorAction SilentlyContinue
Write-Host "Done." -ForegroundColor Green
