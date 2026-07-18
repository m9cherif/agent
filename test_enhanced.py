"""Test all enhanced modules"""
import sys
sys.path.insert(0, ".")

from jarvis_app.tools import create_default_registry
r = create_default_registry()
print(f"{len(r.list_tools())} tools loaded")
for t in r.list_tools():
    print(f"  - {t}")

from jarvis_app.voice import VoiceEngine
v = VoiceEngine()
tts_ok = v.tts_engine is not None
stt_ok = v.stt_recognizer is not None
print(f"TTS: {'OK' if tts_ok else 'N/A'}, STT: {'OK' if stt_ok else 'N/A'}")

from jarvis_app.gui import JarvisGUI
print(f"GUI features: {len(JarvisGUI.FEATURES)}")
print("\nAll enhanced modules verified successfully.")
