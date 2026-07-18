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
pip install requests urllib3 edge-tts pyttsx3 comtypes

:: Optional: Wake word listener
echo [2/2] Installing wake word support...
pip install numpy sounddevice SpeechRecognition

echo.
echo ========================================
echo  Installation complete!
echo.
echo  Next: copy .env.example to .env
echo  Edit .env and set your OPENROUTER_API_KEY
echo  Then run: python -m jarvis_app.main
echo ========================================
pause
