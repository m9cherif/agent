#!/bin/bash
# JARVIS - Kali Linux / Debian Dependencies
set -e

echo "========================================"
echo " JARVIS - Installing Dependencies"
echo "========================================"
echo ""

# System packages
echo "[1/5] Installing system packages..."
sudo apt update -qq
sudo apt install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    tesseract-ocr \
    libtesseract-dev \
    espeak \
    ffmpeg

# Upgrade pip
echo "[2/5] Upgrading pip..."
python3 -m pip install --upgrade pip --quiet

# Core Python packages
echo "[3/5] Installing core Python packages..."
python3 -m pip install --quiet \
    requests \
    urllib3 \
    numpy \
    sounddevice \
    SpeechRecognition \
    pyttsx3 \
    psutil \
    pyperclip \
    Pillow \
    mss

# Optional tools
echo "[4/5] Installing optional tools..."
python3 -m pip install --quiet \
    pyautogui \
    pytesseract \
    qrcode[pil] \
    pyzbar \
    jsonpath-ng \
    edge-tts

# Windows-specific packages (optional, skipped on Linux)
echo "[5/5] Note: pywin32, pycaw, comtypes, win10toast are Windows-only - skipped"

echo ""
echo "========================================"
echo " Installation complete!"
echo ""
echo " To run:"
echo "   1. Copy .env.example to .env and add your OPENROUTER_API_KEY"
echo "   2. python3 run_jarvis.py"
echo "========================================"
