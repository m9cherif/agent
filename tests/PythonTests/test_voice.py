"""
JARVIS Voice Pipeline Tests
"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock


class TestSTTEngine(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "src", "python"
        ))

    @patch("jarvis_voice.stt_engine.STTEngine._init_model")
    def test_stt_initialization(self, mock_init):
        from jarvis_voice.stt_engine import STTEngine
        engine = STTEngine(model_path="/mock/path")
        mock_init.assert_called_once()
        self.assertIsNotNone(engine)

    def test_stt_no_model(self):
        from jarvis_voice.stt_engine import STTEngine
        with self.assertRaises(SystemExit):
            STTEngine(model_path="/nonexistent/model.bin")


class TestTTSEngine(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "src", "python"
        ))

    @patch("jarvis_voice.tts_engine.TTSEngine._find_piper")
    def test_tts_initialization(self, mock_find):
        from jarvis_voice.tts_engine import TTSEngine
        mock_find.return_value = "piper"
        engine = TTSEngine(model_path="/mock/model.onnx")
        self.assertIsNotNone(engine)

    @patch("jarvis_voice.tts_engine.TTSEngine._find_piper")
    def test_tts_speak_no_model(self, mock_find):
        from jarvis_voice.tts_engine import TTSEngine
        mock_find.return_value = "piper"
        engine = TTSEngine(model_path="/nonexistent/model.onnx")
        result = engine.speak("Hello")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
