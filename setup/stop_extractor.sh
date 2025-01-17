@echo off
setlocal enabledelayedexpansion

echo Stopping Course Data Extractor...

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not running!
    pause
    exit /b 1
)

:: Stop the containers
docker compose down

:: Verify all containers are stopped
if %ERRORLEVEL% equ 0 (
    echo.
    echo Application stopped successfully!
) else (
    echo.
    echo Error: There was a problem stopping the application.
    echo Please check if any containers are still running with: docker ps
)

echo.
pause