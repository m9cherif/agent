import sounddevice as sd
import numpy as np
import speech_recognition as sr

DEVICE = 1
SAMPLE_RATE = 44100

print("Testing device 1 - Speak for 3 seconds...")

try:
    audio_data = sd.rec(int(44100 * 3), samplerate=44100, channels=1, dtype='int16', device=1)
    sd.wait()
    
    rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
    print("RMS:", rms)
    
    if rms < 100:
        print("Too quiet")
    else:
        # Resample to 16kHz
        audio_16k = audio_data.flatten()[::2].astype(np.int16)
        
        wav_bytes = audio_16k.tobytes()
        audio = sr.AudioData(wav_bytes, 16000, 2)
        recognizer = sr.Recognizer()
        
        for lang in ['ar', 'ar-SA', 'ar-EG', 'ar-AE', 'en-US', 'en']:
            print("Trying", lang, "...")
            try:
                text = recognizer.recognize_google(audio, language=lang)
                print(f"  {lang}: {text}")
            except sr.UnknownValueError:
                print(f"  {lang}: ?")
            except sr.RequestError as e:
                print(f"  {lang}: API error - {e}")

except Exception as e:
    print("Error:", e)