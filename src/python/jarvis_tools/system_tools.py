"""
JARVIS System Tools - Additional system operations.
File operations, system info, media control, clipboard.
"""

import sys
import os
import json
import subprocess
import platform
import shutil


class SystemTools:
    @staticmethod
    def get_system_info() -> str:
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "python_version": sys.version,
            "cwd": os.getcwd(),
        }
        return json.dumps(info)

    @staticmethod
    def get_env_var(name: str) -> str:
        return json.dumps({"name": name, "value": os.environ.get(name, "")})

    @staticmethod
    def set_clipboard(text: str) -> str:
        try:
            import pyperclip
            pyperclip.copy(text)
            return json.dumps({"success": True, "length": len(text)})
        except ImportError:
            return json.dumps({"error": "pyperclip not installed"})

    @staticmethod
    def get_clipboard() -> str:
        try:
            import pyperclip
            text = pyperclip.paste()
            return json.dumps({"success": True, "text": text[:1000]})
        except ImportError:
            return json.dumps({"error": "pyperclip not installed"})

    @staticmethod
    def media_control(action: str) -> str:
        try:
            import pycaw
            return json.dumps({"error": "pycaw not fully implemented"})
        except ImportError:
            pass

        actions_map = {
            "play_pause": "playpause",
            "next": "nexttrack",
            "prev": "previoustrack",
            "volume_up": "volumeup",
            "volume_down": "volumedown",
            "mute": "mute",
        }

        key = actions_map.get(action, action)
        try:
            import pyautogui
            pyautogui.press(key)
            return json.dumps({"success": True, "action": action})
        except ImportError:
            return json.dumps({"error": "pyautogui not installed"})

    @staticmethod
    def open_file_explorer(path: str = ".") -> str:
        try:
            os.startfile(os.path.abspath(path))
            return json.dumps({"success": True, "path": os.path.abspath(path)})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @staticmethod
    def get_drives() -> str:
        if sys.platform == "win32":
            try:
                import string
                from ctypes import windll
                drives = []
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drives.append(f"{letter}:\\")
                    bitmask >>= 1
                return json.dumps({"drives": drives})
            except:
                pass
        return json.dumps({"drives": []})

    @staticmethod
    def find_files(pattern: str, root: str = None) -> str:
        root = root or os.path.expanduser("~")
        try:
            results = []
            for root_dir, dirs, files in os.walk(root):
                for f in files:
                    if pattern.lower() in f.lower():
                        results.append(os.path.join(root_dir, f))
                if len(results) >= 50:
                    break
            return json.dumps({"count": len(results), "files": results[:50]})
        except Exception as e:
            return json.dumps({"error": str(e)})


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    st = SystemTools()

    actions = {
        "sysinfo": st.get_system_info,
        "env": lambda: st.get_env_var(sys.argv[2]) if len(sys.argv) > 2 else st.get_env_var(""),
        "clipboard_set": lambda: st.set_clipboard(sys.argv[2] if len(sys.argv) > 2 else ""),
        "clipboard_get": st.get_clipboard,
        "media": lambda: st.media_control(sys.argv[2] if len(sys.argv) > 2 else ""),
        "explorer": lambda: st.open_file_explorer(sys.argv[2] if len(sys.argv) > 2 else "."),
        "drives": st.get_drives,
        "find": lambda: st.find_files(
            sys.argv[2] if len(sys.argv) > 2 else "",
            sys.argv[3] if len(sys.argv) > 3 else None
        ),
    }

    result = actions.get(cmd, lambda: json.dumps({
        "commands": list(actions.keys())
    }))()
    print(result, flush=True)
