@echo off
REM JARVIS - Build Script for Windows
REM Requires: CMake 3.20+, MSVC 2022, Qt 6.5+

setlocal enabledelayedexpansion

echo ========================================
echo    JARVIS - Building Desktop Assistant
echo ========================================
echo.

REM Check requirements
where cmake >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CMake not found. Install from https://cmake.org
    exit /b 1
)

where cl >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: MSVC compiler not found.
    echo Run from "x64 Native Tools Command Prompt for VS 2022"
    exit /b 1
)

REM Configure
echo [1/3] Configuring with CMake...
if not exist "build" mkdir build
cd build

cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CMake configuration failed
    cd ..
    exit /b 1
)

REM Build
echo [2/3] Building...
cmake --build . --config Release
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    cd ..
    exit /b 1
)

cd ..

REM Copy output
echo [3/3] Copying artifacts...
if not exist "dist" mkdir dist
copy "build\Release\Jarvis.exe" "dist\Jarvis.exe" >nul
copy "build\Release\*.dll" "dist\" >nul

echo.
echo ========================================
echo    Build successful!
echo    Executable: dist\Jarvis.exe
echo ========================================

exit /b 0
