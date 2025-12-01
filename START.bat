@echo off
echo.
echo ========================================
echo   Starting Loanlytics AI
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file:
    echo 1. Copy .env.example to .env
    echo 2. Fill in your credentials
    echo.
    pause
    exit /b 1
)

echo [1/2] Starting Backend API...
echo.
start cmd /k "call venv\Scripts\activate && python backend\app.py"

timeout /t 3 /nobreak >nul

echo [2/2] Opening Frontend...
echo.
start frontend\index.html

echo.
echo ========================================
echo   Loanlytics AI Started!
echo ========================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: Opening in browser...
echo.
echo Press any key to exit (this will NOT stop the servers)
pause >nul

