@echo off
REM Machine Eden development startup (Windows)
echo Starting Machine Eden...

start "Machine Eden Backend" cmd /k "cd /d %~dp0backend && python -m venv .venv 2>nul && .venv\Scripts\activate && pip install -r requirements.txt -q && uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

start "Machine Eden Frontend" cmd /k "cd /d %~dp0frontend && npm install && npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API docs: http://localhost:8000/docs
