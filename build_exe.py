#!/usr/bin/env python
"""Build JARVIS executable with PyInstaller"""

import PyInstaller.__main__
import os
import shutil

APP_NAME = "Jarvis"
ENTRY_POINT = "run_jarvis.py"
DIST_DIR = "dist"
BUILD_DIR = "build_exe_temp"

if os.path.exists(DIST_DIR):
    shutil.rmtree(DIST_DIR)
if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)

PyInstaller.__main__.run([
    ENTRY_POINT,
    "--name", APP_NAME,
    "--onefile",
    "--windowed",
    "--noconfirm",
    "--clean",
    "--workpath", BUILD_DIR,
    "--distpath", DIST_DIR,
    "--add-data", ".env;.",
    "--add-data", "jarvis_app;jarvis_app",
    "--hidden-import", "jarvis_app",
    "--hidden-import", "jarvis_app.ai",
    "--hidden-import", "jarvis_app.memory",
    "--hidden-import", "jarvis_app.security",
    "--hidden-import", "jarvis_app.tools",
    "--hidden-import", "jarvis_app.core",
    "--hidden-import", "jarvis_app.gui",
    "--hidden-import", "jarvis_app.voice",
    "--hidden-import", "pyttsx3",
    "--hidden-import", "pyttsx3.drivers",
    "--hidden-import", "pyttsx3.drivers.sapi5",
    "--hidden-import", "speech_recognition",
    "--hidden-import", "sounddevice",
    "--hidden-import", "psutil",
    "--hidden-import", "pyperclip",
    "--hidden-import", "comtypes",
    "--hidden-import", "comtypes.client",
    "--collect-submodules", "jarvis_app",
    "--collect-submodules", "pyttsx3",
    "--collect-submodules", "speech_recognition",
    "--collect-submodules", "comtypes",
    "--exclude-module", "PyQt5",
    "--exclude-module", "PyQt6",
    "--exclude-module", "PySide2",
    "--exclude-module", "PySide6",
    "--exclude-module", "qtpy",
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy",
    "--exclude-module", "cv2",
    "--exclude-module", "notebook",
    "--exclude-module", "jupyter",
    "--icon", "resources/icons/jarvis.ico",
])

if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)

size = os.path.getsize(f"{DIST_DIR}/{APP_NAME}.exe")
print(f"\nBuild complete: {DIST_DIR}/{APP_NAME}.exe ({size/1024/1024:.1f} MB)")
