"""
JARVIS Wake Word Detection using Sherpa-ONNX.
Detects "Hey Jarvis" / "Jarvis" keyword and prints WAKE: signal.
"""

import sys
import json
import os

try:
    import sherpa_onnx
except ImportError:
    print("ERROR: sherpa_onnx not installed. Install with: pip install sherpa-onnx", flush=True)
    sys.exit(1)


class WakeWordDetector:
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "models", "sherpa"
            )

        os.makedirs(model_dir, exist_ok=True)

        self.model_dir = model_dir
        self.recognizer = None
        self._init_model()

    def _init_model(self):
        decoder_path = os.path.join(self.model_dir, "decoder.onnx")
        encoder_path = os.path.join(self.model_dir, "encoder.onnx")
        joiner_path = os.path.join(self.model_dir, "joiner.onnx")
        tokens_path = os.path.join(self.model_dir, "tokens.txt")

        if not all(os.path.exists(p) for p in [encoder_path, decoder_path, joiner_path, tokens_path]):
            print(f"ERROR: Sherpa models not found in {self.model_dir}", flush=True)
            print("INFO: Download from: https://github.com/k2-fsa/sherpa-onnx/releases", flush=True)
            print("INFO: Use 'sherpa-onnx-download' or place files manually", flush=True)
            sys.exit(1)

        try:
            self.recognizer = sherpa_onnx.OnlineRecognizer(
                tokens=tokens_path,
                encoder=encoder_path,
                decoder=decoder_path,
                joiner=joiner_path,
                num_threads=2,
                sample_rate=16000,
                feature_dim=80,
                enable_endpoint_detection=True,
                endpoint_silence_seconds=1.5,
            )
        except Exception as e:
            print(f"ERROR: Failed to init Sherpa: {e}", flush=True)
            sys.exit(1)

    def run(self):
        print("WAKE: Wake word detector started. Say 'Hey Jarvis'...", flush=True)

        try:
            import sounddevice as sd
        except ImportError:
            print("ERROR: sounddevice not installed. pip install sounddevice", flush=True)
            sys.exit(1)

        sample_rate = 16000
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            blocksize=8000,
        )

        stream.start()

        try:
            while True:
                block, _ = stream.read(8000)
                if self.recognizer:
                    self.recognizer.accept_waveform(sample_rate, block.flatten())
                    result = self.recognizer.get_result()

                    if result and ("jarvis" in result.lower() or "hey jarvis" in result.lower()):
                        print("WAKE: Jarvis detected!", flush=True)
                        self.recognizer.reset()
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop()
            stream.close()


if __name__ == "__main__":
    model_dir = sys.argv[1] if len(sys.argv) > 1 else None
    detector = WakeWordDetector(model_dir)
    detector.run()
