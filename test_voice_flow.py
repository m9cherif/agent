import sounddevice as sd
import numpy as np
import speech_recognition as sr

# Test the exact flow used in voice.py (which works)
SAMPLE_RATE = 16000
DEVICE = 1  # WO Mic Device (default)

print("Testing voice.py flow...")
print("Speak for 2 seconds...")

try:
    # This is what voice.py does for calibration
    rec = sd.rec(int(SAMPLE_RATE * 1), samplerate=SAMPLE_RATE,
                 channels=1, dtype='int16', device=DEVICE)
    sd.wait()
    
    rms = np.sqrt(np.mean(rec.astype(np.float64) ** 2))
    print(f"Calibration RMS: {rms:.0f}")
    
    # Now test actual recognition
    print("Now speak for 3 seconds...")
    rec = sd.rec(int(SAMPLE_RATE * 3), samplerate=SAMPLE_RATE,
                 channels=1, dtype='int16', device=DEVICE)
    sd.wait()
    
    rms = np.sqrt(np.mean(rec.astype(np.float64) ** 2))
    print(f"Recording RMS: {rms:.0f}")
    
    if rms < 100:
        print("Too quiet")
    else:
        # Convert to WAV with proper headers
        import io, wave
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(rec.astype(np.int16).tobytes())
        wav_data = buf.getvalue()
        
        audio = sr.AudioData(wav_data, SAMPLE_RATE, 2)
        recognizer = sr.Recognizer()
        
        print("Recognizing...")
        try:
            text = recognizer.recognize_google(audio, language='ar-SA')
            print(f"Arabic: {text}")
        except sr.UnknownValueError:
            print("Arabic: ?")
        except Exception as e:
            print(f"Arabic error: {e}")
        
        try:
            text = recognizer.recognize_google(audio, language='en-US')
            print(f"English: {text}")
        except sr.UnknownValueError:
            print("English: ?")
        except Exception as e:
            print(f"English error: {e}")

except Exception as e:
    print(f"Error: {e}")