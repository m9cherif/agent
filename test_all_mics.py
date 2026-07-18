import sounddevice as sd
import numpy as np
import speech_recognition as sr

# Test with all input devices
SAMPLE_RATE = 16000

for device_idx in [0, 1, 6, 11, 14, 15]:
    try:
        print(f"\n=== Testing device {device_idx} ===")
        audio_data = sd.rec(int(SAMPLE_RATE * 2), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=device_idx)
        sd.wait()
        
        rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
        print(f"Device {device_idx} RMS: {rms:.0f}")
        
        if rms > 50:
            wav_bytes = audio_data.tobytes()
            audio = sr.AudioData(wav_bytes, SAMPLE_RATE, 2)
            recognizer = sr.Recognizer()
            
            try:
                text = recognizer.recognize_google(audio, language='en-US')
                print(f"  English: {text}")
            except:
                print("  English: Could not understand")
                
            try:
                text = recognizer.recognize_google(audio, language='ar-SA')
                print(f"  Arabic: {text}")
            except:
                print("  Arabic: Could not understand")
                
    except Exception as e:
        print(f"  Error: {e}")