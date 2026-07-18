@echo off
title Installing JARVIS Dependencies
echo ========================================
echo  JARVIS - Installing Dependencies
echo ========================================
echo.

:: Ensure pip is up to date
python -m pip install --upgrade pip

:: Core dependencies
echo [1/4] Installing core packages...
pip install requests urllib3 numpy sounddevice SpeechRecognition pyttsx3 pywin32 psutil PyAutoGUI pyperclip Pillow mss

:: Optional: Audio control
echo [2/4] Installing audio control...
pip install pycaw comtypes

:: Optional: QR codes
echo [3/4] Installing QR/barcode support...
pip install "qrcode[pil]" pyzbar

:: Optional: OCR, JSON path
echo [4/4] Installing extras...
pip install pytesseract jsonpath-ng edge-tts

:: Optional: Windows notifications
pip install win10toast

echo.
echo ========================================
echo  Installation complete!
echo  You can now run: python -m jarvis_app.main
echo ========================================
pause
