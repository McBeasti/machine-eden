@echo off
REM Machine Eden development startup (Windows CMD)
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%"

echo Starting Machine Eden...
echo.

start "Machine Eden Backend" cmd /k "cd /d ""%ROOT%\backend"" && if not exist .venv python -m venv .venv && call .venv\Scripts\activate.bat && pip install -r requirements.txt -q && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

start "Machine Eden Frontend" cmd /k "cd /d ""%ROOT%\frontend"" && npm install && npm run dev -- --host 127.0.0.1 --port 5173"

echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API docs: http://localhost:8000/docs
echo.
echo Two new windows were opened. Close them to stop the servers.
echo Then open http://localhost:5173 in your browser.
endlocal
