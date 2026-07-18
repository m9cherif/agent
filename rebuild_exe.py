"""Rebuild JARVIS EXE - stripped down for speed"""
import PyInstaller.__main__, os, shutil

for d in ["dist", "build_exe_temp"]:
    if os.path.exists(d):
        shutil.rmtree(d)

PyInstaller.__main__.run([
    "run_jarvis.py",
    "--name", "Jarvis",
    "--onefile",
    "--windowed",
    "--noconfirm",
    "--clean",
    "--distpath", "dist",
    "--workpath", "build_exe_temp",
    "--add-data", ".env;.",
    "--hidden-import", "jarvis_app",
    "--hidden-import", "pyttsx3",
    "--hidden-import", "speech_recognition",
    "--hidden-import", "sounddevice",
    "--hidden-import", "psutil",
    "--hidden-import", "pyperclip",
    "--exclude-module", "PyQt5",
    "--exclude-module", "PyQt6",
    "--exclude-module", "PySide2",
    "--exclude-module", "PySide6",
    "--exclude-module", "qtpy",
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy",
    "--exclude-module", "cv2",
    "--exclude-module", "setuptools",
    "--exclude-module", "pip",
    "--exclude-module", "cryptography",
    "--exclude-module", "notebook",
    "--icon", "resources/icons/jarvis.ico",
])

print(f"\nEXE: {os.path.getsize('dist/Jarvis.exe')/1024/1024:.1f} MB")
