"""Debug microphone detection"""
import sounddevice as sd

print("=== SoundDevice Devices ===")
devices = sd.query_devices()
for i, d in enumerate(devices):
    ins = d["max_input_channels"]
    outs = d["max_output_channels"]
    print(f"  {i}: {d['name']} (in={ins}, out={outs})")

print(f"\nDefault input: {sd.default.device}")

import speech_recognition as sr
print("\n=== SpeechRecognition Microphones ===")
mics = sr.Microphone.list_microphone_names()
if mics:
    for i, m in enumerate(mics):
        print(f"  {i}: {m}")
else:
    print("  NO MICROPHONES DETECTED")

print("\nTrying to open microphone...")
try:
    mic = sr.Microphone(sample_rate=16000)
    with mic as source:
        print(f"  Microphone opened: {mic.device_index}")
        print(f"  Sample rate: {source.SAMPLE_RATE}")
        print(f"  Sample width: {source.SAMPLE_WIDTH}")
        r = sr.Recognizer()
        print("  Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("  Microphone works!")
except Exception as e:
    print(f"  ERROR: {e}")
