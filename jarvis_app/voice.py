"""JARVIS Voice Pipeline - Real-time STT + edge-tts (JARVIS voice) + SAPI fallback"""

import io
import os
import queue
import re
import tempfile
import threading
import time
import wave


def _resample(audio, orig_sr, target_sr):
    import numpy as np
    if orig_sr == target_sr:
        return audio
    ratio = target_sr / orig_sr
    new_len = int(len(audio) * ratio)
    indices = np.arange(new_len) / ratio
    return np.interp(indices, np.arange(len(audio)), audio).astype(np.int16)


class VoiceEngine:
    def __init__(self):
        self._callbacks = {}
        self._listening = False
        self._recording_thread = None
        self._audio_queue = queue.Queue()
        self._sample_rate = 16000
        self._native_rate = 44100
        self._channels = 1
        self._dtype = "int16"
        self._silence_threshold = 60
        self._min_phrase_duration = 0.2
        self._max_silence = 0.6
        self._max_phrase = 6
        self._tts_available = False
        self._stream_buffer = ""
        self._stream_lock = threading.Lock()
        self._speaking = threading.Event()
        self.current_amplitude = 0.0
        self._device = 14
        self._edge_voice = "en-GB-RyanNeural"
        self._speaker = None
        self._init_tts()

    def on(self, event, callback):
        self._callbacks[event] = callback

    def _emit(self, event, *args):
        cb = self._callbacks.get(event)
        if cb:
            cb(*args)

    def _init_tts(self):
        self._edge_available = False
        self._speaker = None
        self._tts_available = False
        # Always init SAPI first (fastest + offline)
        try:
            import pythoncom; pythoncom.CoInitialize()
            import win32com.client
            self._speaker = win32com.client.Dispatch("SAPI.SpVoice")
            voices = self._speaker.GetVoices()
            selected = None
            for i in range(voices.Count):
                desc = voices.Item(i).GetDescription().lower()
                if "david" in desc or "zira" in desc:
                    selected = voices.Item(i)
                    break
            if not selected and voices.Count > 0:
                selected = voices.Item(0)
            if selected:
                self._speaker.Voice = selected
            self._speaker.Rate = 0
            self._speaker.Volume = 100
            self._tts_available = True
        except Exception:
            pass
        # edge-tts for natural voice (optional)
        try:
            import edge_tts
            import asyncio
            asyncio.run(edge_tts.list_voices())
            self._edge_available = True
        except Exception:
            pass
        # pyttsx3 as last resort
        if not self._tts_available:
            try:
                import pyttsx3
                self._tts_fallback = pyttsx3.init()
                self._tts_fallback.setProperty("rate", 180)
                self._tts_fallback.setProperty("volume", 1.0)
                self._tts_available = True
            except Exception:
                pass

    @staticmethod
    def _clean_for_speech(text):
        t = text
        t = re.sub(r'\*+', '', t)
        t = re.sub(r'`[^`]*`', '', t)
        t = re.sub(r'_{2,}', '', t)
        t = re.sub(r'~~(.*?)~~', r'\1', t)
        t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
        t = re.sub(r'^[#*>\-|]\s*', '', t, flags=re.MULTILINE)
        t = re.sub(r'```[\s\S]*?```', ' code block. ', t)
        t = re.sub(r'[(){}\[\]<>]', '', t)
        t = re.sub(r'["\']', '', t)
        t = re.sub(r'\s+', ' ', t).strip()
        t = t.replace(' - ', ', ').replace('...', ', ')
        return t[:2000]

    def speak(self, text):
        if not self._tts_available or not text:
            return
        cleaned = self._clean_for_speech(text)
        if not cleaned:
            return
        # Try edge-tts first for JARVIS British male voice
        if self._edge_available:
            t = threading.Thread(target=self._edge_speak, args=(cleaned,), daemon=True)
            t.start()
            t.join(timeout=1.5)
            if t.is_alive():
                if self._speaker:
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                        self._speaker.Speak(cleaned, 1)
                    except Exception:
                        pass
            return
        # SAPI fallback (fast, no network)
        if self._speaker:
            try:
                import pythoncom
                pythoncom.CoInitialize()
                self._speaker.Speak(cleaned, 1)
                return
            except Exception:
                pass
        # pyttsx3 last resort
        if self._tts_fallback:
            threading.Thread(target=self._fallback_speak, args=(cleaned,), daemon=True).start()

    def speak_stream(self, chunk, is_final=False):
        if not self._tts_available or not chunk:
            return
        with self._stream_lock:
            self._stream_buffer += chunk
            if not is_final:
                return
            full = self._stream_buffer.strip()
            self._stream_buffer = ""
        if full:
            self.speak(full)

    def stop_speech(self):
        with self._stream_lock:
            self._stream_buffer = ""
        try:
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            player = win32com.client.Dispatch("WMPlayer.OCX")
            player.controls.stop()
        except Exception:
            pass
        if self._speaker:
            try:
                import pythoncom
                pythoncom.CoInitialize()
                self._speaker.Speak("", 2)
            except Exception:
                pass

    def _edge_speak(self, text):
        import asyncio
        import edge_tts
        try:
            communicate = edge_tts.Communicate(
                text,
                self._edge_voice,
                rate="-10%",
                pitch="-5Hz",
            )
            f = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            fpath = f.name
            f.close()
            asyncio.run(communicate.save(fpath))
            self._play_mp3(fpath)
            try:
                os.unlink(fpath)
            except Exception:
                pass
        except Exception as e:
            self._emit("tts_error", f"Edge TTS failed: {e}")
            if self._speaker:
                try:
                    self._speaker.Speak(text, 1)
                except Exception:
                    pass

    def _play_mp3(self, path):
        import time
        try:
            import pythoncom; pythoncom.CoInitialize()
            import win32com.client
            player = win32com.client.Dispatch("WMPlayer.OCX")
            media = player.newMedia(path)
            if not media:
                return
            player.currentPlaylist.appendItem(media)
            player.controls.play()
            timeout = 30
            start = time.time()
            while time.time() - start < timeout:
                try:
                    dur = media.duration if media else 0
                    pos = player.controls.currentPosition if player.controls else 0
                    if dur > 0 and pos >= dur - 0.15:
                        break
                    if dur <= 0 and time.time() - start > 1:
                        break
                except Exception:
                    pass
                time.sleep(0.1)
        except Exception:
            try:
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_NODEFAULT | winsound.SND_ASYNC)
            except Exception:
                try:
                    import subprocess
                    subprocess.run(
                        ["powershell", "-c", "(New-Object -ComObject WMP.OCX).controls.play()"],
                        capture_output=True, timeout=15
                    )
                except Exception:
                    pass

    def _fallback_speak(self, text):
        try:
            self._tts_fallback.say(text)
            self._tts_fallback.runAndWait()
        except Exception as e:
            self._emit("tts_error", str(e))

    def _rms(self, frame):
        import numpy as np
        samples = np.frombuffer(frame, dtype=np.int16).astype(np.float64)
        if len(samples) == 0:
            return 0
        return np.sqrt(np.mean(samples ** 2))

    def _record_loop(self):
        import sounddevice as sd
        import numpy as np

        chunk_duration = 0.1
        chunk_samples = int(self._native_rate * chunk_duration)

        try:
            self._emit("listening", "Initializing microphone...")
            buffer = bytearray()
            silence_start = None
            voiced_start = None

            def audio_callback(indata, frames, t, status):
                self._audio_queue.put(indata.copy())

            stream = sd.InputStream(
                samplerate=self._native_rate,
                channels=self._channels,
                dtype=self._dtype,
                blocksize=chunk_samples,
                device=self._device,
                callback=audio_callback,
            )
            stream.start()

            self._emit("listening_started")
            self._emit("listening", "Listening...")

            while self._listening:
                try:
                    chunk = self._audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                raw = chunk.tobytes()
                rms = self._rms(raw)
                self.current_amplitude = rms
                threshold = self._silence_threshold

                if rms > threshold:
                    buffer.extend(raw)
                    if not self._listening:
                        break
                    if voiced_start is None:
                        voiced_start = time.time()
                        self._emit("listening", "Speak...")
                    silence_start = None
                else:
                    if voiced_start is not None and silence_start is None:
                        silence_start = time.time()

                    if silence_start is not None:
                        silence_dur = time.time() - silence_start
                        phrase_dur = time.time() - voiced_start if voiced_start else 0

                        if phrase_dur > self._min_phrase_duration and silence_dur > self._max_silence:
                            if len(buffer) > 1600:
                                self._emit("listening", "Processing...")
                                audio_bytes = bytes(buffer)
                                buffer.clear()
                                voiced_start = None
                                silence_start = None
                                threading.Thread(
                                    target=self._transcribe,
                                    args=(audio_bytes,),
                                    daemon=True
                                ).start()
                                if self._listening:
                                    self._emit("listening", "Listening...")
                            else:
                                buffer.clear()
                                voiced_start = None
                                silence_start = None
                        elif phrase_dur > self._max_phrase:
                            if len(buffer) > 1600:
                                audio_bytes = bytes(buffer)
                                buffer.clear()
                                voiced_start = None
                                silence_start = None
                                threading.Thread(
                                    target=self._transcribe,
                                    args=(audio_bytes,),
                                    daemon=True
                                ).start()
                                if self._listening:
                                    self._emit("listening", "Listening...")

            stream.stop()
            stream.close()

        except Exception as e:
            self._emit("stt_error", f"Recording error: {e}")
        finally:
            self._listening = False
            self.current_amplitude = 0.0
            self._emit("listening_stopped")

    def _transcribe(self, audio_bytes):
        try:
            import speech_recognition as sr
            import numpy as np

            # Convert native rate (44100) to STT rate (16000)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

            # Boost quiet audio to improve STT accuracy
            rms = np.sqrt(np.mean(audio_np.astype(np.float64) ** 2))
            if 1 < rms < 500:
                gain = min(3000.0 / max(rms, 1), 8.0)
                audio_np = (audio_np.astype(np.float64) * gain)
                audio_np = np.clip(audio_np, -32768, 32767).astype(np.int16)

            audio_16k = _resample(audio_np, 44100, 16000)
            wav_bytes = audio_16k.tobytes()

            audio_data = sr.AudioData(
                wav_bytes,
                16000,
                2
            )

            recognizer = sr.Recognizer()
            # Try Arabic first, then English
            text = ""
            try:
                text = recognizer.recognize_google(audio_data, language="ar-SA")
            except sr.UnknownValueError:
                try:
                    text = recognizer.recognize_google(audio_data, language="en-US")
                except sr.UnknownValueError:
                    pass

            if text and text.strip():
                self._emit("stt_result", text.strip())
        except sr.UnknownValueError:
            self._emit("stt_result", "")
        except sr.RequestError as e:
            self._emit("stt_error", f"STT API: {e}")
        except ImportError:
            self._emit("stt_error", "speech_recognition not installed")
        except Exception as e:
            self._emit("stt_error", f"Transcribe error: {e}")

    def start_listening(self, device=None):
        if self._listening:
            return
        if device is not None:
            self._device = device
        self._listening = True

        try:
            import sounddevice as sd
            import numpy as np
            # Calibrate at native rate
            rec = sd.rec(int(self._native_rate * 1), samplerate=self._native_rate,
                         channels=self._channels, dtype=self._dtype, device=self._device)
            sd.wait()
            rms_vals = []
            chunk_size = int(self._native_rate * 0.1)
            for i in range(0, len(rec) - chunk_size, chunk_size):
                chunk = rec[i:i + chunk_size]
                rms_vals.append(self._rms(chunk.tobytes()))
            if rms_vals:
                median_rms = sorted(rms_vals)[len(rms_vals) // 2]
                self._silence_threshold = max(median_rms * 1.2, 60)
        except Exception:
            self._silence_threshold = 200

        self._recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self._recording_thread.start()

    def stop_listening(self):
        self._listening = False
        if self._recording_thread:
            self._recording_thread = None

    def is_listening(self):
        return self._listening

    def calibrate(self):
        import sounddevice as sd
        import numpy as np

        self._emit("listening", "Calibrating... stay silent")
        try:
            recording = sd.rec(int(self._native_rate * 2),
                              samplerate=self._native_rate,
                              channels=self._channels,
                              dtype=self._dtype,
                              device=self._device)
            sd.wait()
            rms_vals = []
            chunk_size = int(self._native_rate * 0.1)
            for i in range(0, len(recording) - chunk_size, chunk_size):
                chunk = recording[i:i + chunk_size]
                frame = chunk.tobytes()
                rms_vals.append(self._rms(frame))
            if rms_vals:
                median_rms = sorted(rms_vals)[len(rms_vals) // 2]
                self._silence_threshold = max(median_rms * 1.5, 60)
                self._emit("listening",
                    f"Calibrated threshold: {self._silence_threshold:.0f}")
        except Exception as e:
            self._emit("stt_error", f"Calibration: {e}")
