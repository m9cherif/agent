@echo off
title Installing JARVIS Dependencies
echo ========================================
echo  JARVIS - Installing Dependencies
echo ========================================
echo.

:: Ensure pip is up to date
python -m pip install --upgrade pip

:: Core dependencies
echo [1/2] Installing core packages...
pip install requests urllib3 edge-tts pyttsx3 pywin32 comtypes ddgs

:: Optional: Wake word listener
echo [2/2] Installing wake word support...
pip install numpy sounddevice SpeechRecognition

echo.
echo ========================================
echo  Installation complete!
echo.
echo  Run: python -m jarvis_app.main
echo  (API key built-in — edit .env to use your own)
echo ========================================
pause
