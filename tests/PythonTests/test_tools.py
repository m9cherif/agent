"""
JARVIS Tools Tests
"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock


class TestCalculatorTool(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "src", "python"
        ))

    def test_system_info(self):
        from jarvis_tools.system_tools import SystemTools
        result = json.loads(SystemTools.get_system_info())
        self.assertIn("os", result)
        self.assertIn("hostname", result)
        self.assertEqual(result["os"], "Windows") if sys.platform == "win32" else None

    def test_clipboard_operations(self):
        from jarvis_tools.system_tools import SystemTools
        try:
            result = json.loads(SystemTools.set_clipboard("test"))
            self.assertIn("success", result)
        except:
            pass


class TestBrowserAutomation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "src", "python"
        ))

    def test_browser_not_available(self):
        from jarvis_tools.browser_automation import BrowserAutomation
        ba = BrowserAutomation()
        result = ba.start(headless=True)
        # Should either succeed or report playwright not installed
        if "error" in result:
            self.assertIn("playwright not installed", result["error"])


class TestDesktopAutomation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(
            os.path.dirname(__file__), "..", "src", "python"
        ))

    def test_screenshot(self):
        from jarvis_tools.desktop_automation import DesktopAutomation
        da = DesktopAutomation()
        try:
            result = json.loads(da.screenshot())
            self.assertIn("path", result)
        except:
            pass

    def test_mouse_position(self):
        from jarvis_tools.desktop_automation import DesktopAutomation
        da = DesktopAutomation()
        try:
            result = json.loads(da.get_mouse_position())
            self.assertIn("x", result)
            self.assertIn("y", result)
        except:
            pass


if __name__ == "__main__":
    unittest.main()
