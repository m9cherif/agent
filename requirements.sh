#!/bin/bash
# JARVIS - Kali Linux / Debian Dependencies
set -e

echo "========================================"
echo " JARVIS - Installing Dependencies"
echo "========================================"
echo ""

# System packages
echo "[1/3] Installing system packages..."
sudo apt update -qq
sudo apt install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    espeak \
    ffmpeg

# Upgrade pip
echo "[2/3] Upgrading pip..."
python3 -m pip install --upgrade pip --quiet

# Python packages
echo "[3/3] Installing Python packages..."
python3 -m pip install --quiet \
    requests \
    urllib3 \
    edge-tts \
    pyttsx3 \
    ddgs \
    numpy \
    sounddevice \
    SpeechRecognition

echo ""
echo "========================================"
echo " Installation complete!"
echo ""
echo " Run: python3 run_jarvis.py"
echo " (API key built-in — edit .env to use your own)"
echo "========================================"
