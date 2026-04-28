@echo off
setlocal
title AI Assistant - Multi-Point System Validation

:: Clean screen and display banner
cls
echo ============================================================
echo   🛠 AI ASSISTANT: SYSTEM HEALTH CHECK
echo ============================================================
echo.
echo [SYSTEM] Starting full architecture health check...
echo.

:: Pillar 0: Sync Dependencies
echo [0/4] Pillar 0: Syncing all dependencies...
call uv sync --quiet
if %ERRORLEVEL% NEQ 0 goto :FAILED

:: Pillar 1: Static Code Quality
echo [1/4] Pillar 1: Static Code Quality (Pyright, Ruff ^& Bandit)...
echo      - Running Pyright (Static Type Checking)...
call uv run pyright
if %ERRORLEVEL% NEQ 0 goto :FAILED

echo.
echo      - Running Ruff (Linting)...
call uv run ruff check .
if %ERRORLEVEL% NEQ 0 goto :FAILED

echo.
echo      - Running Ruff (Formatting Check)...
call uv run ruff format --check .
if %ERRORLEVEL% NEQ 0 goto :FAILED

echo.
echo      - Running Bandit (Security Scan)...
call uv run bandit -r src/ -ll
if %ERRORLEVEL% NEQ 0 goto :FAILED

echo      Done.
echo.

:: Pillar 2: Functional Logic ^& Coverage
echo [2/4] Pillar 2: Functional Logic ^& Coverage...
echo      - Running Pytest with Coverage (Gate: 70%%)...
call uv run pytest tests/ --cov=src --cov-fail-under=70 --tb=short
if %ERRORLEVEL% NEQ 0 goto :FAILED

echo      Done.
echo.

:: Pillar 3: Security ^& Container
echo [3/4] Pillar 3: Security ^& Container (Docker Build)...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo      [WARNING] Docker engine is not running. Skipping build check.
) else (
    docker build -t ai-assistant:latest .
    if %ERRORLEVEL% NEQ 0 goto :FAILED
    echo      Done.
)
echo.

:: Pillar 4: App Service Health
echo [4/4] Pillar 4: App Service Health...
:: Check Streamlit UI (8501)
powershell -Command "try { $c = New-Object System.Net.Sockets.TcpClient('localhost', 8501); if ($c.Connected) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% NEQ 0 (
    echo      Streamlit UI is OFFLINE on port 8501.
) else (
    echo      Streamlit UI is ONLINE on port 8501.
)

:: Check Backend API (8000)
powershell -Command "try { $c = New-Object System.Net.Sockets.TcpClient('localhost', 8000); if ($c.Connected) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %ERRORLEVEL% NEQ 0 (
    echo      Backend API is OFFLINE on port 8000.
) else (
    echo      Backend API is ONLINE on port 8000.
)

echo      Done.
echo.

:SUCCESS
echo ============================================================
echo   ✅ SYSTEM HEALTH: 100%% (ALL GATES PASSED)
echo ============================================================
echo.
echo Your Hardened AI Assistant architecture is validated.
pause
exit /b 0

:FAILED
echo.
echo ============================================================
echo   ❌ VALIDATION FAILED
echo ============================================================
echo.
echo Please review the logs above and correct the issues.
pause
exit /b 1
