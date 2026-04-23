@echo off
setlocal
title AI Assistant - System Launcher

:: Clean screen and display banner
cls
echo ============================================================
echo   [AI ASSISTANT] AGENTIC MLOPS SYSTEM
echo ============================================================
echo.
echo [SYSTEM] Initializing Backend Services and UI...
echo.

:: Step 0: Cleanup existing containers to avoid port conflicts
echo [0/4] Cleaning up conflicting Docker services...
:: We stop Docker versions of backend/frontend to run them locally
docker compose stop backend frontend >nul 2>&1
echo      Done.
echo.

:: Step 1: Check/Sync Dependencies
echo [1/4] Verifying local dependencies with UV...
uv sync --quiet
if "%ERRORLEVEL%" NEQ "0" (
    echo.
    echo 🚨 Error: Failed to sync dependencies. Verify 'uv' is installed.
    pause
    exit /b %ERRORLEVEL%
)
echo      Done.
echo.

:: Step 2: Orchestrate Infrastructure (Optional)
echo [2/4] Ensuring infrastructure services are active...
:: Check if Docker engine is running
docker info >nul 2>&1
if "%ERRORLEVEL%" NEQ "0" (
    echo      [WARNING] Docker engine is not running. Skipping infrastructure orchestration.
    echo      (Note: If you are using local models in Docker, they will not be available.)
) else (
    :: We keep Docker for the LLM/Database services if they are defined
    docker compose up -d llm >nul 2>&1
    echo      Done.
)
echo.

:: Step 3: Launch FastAPI in a separate minimized window
echo [3/4] Launching Agentic API (FastAPI)...
echo      Endpoint: http://localhost:8000
:: Start the API window minimized to keep it tidy but accessible
:: IMPORTANT: We use --env-file .env to ensure local environment variables are loaded
start "AI-Assistant-API" /min cmd /k "title AI-Assistant-API && uv run --env-file .env uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for API to warm up
echo.
echo [WAIT] Stalling for API initialization (5s)...
timeout /t 5 >nul

:: Step 4: Launch Intelligence Dashboard (Streamlit)
echo.
echo [4/4] Launching Interactive UI (Streamlit)...
echo      URL: http://localhost:8501
echo.
echo ------------------------------------------------------------
echo [INFO] The API is running in a separate window (minimized).
echo.
echo    To stop EVERYTHING:
echo    1. Close the "AI-Assistant-API" window in the taskbar.
echo    2. Press Ctrl+C in THIS window to stop Streamlit.
echo    3. Run 'docker compose down' if you used infrastructure.
echo ------------------------------------------------------------
echo.

:: Run Streamlit in the foreground with environment loading
:: Note: Streamlit will automatically open the browser to http://localhost:8501
:: Set PYTHONPATH to include the project root for module resolution
set PYTHONPATH=%PYTHONPATH%;%CD%
uv run --env-file .env streamlit run src/ui/app.py

:SUCCESS
echo.
echo [SYSTEM] AI Assistant Sessions Terminated.
pause
exit /b 0
