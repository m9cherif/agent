#!/usr/bin/env python3
"""Install optional dependencies for JARVIS tools"""

import subprocess
import sys
import os

# Core packages (already installed via pip)
CORE = [
    "requests",
    "sounddevice",
    "speechrecognition",
    "pyttsx3",
    "psutil",
    "pywin32",
    "pyperclip",
    "pyautogui",
]

# Optional packages for extra tools
OPTIONAL = [
    # Audio control (volume/mute)
    "pycaw",
    "comtypes",
    # QR codes
    "qrcode[pil]",
    "pyzbar",
    # OCR
    "pytesseract",
    # JSON path queries
    "jsonpath-ng",
    # Network speed test (optional)
    # "speedtest-cli",
]

def install(packages, desc):
    print(f"\n=== Installing {desc} ===")
    for pkg in packages:
        print(f"  {pkg}...", end=" ", flush=True)
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg], 
                         check=True, capture_output=True, text=True)
            print("OK")
        except subprocess.CalledProcessError as e:
            print(f"FAILED: {e.stderr[:100]}")

def main():
    print("JARVIS Optional Dependencies Installer")
    print("=" * 40)
    
    # Install core first
    install(CORE, "Core Dependencies")
    
    # Install optional
    install(OPTIONAL, "Optional Tool Dependencies")
    
    print("\n=== Post-install Notes ===")
    print("For OCR (tesseract): Install tesseract-ocr from:")
    print("  https://github.com/UB-Mannheim/tesseract/wiki")
    print("  Then add to PATH")
    print()
    print("For pyzbar (QR decode): Install zbar from:")
    print("  https://github.com/mchehab/zbar/releases")
    print()
    print("All done! Run: python run_jarvis.py")

if __name__ == "__main__":
    main()