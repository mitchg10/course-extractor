@echo off
setlocal enabledelayedexpansion

echo Course Data Extractor Launcher
echo ============================
echo.

:: Set default environment if not provided
if "%1"=="" (
    set ENVIRONMENT=development
) else (
    set ENVIRONMENT=%1
)

echo Running in %ENVIRONMENT% mode
echo.

:: Check if Docker is installed
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Docker is not installed! Please install Docker Desktop first.
    echo You can download it from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Docker is not running! Please start Docker Desktop.
    pause
    exit /b 1
)

echo Starting Course Data Extractor...
echo This may take a few minutes on first run...
echo.

:: Create required directories if they don't exist
if not exist uploads mkdir uploads
if not exist downloads mkdir downloads
if not exist logs mkdir logs

:: Pull and start the containers with environment variable
echo Building and starting Course Extractor...
set ENVIRONMENT=%ENVIRONMENT%
docker compose up --build -d

:: Wait for the application to start
echo Waiting for the application to start...
timeout /t 5 /nobreak >nul

:: Check if the application is running
docker compose ps | findstr "course-extractor" >nul
if %ERRORLEVEL% equ 0 (
    echo Course Extractor is running!
    echo Backend API: http://localhost:8000
    echo Frontend: http://localhost:5173
) else (
    echo Error: Course Extractor failed to start
    docker compose logs
    exit /b 1
)

:: Open the browser
start http://localhost:5173

echo.
echo Application is running!
echo You can access it at: http://localhost:5173
echo.
echo To stop the application, close this window and run stop_extractor.bat
echo.

pause