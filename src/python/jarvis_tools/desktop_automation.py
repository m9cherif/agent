"""
JARVIS Desktop Automation via pyautogui and Windows API.
Controls mouse, keyboard, windows, and system functions.
"""

import sys
import os
import json

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5
except ImportError:
    pyautogui = None


class DesktopAutomation:
    @staticmethod
    def screenshot() -> str:
        if not pyautogui:
            return json.dumps({"error": "pyautogui not installed"})
        try:
            img = pyautogui.screenshot()
            path = os.path.join(os.environ.get("TEMP", "."), "jarvis_screenshot.png")
            img.save(path)
            return json.dumps({"path": path, "size": f"{img.width}x{img.height}"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @staticmethod
    def get_mouse_position() -> str:
        if not pyautogui:
            return json.dumps({"error": "pyautogui not installed"})
        try:
            x, y = pyautogui.position()
            return json.dumps({"x": x, "y": y})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @staticmethod
    def click(x: int = None, y: int = None, button: str = "left") -> str:
        if not pyautogui:
            return json.dumps({"error": "pyautogui not installed"})
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, button=button)
            else:
                pyautogui.click(button=button)
            return json.dumps({"success": True})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @staticmethod
    def type_text(text: str) -> str:
        if not pyautogui:
            return json.dumps({"error": "pyautogui not installed"})
        try:
            pyautogui.typewrite(text)
            return json.dumps({"success": True, "text": text})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @staticmethod
    def press_key(key: str) -> str:
        if not pyautogui:
            return json.dumps({"error": "pyautogui not installed"})
        try:
            pyautogui.press(key)
            return json.dumps({"success": True, "key": key})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @staticmethod
    def hotkey(keys: list) -> str:
        if not pyautogui:
            return json.dumps({"error": "pyautogui not installed"})
        try:
            pyautogui.hotkey(*keys)
            return json.dumps({"success": True, "keys": keys})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @staticmethod
    def get_active_window() -> str:
        try:
            import win32gui
            window = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(window)
            return json.dumps({"title": title, "handle": window})
        except ImportError:
            return json.dumps({"error": "win32gui not available"})
        except Exception as e:
            return json.dumps({"error": str(e)})


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    da = DesktopAutomation()

    actions = {
        "screenshot": da.screenshot,
        "mouse_pos": da.get_mouse_position,
        "click": lambda: da.click(
            int(sys.argv[2]) if len(sys.argv) > 2 else None,
            int(sys.argv[3]) if len(sys.argv) > 3 else None,
            sys.argv[4] if len(sys.argv) > 4 else "left"
        ),
        "type": lambda: da.type_text(sys.argv[2] if len(sys.argv) > 2 else ""),
        "press": lambda: da.press_key(sys.argv[2] if len(sys.argv) > 2 else ""),
        "hotkey": lambda: da.hotkey(sys.argv[2].split("+") if len(sys.argv) > 2 else []),
        "active_window": da.get_active_window,
    }

    result = actions.get(cmd, lambda: json.dumps({"error": "unknown command"}))()
    print(result, flush=True)
