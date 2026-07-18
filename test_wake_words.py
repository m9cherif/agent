import sounddevice as sd
import numpy as np
import speech_recognition as sr
import io, wave

# Test with WO Mic (device 1) - better sensitivity
DEVICE = 1
SAMPLE_RATE = 44100

print('Speak the wake word clearly for 3 seconds...')
rec = sd.rec(int(SAMPLE_RATE * 3), samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=DEVICE)
sd.wait()

rms = np.sqrt(np.mean(rec.astype(np.float64) ** 2))
print('RMS:', rms)

if rms > 50:
    # Resample to 16000
    ratio = 16000 / SAMPLE_RATE
    step = int(1 / ratio)
    audio_16k = rec.flatten()[::step].astype(np.int16)
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_16k.tobytes())
    wav_data = buf.getvalue()
    
    audio = sr.AudioData(wav_data, 16000, 2)
    r = sr.Recognizer()
    
    # Test multiple Arabic dialects
    for lang in ['ar', 'ar-SA', 'ar-EG', 'ar-AE', 'ar-MA', 'ar-DZ', 'ar-TN', 'ar-LB', 'ar-JO', 'ar-IQ']:
        try:
            text = r.recognize_google(audio, language=lang)
            print(lang + ': ' + text)
        except sr.UnknownValueError:
            print(lang + ': ?')
        except sr.RequestError as e:
            print(lang + ': API error - ' + str(e))
else:
    print('Too quiet')