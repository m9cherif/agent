import sounddevice as sd
import numpy as np

# Check device 6 info
devices = sd.query_devices()
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        print(f"{i}: {d['name']} | sr={d['default_samplerate']} | ch={d['max_input_channels']} | hostapi={d['hostapi']}")