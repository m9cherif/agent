import sounddevice as sd
import numpy as np
import speech_recognition as sr

# Test device 1 (WO Mic) with longer duration
DEVICE = 1
SAMPLE_RATE = 44100

print(f"Testing device {DEVICE} at {SAMPLE_RATE}Hz...")
print("Speak a clear sentence for 5 seconds...")

try:
    audio_data = sd.rec(int(SAMPLE_RATE * 5), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=DEVICE)
    sd.wait()
    
    rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
    print(f"RMS: {rms:.0f}")
    
    if rms < 100:
        print("Too quiet")
    else:
        # Resample to 16kHz
        ratio = 16000 / SAMPLE_RATE
        audio_16k = (audio_data.flatten()[::int(1/ratio)]).astype(np.int16)
        
        wav_bytes = audio_16k.tobytes()
        audio = sr.AudioData(wav_bytes, 16000, 2)
        recognizer = sr.Recognizer()
        
        print("Recognizing...")
        try:
            text = recognizer.recognize_google(audio, language='ar-SA')
            print(f"Arabic: {text}")
        except sr.UnknownValueError:
            print("Arabic: Could not understand")
        except sr.RequestError as e:
            print(f"Arabic API error: {e}")
        
        try:
            text = recognizer.recognize_google(audio, language='en-US')
            print(f"English: {text}")
        except sr.UnknownValueError:
            print("English: Could not understand")
        except sr.RequestError as e:
            print(f"English API error: {e}")

except Exception as e:
    print(f"Error: {e}")