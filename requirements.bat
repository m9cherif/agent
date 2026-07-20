@echo off
title Installing JARVIS Dependencies
echo ========================================
echo  JARVIS - Installing Dependencies
echo ========================================
echo.

:: Ensure pip is up to date
python -m pip install --upgrade pip

:: Core dependencies
echo [1/3] Installing core packages...
pip install requests urllib3 edge-tts pyttsx3 pywin32 comtypes ddgs

:: Optional: System monitoring & UI
echo [2/3] Installing system & UI packages...
pip install psutil pyautogui pyperclip qrcode[pil] Pillow

:: Optional: Wake word listener
echo [3/3] Installing wake word & misc...
pip install numpy sounddevice SpeechRecognition dnspython jsonpath-ng mss

echo.
echo ========================================
echo  Installation complete!
echo.
echo  Run: python -m jarvis_app.main
echo  (API key built-in — edit .env to use your own)
echo ========================================
pause
