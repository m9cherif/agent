"""
JARVIS Speech-to-Text using whisper.cpp Python bindings.
Records audio and transcribes, printing STT: result.
"""

import sys
import os
import tempfile
import wave


class STTEngine:
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "models",
                "ggml-base.en.bin"
            )

        self.model_path = model_path
        self.whisper = None
        self._init_model()

    def _init_model(self):
        if not os.path.exists(self.model_path):
            print(f"ERROR: Whisper model not found at {self.model_path}", flush=True)
            print("INFO: Download from: https://huggingface.co/ggerganov/whisper.cpp", flush=True)
            sys.exit(1)

        try:
            import whisper_cpp_py as whisper
            self.whisper = whisper.Whisper(self.model_path)
        except ImportError:
            print("ERROR: whisper_cpp_py not installed.", flush=True)
            print("INFO: pip install whisper-cpp-py", flush=True)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to init Whisper: {e}", flush=True)
            sys.exit(1)

    def transcribe_file(self, audio_path: str) -> str:
        if not self.whisper:
            return ""

        try:
            result = self.whisper.transcribe(audio_path)
            return result.get("text", "").strip()
        except Exception as e:
            return f"ERROR: Transcription failed: {e}"

    def transcribe_mic(self, duration: int = 5):
        try:
            import sounddevice as sd
        except ImportError:
            print("ERROR: sounddevice not installed", flush=True)
            sys.exit(1)

        sample_rate = 16000
        print(f"STT: Recording for {duration} seconds...", flush=True)

        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32"
        )
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            with wave.open(f, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes((audio_data * 32767).astype("int16").tobytes())
            temp_path = f.name

        text = self.transcribe_file(temp_path)
        os.unlink(temp_path)
        return text


if __name__ == "__main__":
    engine = STTEngine()
    if len(sys.argv) > 1 and sys.argv[1] == "--file":
        text = engine.transcribe_file(sys.argv[2])
    else:
        duration = int(sys.argv[1]) if len(sys.argv) > 1 else 5
        text = engine.transcribe_mic(duration)

    print(f"STT: {text}", flush=True)
