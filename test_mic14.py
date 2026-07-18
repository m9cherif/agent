import sounddevice as sd
import numpy as np
import speech_recognition as sr

# Test with device 14 (HD Audio Microphone - likely real hardware)
DEVICE = 14
SAMPLE_RATE = 16000

print(f"Testing with device {DEVICE}...")
print("Speak now for 3 seconds...")

try:
    audio_data = sd.rec(int(SAMPLE_RATE * 3), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=DEVICE)
    sd.wait()
    
    rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
    print(f"RMS: {rms:.0f}")
    
    if rms < 50:
        print("Audio too quiet!")
    else:
        # Convert to AudioData
        wav_bytes = audio_data.tobytes()
        audio = sr.AudioData(wav_bytes, SAMPLE_RATE, 2)
        recognizer = sr.Recognizer()
        
        print("Trying Arabic...")
        try:
            text = recognizer.recognize_google(audio, language='ar-SA')
            print(f"Arabic: {text}")
        except sr.UnknownValueError:
            print("Arabic: Could not understand")
        except sr.RequestError as e:
            print(f"Arabic API error: {e}")
        
        print("Trying English...")
        try:
            text = recognizer.recognize_google(audio, language='en-US')
            print(f"English: {text}")
        except sr.UnknownValueError:
            print("English: Could not understand")
        except sr.RequestError as e:
            print(f"English API error: {e}")

except Exception as e:
    print(f"Error: {e}")