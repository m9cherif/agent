import sounddevice as sd
import numpy as np
import speech_recognition as sr_module

def resample(audio, orig_sr, target_sr):
    """Simple linear interpolation resample"""
    if orig_sr == target_sr:
        return audio
    ratio = target_sr / orig_sr
    new_len = int(len(audio) * ratio)
    indices = np.arange(new_len) / ratio
    return np.interp(indices, np.arange(len(audio)), audio).astype(np.int16)

# Test devices that showed activity
test_devices = [
    (5, 44100),  # Primary Audio Capture Driver
    (6, 44100),  # WO Mic Device (hostapi 1) - had highest RMS
    (1, 44100),  # WO Mic Device (hostapi 0)
    (14, 44100), # HD Audio Microphone
]

print("Speak for 3 seconds each test...\n")

for device_idx, sr in test_devices:
    try:
        print(f"\n=== Device {device_idx} at {sr}Hz ===")
        audio_data = sd.rec(int(sr * 3), samplerate=sr, channels=1, dtype='int16', device=device_idx)
        sd.wait()
        
        rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
        print(f"RMS: {rms:.0f}")
        
        if rms > 100:
            # Resample to 16k
            audio_16k = resample(audio_data.flatten(), sr, 16000)
            
            wav_bytes = audio_16k.tobytes()
            audio = sr_module.AudioData(wav_bytes, 16000, 2)
            recognizer = sr_module.Recognizer()
            
            # Quick test
            try:
                text = recognizer.recognize_google(audio, language='en-US')
                print(f"  English: {text[:60]}")
            except:
                print("  English: ?")
                
            try:
                text = recognizer.recognize_google(audio, language='ar-SA')
                print(f"  Arabic: {text[:60]}")
            except:
                print("  Arabic: ?")
        else:
            print("  Too quiet")
            
    except Exception as e:
        print(f"  Error: {e}")