@echo off
REM Build script for web-game (Windows)
REM This script builds the game using pygbag and ensures the output is ready for Vercel

echo Building Tragedy of the Commons Web Game...
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.9+
    exit /b 1
)

REM Check if pygbag is installed
python -m pip show pygbag >nul 2>&1
if errorlevel 1 (
    echo Installing pygbag...
    python -m pip install pygbag
)

REM Build the game
echo Building with pygbag...
python -m pygbag --build main.py

REM Check if build was successful
if not exist "build\web\index.html" (
    echo Error: Build failed - index.html not found
    exit /b 1
)

echo.
echo Build successful!
echo Output directory: build\web
echo.
echo To deploy:
echo 1. Commit the build\web directory: git add build/web ^&^& git commit -m "Update web-game build"
echo 2. Push to trigger Vercel deployment

