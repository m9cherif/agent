"""
JARVIS Voice Pipeline - Main entry point.
Integrates wake word, STT, and TTS.
"""

import sys
import os
import threading
import queue

from wake_word import WakeWordDetector
from stt_engine import STTEngine
from tts_engine import TTSEngine


class VoicePipeline:
    def __init__(self):
        self.wake_detector = WakeWordDetector()
        self.stt = STTEngine()
        self.tts = TTSEngine()
        self.command_queue = queue.Queue()
        self.running = False

    def on_wake_word(self):
        print("WAKE: Wake word detected!", flush=True)
        text = self.stt.transcribe_mic(duration=5)
        if text:
            print(f"STT: {text}", flush=True)
            self.command_queue.put(text)

    def wake_loop(self):
        self.wake_detector.run()

    def process_commands(self):
        while self.running:
            try:
                command = self.command_queue.get(timeout=1)
                print(f"CMD: {command}", flush=True)
            except queue.Empty:
                continue

    def run(self):
        self.running = True

        wake_thread = threading.Thread(target=self.wake_loop, daemon=True)
        cmd_thread = threading.Thread(target=self.process_commands, daemon=True)

        wake_thread.start()
        cmd_thread.start()

        try:
            while self.running:
                import time
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.running = False


if __name__ == "__main__":
    pipeline = VoicePipeline()
    pipeline.run()
