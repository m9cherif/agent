"""
JARVIS Text-to-Speech using Coqui Piper.
Receives text via argv or stdin and plays audio.
"""

import sys
import os
import subprocess
import tempfile


class TTSEngine:
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "models",
                "piper", "en_US-lessac-medium.onnx"
            )

        self.model_path = model_path
        self.config_path = model_path.replace(".onnx", ".json")
        self.piper_binary = self._find_piper()

    def _find_piper(self) -> str:
        paths = [
            "piper",
            "piper.exe",
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "bin", "piper.exe"),
        ]
        for p in paths:
            try:
                subprocess.run([p, "--help"], capture_output=True, timeout=5)
                return p
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return "piper"

    def speak(self, text: str) -> bool:
        if not os.path.exists(self.model_path):
            print(f"ERROR: Piper model not found at {self.model_path}", flush=True)
            print("INFO: Download from: https://huggingface.co/rhasspy/piper-voices", flush=True)
            return False

        try:
            import sounddevice as sd
            import soundfile as sf
        except ImportError:
            print("ERROR: sounddevice/soundfile not installed", flush=True)
            return False

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        try:
            cmd = [
                self.piper_binary,
                "--model", self.model_path,
                "--output-raw",
            ]
            if os.path.exists(self.config_path):
                cmd.extend(["--config", self.config_path])

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            audio_bytes, stderr = process.communicate(
                input=text.encode("utf-8"), timeout=30
            )

            if process.returncode != 0:
                print(f"ERROR: Piper failed: {stderr.decode()}", flush=True)
                os.unlink(temp_path)
                return False

            sample_rate = 22050

            import numpy as np
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

            sf.write(temp_path, audio_array, sample_rate)

            data, sr = sf.read(temp_path)
            sd.play(data, sr)
            sd.wait()

            os.unlink(temp_path)
            return True

        except Exception as e:
            print(f"ERROR: TTS failed: {e}", flush=True)
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return False


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().strip()

    if not text:
        print("ERROR: No text provided for TTS", flush=True)
        sys.exit(1)

    engine = TTSEngine()
    success = engine.speak(text)
    sys.exit(0 if success else 1)
