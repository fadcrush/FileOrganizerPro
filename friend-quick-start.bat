@echo off
REM Quick Start Script for Friends (Windows)
REM Double-click this file to start FileOrganizer Pro

setlocal enabledelayedexpansion

echo.
echo =====================================
echo FileOrganizer Pro - Friend Quick Start
echo =====================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found
    echo Install from: https://docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker found

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose not found
    pause
    exit /b 1
)
echo [OK] Docker Compose found
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file...
    copy ".env.example" ".env" >nul
    echo [OK] .env created
)
echo.

REM Start services
echo Starting FileOrganizer Pro...
docker-compose up -d

echo.
echo Waiting for services to start...
timeout /t 5 /nobreak

REM Check if API is running
echo Checking API health...
for /f "tokens=*" %%i in ('curl -s http://localhost:8000/health 2^>nul') do set health=%%i

if "%health%"=="" (
    echo Still starting up... waiting a few more seconds
    timeout /t 5 /nobreak
)

echo.
echo =====================================
echo SUCCESS! FileOrganizer Pro is ready!
echo =====================================
echo.
echo Open in your browser:
echo   Swagger Docs: http://localhost:8000/docs
echo   ReDoc Docs:   http://localhost:8000/redoc
echo.
echo Test the API:
echo   curl http://localhost:8000/health
echo.
echo Stop services:
echo   docker-compose down
echo.
echo Having issues?
echo   docker-compose logs -f app
echo.
pause
