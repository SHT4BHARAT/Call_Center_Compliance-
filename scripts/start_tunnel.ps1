# Start FastAPI and Cloudflare Tunnel

$Host.UI.RawUI.WindowTitle = "FastAPI + Cloudflare Tunnel"

# 1. Start FastAPI server in a new window
Write-Host "Starting FastAPI server on http://localhost:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..'; uvicorn main:app --host 0.0.0.0 --port 8000"

# 2. Wait for server to initialize
Start-Sleep -Seconds 3

# 3. Start Cloudflare Tunnel
Write-Host "Launching Cloudflare Tunnel..." -ForegroundColor Yellow
cloudflared tunnel --url http://localhost:8000
