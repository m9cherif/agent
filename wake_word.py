"""
JARVIS Wake Word Listener - Uses sounddevice (no PyAudio needed)
"""
import os
import sys
import time
import threading
import subprocess
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from pathlib import Path


class WakeWordListener:
    def __init__(self):
        self._callbacks = {}
        self._listening = False
        self._thread = None
        self._wake_words = [
            # Arabic - exact
            "أفق", "أفق يا جارفيس", "يا جارفيس", "جارفيس",
            "لفق", "لفق يا جارفيس", "يا جارفيس لفق",
            # Arabic - phonetic (what Google STT actually hears)
            "أفغ", "أفك", "أفوق", "أفاك", "أفواق", "افاق",
            "أفاج", "أفج", "أفح", "أفخ", "آفاق", "أفاكس",
            "لفغ", "لفك", "لفاك", "لفاج", "لفج", "لفخ",
            "ل فق", "لأفق", "لفاغ", "لفوق", "لافق", "لافاك",
            "يا جرفيس", "يا جار فيس", "يا جارافيس", "يا كرافيس",
            "جار فيس", "جارافيس", "جارفيز", "جرفيس", "كرافيس",
            # English
            "hey jarvis", "jarvis", "ok jarvis", "hello jarvis",
            "hey jarvus", "hey jarviz", "hey jahvis",
            "jarvus", "jarviz", "j.arvis", "j arvis",
            # Mixed
            "أفق jarvis", "jarvis أقف", "jarvis أفق",
            "هي jarvis", "هي جارفيس",
        ]
        self._last_trigger = 0
        self._cooldown = 3.0
        self._sample_rate = 16000
        
    def on(self, event, callback):
        self._callbacks[event] = callback
        
    def _emit(self, event, *args):
        cb = self._callbacks.get(event)
        if cb:
            try:
                cb(*args)
            except Exception:
                pass
    
    def _listen_loop(self):
        try:
            self._emit("listening", "Wake word listening...")
            
            recognizer = sr.Recognizer()
            # Use sounddevice directly instead of sr.Microphone
            # This avoids PyAudio dependency
            
            # Calibrate noise level
            self._emit("listening", "Calibrating... stay silent")
            with sd.InputStream(samplerate=self._sample_rate, channels=1, dtype='int16') as stream:
                # Record 1 second for calibration
                audio_data, _ = stream.read(int(self._sample_rate * 1))
                # Convert to AudioData for recognizer
                audio_np = audio_data.flatten()
                # Calculate noise floor - use lower multiplier for quiet mic
                noise_rms = np.sqrt(np.mean(audio_np.astype(np.float64) ** 2))
                recognizer.energy_threshold = max(noise_rms * 1.5, 80)
            
            self._emit("listening", "Ready. Say 'hey jarvis'")
            
            while self._listening:
                try:
                    # Record audio using sounddevice
                    with sd.InputStream(samplerate=self._sample_rate, channels=1, dtype='int16') as stream:
                        # Listen for up to 3 seconds
                        frames = []
                        start_time = time.time()
                        silence_threshold = recognizer.energy_threshold
                        silence_duration = 0
                        min_speech_duration = 0.3
                        max_silence = 0.6
                        
                        while self._listening and (time.time() - start_time) < 4:
                            audio_chunk, _ = stream.read(1600)  # 100ms chunks
                            frames.append(audio_chunk.flatten())
                            
                            # Check energy
                            rms = np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2))
                            if rms > silence_threshold:
                                silence_duration = 0
                            else:
                                silence_duration += 0.1
                            
                            # If we had speech and then silence, stop
                            total_audio = len(np.concatenate(frames)) / self._sample_rate
                            if total_audio > min_speech_duration and silence_duration > max_silence:
                                break
                        
                        if not frames:
                            continue
                            
                        audio_np = np.concatenate(frames)

                        # Boost quiet audio for better STT
                        audio_np = self._boost_audio(audio_np)
                        
                        # Convert to AudioData for recognizer
                        wav_data = self._numpy_to_wav(audio_np)
                        audio_data = sr.AudioData(wav_data, self._sample_rate, 2)
                    
                    # Try to recognize
                    try:
                        # Try Arabic first, then English fallback
                        text = ""
                        try:
                            text = recognizer.recognize_google(audio_data, language="ar-SA").lower()
                            print(f"  Arabic: {text}")
                        except sr.UnknownValueError:
                            pass
                        except Exception as e:
                            print(f"  Arabic error: {e}")
                        
                        if not text:
                            try:
                                text = recognizer.recognize_google(audio_data, language="en-US").lower()
                                print(f"  English: {text}")
                            except sr.UnknownValueError:
                                pass
                            except Exception as e:
                                print(f"  English error: {e}")
                        
                        # Check for wake words
                        for wake in self._wake_words:
                            if wake in text:
                                now = time.time()
                                if now - self._last_trigger > self._cooldown:
                                    self._last_trigger = now
                                    self._emit("wake_word", wake)
                                    self._launch_jarvis()
                                    break
                    except sr.UnknownValueError:
                        pass  # No speech detected
                    except sr.RequestError as e:
                        self._emit("error", f"STT API: {e}")
                        time.sleep(2)
                        
                except Exception as e:
                    self._emit("error", f"Recording error: {e}")
                    time.sleep(0.5)
                    
        except Exception as e:
            self._emit("error", f"Wake word error: {e}")
        finally:
            self._listening = False
            self._emit("stopped")
    
    def _boost_audio(self, audio_np, target_rms=3000):
        """Amplify quiet audio to improve STT accuracy"""
        rms = np.sqrt(np.mean(audio_np.astype(np.float64) ** 2))
        if rms < 1:
            return audio_np
        gain = min(target_rms / rms, 10.0)
        if gain > 1.2:
            audio_np = (audio_np.astype(np.float64) * gain)
            audio_np = np.clip(audio_np, -32768, 32767).astype(np.int16)
        return audio_np

    def _numpy_to_wav(self, audio_np):
        """Convert numpy array to WAV bytes for speech_recognition"""
        import io
        import wave
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._sample_rate)
            wf.writeframes(audio_np.astype(np.int16).tobytes())
        return buf.getvalue()
    
    def _launch_jarvis(self):
        """Launch the main JARVIS app"""
        try:
            script_dir = Path(__file__).parent
            run_script = script_dir / "run_jarvis.py"
            
            if run_script.exists():
                if sys.platform == "win32":
                    subprocess.Popen(
                        [sys.executable, str(run_script)],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        cwd=str(script_dir)
                    )
                else:
                    subprocess.Popen(
                        [sys.executable, str(run_script)],
                        cwd=str(script_dir)
                    )
                self._emit("launched", "JARVIS started")
            else:
                self._emit("error", "run_jarvis.py not found")
        except Exception as e:
            self._emit("error", f"Launch failed: {e}")
    
    def start(self):
        if self._listening:
            return
        self._listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._listening = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None


