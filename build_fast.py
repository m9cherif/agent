"""Fast build with --onedir mode (skips unnecessary analysis)"""
import PyInstaller.__main__
import os, shutil, sys

APP_NAME = "Jarvis"
DIST_DIR = "dist"

old_spec = "Jarvis.spec"
if os.path.exists(old_spec):
    os.remove(old_spec)

if os.path.exists(DIST_DIR):
    shutil.rmtree(DIST_DIR)

args = [
    "run_jarvis.py",
    "--name", APP_NAME,
    "--onedir",
    "--windowed",
    "--noconfirm",
    "--workpath", "build_exe_temp",
    "--distpath", DIST_DIR,
    "--add-data", ".env;.",
    "--hidden-import", "jarvis_app.ai",
    "--hidden-import", "jarvis_app.memory",
    "--hidden-import", "jarvis_app.tools",
    "--hidden-import", "jarvis_app.core",
    "--hidden-import", "jarvis_app.gui",
    "--hidden-import", "jarvis_app.voice",
    "--hidden-import", "pyttsx3",
    "--hidden-import", "speech_recognition",
    "--hidden-import", "sounddevice",
    "--hidden-import", "psutil",
    "--hidden-import", "pyperclip",
    "--icon", "resources/icons/jarvis.ico",
]

if "--exclude" in sys.argv:
    args += ["--exclude-module", sys.argv[sys.argv.index("--exclude") + 1]]

PyInstaller.__main__.run(args)

size = os.path.getsize(f"{DIST_DIR}/{APP_NAME}.exe")
total = 0
if os.path.isdir(DIST_DIR):
    for root, dirs, files in os.walk(DIST_DIR):
        total += sum(os.path.getsize(os.path.join(root, f)) for f in files)
print(f"\nEXE: {size/1024/1024:.1f} MB, Total dir: {total/1024/1024:.1f} MB")
