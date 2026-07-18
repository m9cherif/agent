@echo off
REM JARVIS - Package Installer Script
REM Creates NSIS installer or portable ZIP

setlocal enabledelayedexpansion

echo ========================================
echo    JARVIS - Packaging
echo ========================================
echo.

if "%1"=="--portable" goto portable
if "%1"=="--installer" goto installer

:portable
echo Creating portable ZIP package...
if not exist "..\dist" mkdir ..\dist

REM Collect files
set DIST_DIR=..\dist\JarvisPortable
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
mkdir "%DIST_DIR%"

copy "..\build\Release\Jarvis.exe" "%DIST_DIR%\" >nul
xcopy /E /I /Y "..\src\python" "%DIST_DIR%\python\" >nul
xcopy /E /I /Y "..\plugins" "%DIST_DIR%\plugins\" >nul
copy "..\requirements.txt" "%DIST_DIR%\" >nul
copy "..\.env.example" "%DIST_DIR%\.env" >nul

REM Collect Qt DLLs
if exist "%QTDIR%\bin" (
    for %%D in (Qt6Core Qt6Widgets Qt6Network Qt6Sql Qt6Gui) do (
        if exist "%QTDIR%\bin\%%D.dll" (
            copy "%QTDIR%\bin\%%D.dll" "%DIST_DIR%\" >nul
        )
    )
    xcopy /E /I /Y "%QTDIR%\plugins\platforms" "%DIST_DIR%\platforms\" >nul
)

REM Create ZIP
powershell -Command "& {Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath '..\dist\Jarvis-Portable.zip' -Force}"
echo Portable package created: dist\Jarvis-Portable.zip
goto end

:installer
echo Creating NSIS installer...
if not exist "..\installer" mkdir ..\installer

echo !define PRODUCT_NAME "JARVIS" > ..\installer\jarvis.nsi
echo !define PRODUCT_VERSION "1.0.0" >> ..\installer\jarvis.nsi
echo !define PRODUCT_PUBLISHER "JARVIS Team" >> ..\installer\jarvis.nsi
echo. >> ..\installer\jarvis.nsi
echo Name "\${PRODUCT_NAME}" >> ..\installer\jarvis.nsi
echo OutFile "..\dist\JarvisInstaller.exe" >> ..\installer\jarvis.nsi
echo InstallDir "\$PROGRAMFILES64\JARVIS" >> ..\installer\jarvis.nsi
echo. >> ..\installer\jarvis.nsi
echo Section "Main" SEC01 >> ..\installer\jarvis.nsi
echo   SetOutPath "\$INSTDIR" >> ..\installer\jarvis.nsi
echo   File "..\build\Release\Jarvis.exe" >> ..\installer\jarvis.nsi
echo   SetOutPath "\$INSTDIR\python" >> ..\installer\jarvis.nsi
echo   File /r "..\src\python\*.*" >> ..\installer\jarvis.nsi
echo   SetOutPath "\$INSTDIR\plugins" >> ..\installer\jarvis.nsi
echo   File /r "..\plugins\*.*" >> ..\installer\jarvis.nsi
echo   CreateShortCut "\$SMPROGRAMS\JARVIS.lnk" "\$INSTDIR\Jarvis.exe" >> ..\installer\jarvis.nsi
echo SectionEnd >> ..\installer\jarvis.nsi

echo NSI script created at installer\jarvis.nsi
echo Run 'makensis installer\jarvis.nsi' to build installer

:end
echo.
echo Packaging complete!
exit /b 0
