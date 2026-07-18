@echo off
REM JARVIS - Install Dependencies Script
REM Run this first to set up all dependencies

echo ========================================
echo    JARVIS - Installing Dependencies
echo ========================================
echo.

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    echo Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Installing Python packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some Python packages failed to install
)

echo [2/4] Checking for CMake...
where cmake >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: CMake not found. Install from https://cmake.org
)

echo [3/4] Checking for Qt6...
where qmake6 >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Qt6 may not be in PATH.
    echo Install Qt 6.5+ from https://qt.io
)

echo [4/4] Setting up directories...
if not exist "models" mkdir models
if not exist "models\sherpa" mkdir models\sherpa
if not exist "models\piper" mkdir models\piper

echo.
echo ========================================
echo    Setup complete!
echo.
echo    Next steps:
echo    1. Copy .env.example to .env and set your API key
echo    2. Run build.bat to compile
echo    3. Run scripts\download_models.bat for voice models
echo ========================================
pause
