import sounddevice as sd
import numpy as np

# Test different ways to record
print("Testing different recording methods...")

# Method 1: InputStream
print("\n=== Method 1: InputStream ===")
try:
    SAMPLE_RATE = 16000
    frames = []
    def callback(indata, frames_count, time, status):
        frames.append(indata.copy())
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=1, callback=callback):
        sd.sleep(3000)
    
    if frames:
        audio = np.concatenate(frames)
        rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
        print(f"InputStream RMS: {rms:.0f}")
    else:
        print("No frames captured")
except Exception as e:
    print(f"InputStream error: {e}")

# Method 2: rec with default device (None)
print("\n=== Method 2: rec with device=None ===")
try:
    rec = sd.rec(int(16000 * 3), samplerate=16000, channels=1, dtype='int16', device=None)
    sd.wait()
    rms = np.sqrt(np.mean(rec.astype(np.float64) ** 2))
    print(f"rec(device=None) RMS: {rms:.0f}")
except Exception as e:
    print(f"rec(device=None) error: {e}")

# Method 3: rec with device=0 (Microsoft Sound Mapper)
print("\n=== Method 3: rec with device=0 ===")
try:
    rec = sd.rec(int(16000 * 3), samplerate=16000, channels=1, dtype='int16', device=0)
    sd.wait()
    rms = np.sqrt(np.mean(rec.astype(np.float64) ** 2))
    print(f"rec(device=0) RMS: {rms:.0f}")
except Exception as e:
    print(f"rec(device=0) error: {e}")

# Method 4: rec with device=2
print("\n=== Method 4: rec with device=2 ===")
try:
    rec = sd.rec(int(16000 * 3), samplerate=16000, channels=1, dtype='int16', device=2)
    sd.wait()
    rms = np.sqrt(np.mean(rec.astype(np.float64) ** 2))
    print(f"rec(device=2) RMS: {rms:.0f}")
except Exception as e:
    print(f"rec(device=2) error: {e}")