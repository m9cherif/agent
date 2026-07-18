import sounddevice as sd
import numpy as np
import speech_recognition as sr
import io, wave

sample_rate = 16000
print("Speak clearly for 3 seconds...")
recording = sd.rec(int(sample_rate * 3), samplerate=sample_rate, channels=1, dtype='int16')
sd.wait()

audio_np = recording.flatten()
rms = np.sqrt(np.mean(audio_np.astype(np.float64) ** 2))
print(f"RMS: {rms:.0f}")

buf = io.BytesIO()
with wave.open(buf, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(audio_np.astype(np.int16).tobytes())
wav_data = buf.getvalue()

audio_data = sr.AudioData(wav_data, sample_rate, 2)
r = sr.Recognizer()

print("Trying ar-SA...")
try:
    text = r.recognize_google(audio_data, language='ar-SA')
    print(f'Result: "{text}"')
except sr.UnknownValueError:
    print("Could not understand")
except sr.RequestError as e:
    print(f'Request error: {e}')
except Exception as e:
    print(f'Other error: {e}')