# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['jarvis_app', 'jarvis_app.ai', 'jarvis_app.memory', 'jarvis_app.security', 'jarvis_app.tools', 'jarvis_app.core', 'jarvis_app.gui', 'jarvis_app.voice', 'pyttsx3', 'pyttsx3.drivers', 'pyttsx3.drivers.sapi5', 'speech_recognition', 'sounddevice', 'psutil', 'pyperclip', 'comtypes', 'comtypes.client']
hiddenimports += collect_submodules('jarvis_app')
hiddenimports += collect_submodules('pyttsx3')
hiddenimports += collect_submodules('speech_recognition')
hiddenimports += collect_submodules('comtypes')


a = Analysis(
    ['run_jarvis.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.'), ('jarvis_app', 'jarvis_app')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'qtpy', 'matplotlib', 'scipy', 'cv2', 'notebook', 'jupyter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Jarvis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources\\icons\\jarvis.ico'],
)
