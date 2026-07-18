import sounddevice as sd
import numpy as np
import speech_recognition as sr

# Device 6 works at 48000 Hz - let's use it at native rate
DEVICE = 6
SAMPLE_RATE = 48000

print(f"Testing device {DEVICE} at {SAMPLE_RATE}Hz...")
print("Speak clearly for 3 seconds...")

try:
    audio_data = sd.rec(int(SAMPLE_RATE * 3), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=DEVICE)
    sd.wait()
    
    rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
    print(f"RMS: {rms:.0f}")
    
    if rms < 50:
        print("Audio too quiet!")
    else:
        # Resample to 16000 for Google STT
        import scipy.signal
        audio_16k = scipy.signal.resample(audio_data, int(len(audio_data) * 16000 / SAMPLE_RATE)).astype(np.int16)
        
        wav_bytes = audio_16k.tobytes()
        audio = sr.AudioData(wav_bytes, 16000, 2)
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