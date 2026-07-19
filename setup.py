#!/usr/bin/env python
"""JARVIS - One-command setup for Windows or Kali Linux"""
import os, sys, subprocess

def run(cmd, shell=False):
    print(f"  > {cmd}")
    subprocess.check_call(cmd if shell else cmd.split(), shell=shell)

def main():
    print("=" * 50)
    print("  J.A.R.V.I.S — Setup")
    print("=" * 50)
    pip = [sys.executable, "-m", "pip"]

    # Upgrade pip
    print("\n[1] Upgrading pip...")
    run(pip + ["install", "--upgrade", "pip"])

    # Install core deps
    print("\n[2] Installing core packages...")
    run(pip + ["install", "requests", "urllib3", "edge-tts", "pyttsx3", "numpy", "sounddevice", "SpeechRecognition"])

    if sys.platform == "win32":
        # Windows-only deps
        print("\n[3] Installing Windows packages...")
        try:
            run(pip + ["install", "pywin32", "comtypes", "pyperclip", "Pillow", "mss"])
        except Exception:
            print("  (optional packages skipped)")
    else:
        # Linux system deps
        print("\n[3] Installing Linux system packages...")
        try:
            run("sudo apt update -qq && sudo apt install -y -qq python3-pip espeak ffmpeg", shell=True)
        except Exception:
            print("  (run with sudo or install manually: espeak, ffmpeg)")

    print("\n" + "=" * 50)
    print("  Setup complete!")
    print("  Run: python run_jarvis.py")
    print("=" * 50)

if __name__ == "__main__":
    main()
