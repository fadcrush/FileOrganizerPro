@echo off
REM Quick GitHub Setup Script for Windows
REM This script helps you push FileOrganizerPro to GitHub

echo.
echo =====================================
echo GitHub Setup for FileOrganizer Pro
echo =====================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found. Install from: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [OK] Git found: 
git --version
echo.

REM Check if in correct directory
if not exist "src\backend\api\main.py" (
    echo ERROR: Not in FileOrganizerPro directory
    echo Please run this script from the FileOrganizerPro root folder
    pause
    exit /b 1
)
echo [OK] FileOrganizerPro directory detected
echo.

REM Check git status
echo.
echo Checking git status...
git status
echo.

REM Ask for GitHub username
set /p github_user="Enter your GitHub username: "
if "%github_user%"=="" (
    echo ERROR: GitHub username required
    pause
    exit /b 1
)

REM Ask for repository name
set /p repo_name="Enter repository name (default: FileOrganizerPro): "
if "%repo_name%"=="" (
    set repo_name=FileOrganizerPro
)

echo.
echo =====================================
echo Setup Information
echo =====================================
echo GitHub User: %github_user%
echo Repository: %repo_name%
echo URL: https://github.com/%github_user%/%repo_name%
echo.
echo Steps to complete:
echo 1. Create repo on GitHub: https://github.com/new
echo 2. Use name: %repo_name%
echo 3. Select: Public or Private
echo 4. Copy the commands GitHub shows
echo 5. Come back and press Enter when ready
echo.
pause

REM Initialize git
if not exist ".git" (
    echo.
    echo Initializing git repository...
    git init
    git branch -M main
    echo [OK] Git repository initialized
) else (
    echo [OK] Git repository already exists
)

echo.
echo Checking .gitignore...
if exist ".gitignore" (
    echo [OK] .gitignore found
) else (
    echo Creating .gitignore...
    (
        echo .env
        echo *.db
        echo venv/
        echo __pycache__/
        echo .pytest_cache/
        echo node_modules/
        echo dist/
        echo *.log
        echo data/logs/
        echo data/backups/
        echo .DS_Store
    ) > .gitignore
    echo [OK] .gitignore created
)

echo.
echo Adding files to git...
git add .
echo [OK] Files staged for commit

echo.
echo Creating initial commit...
git commit -m "Initial commit: FileOrganizer Pro v3.0 - Production-ready backend" --quiet
echo [OK] Initial commit created

echo.
echo =====================================
echo Ready to Push to GitHub!
echo =====================================
echo.
echo Copy and paste these commands:
echo.
echo git remote add origin https://github.com/%github_user%/%repo_name%.git
echo git branch -M main
echo git push -u origin main
echo.
echo Run these commands in this folder to push to GitHub.
echo.
pause
