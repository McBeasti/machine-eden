# Machine Eden development startup (Windows PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Starting Machine Eden..."
Write-Host ""

$backendCmd = @"
cd /d `"$Root\backend`"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@

$frontendCmd = @"
cd /d `"$Root\frontend`"
npm install
npm run dev -- --host 127.0.0.1 --port 5173
"@

Start-Process cmd -ArgumentList "/k", $backendCmd
Start-Sleep -Seconds 3
Start-Process cmd -ArgumentList "/k", $frontendCmd

Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "API docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "Two new windows were opened. Close them to stop the servers."
Write-Host "Then open http://localhost:5173 in your browser."