def main():
    """Run as standalone wake word listener"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS Wake Word Listener")
    parser.add_argument("--install-service", action="store_true", 
                       help="Install as Windows startup service")
    args = parser.parse_args()
    
    if args.install_service:
        install_startup_service()
        return
    
    listener = WakeWordListener()
    
    def on_wake(word):
        print(f"Wake word detected: {word}")
    
    def on_launched(msg):
        print(msg)
    
    def on_error(err):
        print(f"Error: {err}")
    
    listener.on("wake_word", on_wake)
    listener.on("launched", on_launched)
    listener.on("error", on_error)
    listener.on("listening", lambda msg: print(f"Status: {msg}"))
    
    print("Starting wake word listener...")
    print("Say 'hey jarvis' to launch JARVIS")
    print("Press Ctrl+C to stop")
    
    listener.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        listener.stop()


def install_startup_service():
    """Install as Windows startup task"""
    if sys.platform != "win32":
        print("Service install only for Windows")
        return
    
    import winreg
    
    try:
        script_path = Path(__file__).resolve()
        python_exe = sys.executable
        
        # Add to Windows startup registry
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "JarvisWakeWord", 0, winreg.REG_SZ,
                         f'"{python_exe}" "{script_path}"')
        winreg.CloseKey(key)
        
        print("Wake word listener installed to startup")
        print("It will run automatically on next login")
    except Exception as e:
        print(f"Install failed: {e}")


if __name__ == "__main__":
    main()