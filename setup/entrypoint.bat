@echo off
setlocal enabledelayedexpansion

:: Create required directories if they don't exist
if not exist \app\downloads mkdir \app\downloads
if not exist \app\uploads mkdir \app\uploads
if not exist \app\logs mkdir \app\logs

:: Function to handle cleanup (implemented as label)
:cleanup
echo Shutting down processes...
:: Kill all background processes
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
exit /b 0

:: Set up cleanup on CTRL+C
if "%ENVIRONMENT%"=="development" (
    echo Starting in development mode...
    :: Start FastAPI with hot reload - FIXED PATH
    start /B uvicorn backend.app.main:app --host 0.0.0.0 --port %API_PORT% --reload
    set FASTAPI_PID=!ERRORLEVEL!
    
    :: Rest of the development mode setup...
    cd frontend
    if exist package.json (
        if not exist node_modules (
            echo Installing frontend dependencies...
            call npm install
        )
        echo Starting Vite development server...
        start /B npm run dev -- --host 0.0.0.0 --port %FRONTEND_PORT%
        set VITE_PID=!ERRORLEVEL!
    ) else (
        echo Error: Frontend package.json not found in mounted volume
        exit /b 1
    )
    cd ..
) else (
    echo Starting in production mode...
    :: Start FastAPI without hot reload - FIXED PATH
    start /B uvicorn backend.app.main:app --host 0.0.0.0 --port %API_PORT%
    set FASTAPI_PID=!ERRORLEVEL!
    
    :: Rest of the production mode setup...
    if exist frontend\dist (
        where serve >nul 2>&1
        if !ERRORLEVEL! neq 0 (
            call npm install -g serve
        )
        echo Starting production server for Vite build...
        start /B npx serve -s frontend/dist -l %FRONTEND_PORT%
        set VITE_PID=!ERRORLEVEL!
    ) else (
        echo Error: Frontend dist files not found
        exit /b 1
    )
)

:: Keep the script running and monitor child processes
:loop
timeout /t 1 /nobreak >nul
tasklist | findstr "uvicorn.exe" >nul
if !ERRORLEVEL! neq 0 (
    echo FastAPI process died
    goto cleanup
)
tasklist | findstr "node.exe" >nul
if !ERRORLEVEL! neq 0 (
    echo Vite process died
    goto cleanup
)
goto loop