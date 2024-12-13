@echo off
SETLOCAL EnableDelayedExpansion

echo Course Data Extractor Launcher
echo ============================
echo.

REM Check if Docker is installed
docker --version > nul 2>&1
if errorlevel 1 (
    echo Docker is not installed! Please install Docker Desktop first.
    echo You can download it from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker is running
docker info > nul 2>&1
if errorlevel 1 (
    echo Docker is not running! Please start Docker Desktop.
    pause
    exit /b 1
)

echo Starting Course Data Extractor...
echo This may take a few minutes on first run...
echo.

REM Create data directory if it doesn't exist
if not exist "data" mkdir data

REM Pull and start the containers
docker-compose up --build -d

REM Wait for the application to start
echo Waiting for the application to start...
timeout /t 10 /nobreak > nul

REM Open the browser
start http://localhost:8501

echo.
echo Application is running!
echo You can access it at: http://localhost:8501
echo.
echo To stop the application, close this window and run stop_extractor.bat
echo.

REM Keep the window open
pause