"""JARVIS Tools - 35+ tools for web, file, system, utilities"""

import json
import os
import sys
import subprocess
import ssl
import urllib.request
import urllib.parse
import re
import random
import string
import math
import time
import tempfile
import datetime
import threading
import hashlib
import hmac
import mimetypes
import textwrap
import base64
import urllib.error

_XOR = bytes([29, 10, 96, 1, 29, 95, 63, 16, 25, 10, 5, 4, 22, 8, 66, 17, 84, 127, 89, 3, 120, 93, 95, 71, 123, 71, 82, 10, 82, 4, 16, 95, 20, 20, 85, 44, 88, 87, 116, 95, 10, 22, 124, 71, 5, 7, 1, 6, 68, 94, 79, 22, 7, 47, 15, 2, 116, 88, 9, 20, 42, 16, 5, 87, 4, 84, 69, 10, 71, 20, 89, 121, 86])
_MASK = b'naMnorI!4202sivraJ'
DEFAULT_API_KEY = bytes(a ^ b for a, b in zip(_XOR, _MASK * (len(_XOR) // len(_MASK) + 1))).decode()


class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._history = []

    def register(self, name, tool):
        self._tools[name] = tool

    def get(self, name):
        return self._tools.get(name)

    def list_tools(self):
        return list(self._tools.keys())

    def add_history(self, entry):
        self._history.append(entry)
        if len(self._history) > 50:
            self._history.pop(0)

    def get_history(self, tool=None):
        if tool:
            return [h for h in self._history if h.get("tool") == tool]
        return self._history


class BaseTool:
    def execute(self, params):
        raise NotImplementedError


class WebSearchTool(BaseTool):
    def execute(self, params):
        query = params.get("query", "")
        if not query:
            return {"success": False, "result": "No query provided"}
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=6))
            if not results:
                return {"success": True, "result": "No results found"}
            lines = []
            for r in results:
                title = r.get("title", "")
                href = r.get("href", "")
                body = r.get("body", "")
                if title and href:
                    lines.append(f"• [{title}]({href})\n  {body[:150]}")
            return {"success": True, "result": f"Results for '{query}':\n" + "\n".join(lines)}
        except Exception as e:
            return {"success": False, "result": f"Search error: {e}"}


class FileIOTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "read")
        path = params.get("path", "")
        content = params.get("content", "")
        if not path:
            return {"success": False, "result": "No path provided"}
        try:
            if action == "read":
                with open(path, "r", encoding="utf-8") as f:
                    data = f.read()
                return {"success": True, "result": data[:5000]}
            elif action == "write":
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "result": f"Saved to {os.path.basename(path)}"}
            elif action == "list":
                entries = os.listdir(path)
                files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
                dirs = [e + "/" for e in entries if os.path.isdir(os.path.join(path, e))]
                return {"success": True, "result": f"Dirs: {', '.join(dirs[:20])}\nFiles: {', '.join(files[:30])}"}
            elif action == "info":
                stat = os.stat(path)
                return {"success": True, "result":
                    f"Size: {_format_size(stat.st_size)}, Modified: {_format_time(stat.st_mtime)}"}
            elif action == "delete":
                os.remove(path)
                return {"success": True, "result": f"Deleted {path}"}
            else:
                return {"success": False, "result": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "result": f"File error: {e}"}


class SystemControlTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "")
        command = params.get("command", "")
        try:
            if action == "run" and command:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout[:2000] + ("\n" + result.stderr[:500] if result.stderr else "")
                return {"success": True, "result": output or "Done (no output)"}
            elif action == "open":
                target = params.get("target", "")
                if hasattr(os, "startfile"):
                    os.startfile(target)
                else:
                    subprocess.Popen(["xdg-open", target])
                return {"success": True, "result": f"Opened {target}"}
            else:
                return {"success": False, "result": f"Unknown action: {action}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "result": "Command timed out"}
        except Exception as e:
            return {"success": False, "result": f"System error: {e}"}


class CalculatorTool(BaseTool):
    def __init__(self):
        self.history = []

    def execute(self, params):
        expr = params.get("expression", "") or params.get("expr", "")
        if not expr:
            return {"success": False, "result": "No expression"}
        try:
            safe = re.sub(r"[^0-9+\-*/.()% eE ]", "", expr)
            result = eval(safe, {"__builtins__": {}}, {"math": math})
            entry = {"expr": expr, "result": result}
            self.history.append(entry)
            return {"success": True, "result": f"{expr} = {result}"}
        except Exception as e:
            return {"success": False, "result": f"Calc error: {e}"}


class WeatherTool(BaseTool):
    def execute(self, params):
        location = params.get("location", params.get("query", ""))
        if not location:
            return {"success": False, "result": "No location"}
        try:
            encoded = urllib.parse.quote(location)
            url = f"https://wttr.in/{encoded}?format=%C+%t+%w+%h&lang=en"
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read().decode().strip()
            data = data.encode('ascii', 'replace').decode()
            return {"success": True, "result": f"Weather in {location}: {data}"}
        except Exception as e:
            return {"success": False, "result": f"Weather error: {e}"}


class TimeTool(BaseTool):
    def execute(self, params):
        tz_name = params.get("timezone", params.get("tz", ""))
        try:
            now = datetime.datetime.now(datetime.timezone.utc).astimezone()
            result = now.strftime("%A, %B %d, %Y at %I:%M:%S %p %Z")
            utc = datetime.datetime.now(datetime.timezone.utc)
            return {"success": True, "result": f"Local time: {result}\nUTC: {utc.strftime('%Y-%m-%d %H:%M:%S UTC')}"}
        except Exception as e:
            return {"success": False, "result": f"Time error: {e}"}


class SystemInfoTool(BaseTool):
    def execute(self, params):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            boot = datetime.datetime.fromtimestamp(psutil.boot_time())
            info = (
                f"CPU: {cpu}% ({psutil.cpu_count()} cores)\n"
                f"RAM: {_format_size(mem.used)} / {_format_size(mem.total)} ({mem.percent}%)\n"
                f"Disk: {_format_size(disk.used)} / {_format_size(disk.total)} ({disk.percent}%)\n"
                f"Boot: {boot.strftime('%Y-%m-%d %H:%M')}\n"
                f"Processes: {len(psutil.pids())}"
            )
            return {"success": True, "result": info}
        except ImportError:
            import platform
            uname = platform.uname()
            return {"success": True, "result":
                f"OS: {uname.system} {uname.release}\n"
                f"Node: {uname.node}\n"
                f"Arch: {uname.machine}"}
        except Exception as e:
            return {"success": False, "result": f"Error: {e}"}


class ScreenshotTool(BaseTool):
    def execute(self, params):
        try:
            import pyautogui
            path = os.path.join(tempfile.gettempdir(), "jarvis_screenshot.png")
            img = pyautogui.screenshot(path)
            return {"success": True, "result": f"Screenshot saved: {path} ({img.width}x{img.height})"}
        except ImportError:
            return {"success": False, "result": "pyautogui not installed"}
        except Exception as e:
            return {"success": False, "result": f"Screenshot error: {e}"}


class VisionTool(BaseTool):
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", DEFAULT_API_KEY)
        self.base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = "nvidia/nemotron-nano-12b-v2-vl:free"

    def _image_to_base64(self, image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def execute(self, params):
        action = params.get("action", "analyze")
        prompt = params.get("prompt", "Describe what you see in this image")
        image_path = params.get("image", params.get("path", ""))
        
        try:
            if action == "analyze":
                if not image_path:
                    # Take screenshot
                    import pyautogui
                    path = os.path.join(tempfile.gettempdir(), f"vision_{int(time.time())}.png")
                    img = pyautogui.screenshot(path)
                    image_path = path
                
                if not os.path.exists(image_path):
                    return {"success": False, "result": "Image not found"}
                
                # Encode image
                b64 = self._image_to_base64(image_path)
                mime = mimetypes.guess_type(image_path)[0] or "image/png"
                
                # Call vision model
                import requests
                url = f"{self.base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }
                payload = {
                    "model": self.model,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
                        ]
                    }],
                    "max_tokens": 512,
                    "stream": False,
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code != 200:
                    return {"success": False, "result": f"API error: {resp.status_code} {resp.text[:200]}"}
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return {"success": True, "result": content}
                return {"success": False, "result": "No response from vision model"}
            
            elif action == "screenshot":
                import pyautogui
                path = os.path.join(tempfile.gettempdir(), f"vision_{int(time.time())}.png")
                img = pyautogui.screenshot(path)
                return {"success": True, "result": f"Screenshot saved: {path}"}
            
            return {"success": False, "result": "Actions: analyze, screenshot"}
        except ImportError:
            return {"success": False, "result": "pyautogui not installed"}
        except Exception as e:
            return {"success": False, "result": f"Vision error: {e}"}


class NotesTool(BaseTool):
    def __init__(self):
        self.notes_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "JarvisAssistant", "notes")
        os.makedirs(self.notes_dir, exist_ok=True)

    def execute(self, params):
        action = params.get("action", "list")
        title = params.get("title", params.get("name", "note"))
        content = params.get("content", params.get("text", ""))
        try:
            if action == "save":
                path = os.path.join(self.notes_dir, f"{title}.txt")
                with open(path, "w") as f:
                    f.write(content)
                return {"success": True, "result": f"Note saved: {title}"}
            elif action == "read":
                path = os.path.join(self.notes_dir, f"{title}.txt")
                if not os.path.exists(path):
                    return {"success": False, "result": f"Note '{title}' not found"}
                with open(path, "r") as f:
                    return {"success": True, "result": f"**{title}**:\n{f.read()[:2000]}"}
            elif action == "list":
                notes = [f.replace(".txt", "") for f in os.listdir(self.notes_dir) if f.endswith(".txt")]
                return {"success": True, "result": f"Notes ({len(notes)}): {', '.join(notes) or 'None'}"}
            elif action == "delete":
                path = os.path.join(self.notes_dir, f"{title}.txt")
                if os.path.exists(path):
                    os.remove(path)
                    return {"success": True, "result": f"Deleted note: {title}"}
                return {"success": False, "result": f"Note not found: {title}"}
            else:
                return {"success": False, "result": "Actions: save, read, list, delete"}
        except Exception as e:
            return {"success": False, "result": f"Notes error: {e}"}


class TodoTool(BaseTool):
    def __init__(self):
        self.todo_file = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "JarvisAssistant", "todos.json")
        os.makedirs(os.path.dirname(self.todo_file), exist_ok=True)
        if not os.path.exists(self.todo_file):
            with open(self.todo_file, "w") as f:
                json.dump([], f)

    def _load(self):
        with open(self.todo_file, "r") as f:
            return json.load(f)

    def _save(self, todos):
        with open(self.todo_file, "w") as f:
            json.dump(todos, f, indent=2)

    def execute(self, params):
        action = params.get("action", "list")
        try:
            todos = self._load()
            
            if action == "add":
                task = params.get("task", params.get("title", ""))
                if not task:
                    return {"success": False, "result": "Task required"}
                priority = params.get("priority", "medium")
                todos.append({
                    "id": str(time.time()),
                    "task": task,
                    "priority": priority,
                    "done": False,
                    "created": datetime.datetime.now().isoformat()
                })
                self._save(todos)
                return {"success": True, "result": f"Added: {task}"}
            
            elif action == "list":
                filter_done = params.get("filter")
                if filter_done == "active":
                    todos = [t for t in todos if not t["done"]]
                elif filter_done == "done":
                    todos = [t for t in todos if t["done"]]
                
                if not todos:
                    return {"success": True, "result": "No tasks"}
                
                lines = []
                for t in todos:
                    status = "✓" if t["done"] else "☐"
                    pri = t.get("priority", "medium")[0].upper()
                    lines.append(f"{status} [{pri}] {t['task']}")
                return {"success": True, "result": "\n".join(lines)}
            
            elif action == "done":
                task_id = params.get("id")
                for t in todos:
                    if t["id"] == task_id:
                        t["done"] = True
                        self._save(todos)
                        return {"success": True, "result": f"Completed: {t['task']}"}
                return {"success": False, "result": "Task not found"}
            
            elif action == "remove":
                task_id = params.get("id")
                todos = [t for t in todos if t["id"] != task_id]
                self._save(todos)
                return {"success": True, "result": "Removed"}
            
            elif action == "clear":
                self._save([t for t in todos if not t["done"]])
                return {"success": True, "result": "Cleared completed"}
            
            return {"success": False, "result": "Actions: add, list, done, remove, clear"}
        except Exception as e:
            return {"success": False, "result": f"Todo error: {e}"}


class ClipboardTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "get")
        text = params.get("text", "")
        try:
            import pyperclip
            if action == "get":
                content = pyperclip.paste()
                return {"success": True, "result": f"Clipboard: {content[:500]}"}
            elif action == "set":
                pyperclip.copy(text)
                return {"success": True, "result": f"Copied: {text[:100]}"}
            else:
                return {"success": False, "result": "Actions: get, set"}
        except ImportError:
            return {"success": False, "result": "pyperclip not installed"}


class DictTool(BaseTool):
    def execute(self, params):
        word = params.get("word", params.get("query", ""))
        if not word:
            return {"success": False, "result": "No word"}
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())[0]
            meanings = data.get("meanings", [])
            parts = []
            for m in meanings[:3]:
                defs = m.get("definitions", [])[:2]
                def_texts = [f"  - {d.get('definition', '')}" for d in defs]
                parts.append(f"*{m.get('partOfSpeech', '?')}*:\n" + "\n".join(def_texts))
            phonetic = data.get("phonetic", data.get("phonetics", [{}])[0].get("text", ""))
            result = f"**{word}** {phonetic}\n" + "\n".join(parts)
            return {"success": True, "result": result}
        except urllib.error.HTTPError as e:
            return {"success": False, "result": f"Word not found" if e.code == 404 else f"Error: {e}"}
        except Exception as e:
            return {"success": False, "result": f"Dict error: {e}"}


class JokesTool(BaseTool):
    def execute(self, params):
        try:
            url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,racist,sexist&format=txt"
            req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                joke = resp.read().decode().strip()
            return {"success": True, "result": joke}
        except Exception as e:
            return {"success": False, "result": f"Joke error: {e}"}


class QuoteTool(BaseTool):
    FALLBACKS = [
        '"The only way to do great work is to love what you do." — Steve Jobs',
        '"In the middle of every difficulty lies opportunity." — Albert Einstein',
        '"Be yourself; everyone else is already taken." — Oscar Wilde',
        '"Two things are infinite: the universe and human stupidity." — Albert Einstein',
        '"The best time to plant a tree was 20 years ago. The second best time is now." — Chinese Proverb',
    ]

    def execute(self, params):
        for url in [
            "https://zenquotes.io/api/random",
            "https://api.quotable.io/random",
            "https://quotes.rest/qod",
        ]:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/1.0"})
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                    data = json.loads(resp.read())
                    if isinstance(data, list) and data:
                        q = data[0]
                        return {"success": True, "result": f'"{q.get("q", q.get("content", ""))}"\n— {q.get("a", q.get("author", ""))}'}
                    if isinstance(data, dict):
                        quotes = data.get("quotes", [data])
                        if quotes:
                            q = quotes[0]
                            return {"success": True, "result": f'"{q.get("quote", q.get("content", ""))}"\n— {q.get("author", q.get("title", ""))}'}
            except Exception:
                continue
        return {"success": True, "result": random.choice(self.FALLBACKS)}


class PasswordTool(BaseTool):
    def execute(self, params):
        length = params.get("length", 16)
        include_symbols = params.get("symbols", True)
        try:
            length = max(4, min(128, int(length)))
            chars = string.ascii_letters + string.digits
            if include_symbols:
                chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            pwd = "".join(random.choice(chars) for _ in range(length))
            return {"success": True, "result": f"Password ({length} chars): `{pwd}`"}
        except Exception as e:
            return {"success": False, "result": f"Error: {e}"}


class ConvertTool(BaseTool):
    UNITS = {
        "length": {"m": 1, "km": 1000, "cm": 0.01, "mm": 0.001, "mi": 1609.34, "ft": 0.3048, "in": 0.0254},
        "mass": {"kg": 1, "g": 0.001, "lb": 0.453592, "oz": 0.0283495, "t": 1000},
        "temp": {"c": "c", "f": "f", "k": "k"},
        "speed": {"m/s": 1, "km/h": 0.277778, "mph": 0.44704, "knot": 0.514444},
    }

    def execute(self, params):
        value = params.get("value")
        from_unit = params.get("from", "")
        to_unit = params.get("to", "")
        category = params.get("category", self._detect_category(from_unit, to_unit))
        if value is None or not from_unit or not to_unit:
            return {"success": False, "result": "Usage: value=X, from=unit, to=unit"}
        try:
            value = float(value)
            if category == "temp":
                if from_unit == "c" and to_unit == "f":
                    result = value * 9/5 + 32
                elif from_unit == "f" and to_unit == "c":
                    result = (value - 32) * 5/9
                elif from_unit == "c" and to_unit == "k":
                    result = value + 273.15
                elif from_unit == "k" and to_unit == "c":
                    result = value - 273.15
                else:
                    return {"success": False, "result": "Unsupported temp conversion"}
            else:
                units = self.UNITS.get(category, {})
                if from_unit not in units or to_unit not in units:
                    return {"success": False, "result": f"Unknown units. Available: {list(units.keys())}"}
                result = value * units[from_unit] / units[to_unit]
            return {"success": True, "result": f"{value} {from_unit} = {result:.4f} {to_unit}"}
        except Exception as e:
            return {"success": False, "result": f"Convert error: {e}"}

    def _detect_category(self, a, b):
        for cat, units in self.UNITS.items():
            if a in units or b in units:
                return cat
        return "length"


class FileSearchTool(BaseTool):
    def execute(self, params):
        pattern = params.get("pattern", "")
        root = params.get("path", os.path.expanduser("~"))
        if not pattern:
            return {"success": False, "result": "No search pattern"}
        try:
            results = []
            for dirpath, dirnames, filenames in os.walk(root):
                for f in filenames:
                    if pattern.lower() in f.lower():
                        results.append(os.path.join(dirpath, f))
                        if len(results) >= 30:
                            break
                if len(results) >= 30:
                    break
            if results:
                return {"success": True, "result": f"Found {len(results)}:\n" + "\n".join(results[:20])}
            return {"success": True, "result": "No files found"}
        except Exception as e:
            return {"success": False, "result": f"Search error: {e}"}


class BatteryTool(BaseTool):
    def execute(self, params):
        try:
            import psutil
            batt = psutil.sensors_battery()
            if not batt:
                return {"success": True, "result": "No battery detected"}
            pct = batt.percent
            plugged = "Charging" if batt.power_plugged else "On battery"
            secs = batt.secsleft
            time_left = f"{secs // 3600}h {secs % 3600 // 60}m" if secs != -1 else "Unknown"
            return {"success": True, "result": f"Battery: {pct}% ({plugged})\nTime left: {time_left}"}
        except ImportError:
            return {"success": False, "result": "psutil not installed"}
        except Exception as e:
            return {"success": False, "result": f"Battery error: {e}"}


class ProcessTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "list")
        name = params.get("name", "")
        try:
            import psutil
            if action == "list":
                procs = []
                for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                    try:
                        procs.append(f"{p.info['pid']:6d} {p.info['name'][:30]:30s} "
                                     f"CPU:{p.info['cpu_percent'] or 0:5.1f}% MEM:{p.info['memory_percent'] or 0:5.1f}%")
                    except:
                        pass
                return {"success": True, "result": "Processes:\n" + "\n".join(procs[:30])}
            elif action == "kill" and name:
                for p in psutil.process_iter(["pid", "name"]):
                    if name.lower() in p.info["name"].lower():
                        p.kill()
                        return {"success": True, "result": f"Killed {p.info['name']} (PID {p.info['pid']})"}
                return {"success": False, "result": f"No process matching '{name}'"}
            else:
                return {"success": False, "result": "Actions: list, kill"}
        except ImportError:
            return {"success": False, "result": "psutil not installed"}
        except Exception as e:
            return {"success": False, "result": f"Error: {e}"}


class RandomTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "number")
        try:
            if action == "number":
                min_n = int(params.get("min", 1))
                max_n = int(params.get("max", 100))
                return {"success": True, "result": f"Random number between {min_n} and {max_n}: {random.randint(min_n, max_n)}"}
            elif action == "coin":
                return {"success": True, "result": f"Coin flip: {random.choice(['Heads', 'Tails'])}"}
            elif action == "dice":
                sides = int(params.get("sides", 6))
                return {"success": True, "result": f"D{sides} roll: {random.randint(1, sides)}"}
            elif action == "choice":
                options = params.get("options", "")
                items = [x.strip() for x in options.split(",") if x.strip()]
                if items:
                    return {"success": True, "result": f"Chose: {random.choice(items)}"}
                return {"success": False, "result": "No options provided (comma-separated)"}
            elif action == "uuid":
                import uuid
                return {"success": True, "result": f"UUID: {uuid.uuid4()}"}
            else:
                return {"success": False, "result": "Actions: number, coin, dice, choice, uuid"}
        except Exception as e:
            return {"success": False, "result": f"Error: {e}"}


class NewsTool(BaseTool):
    def execute(self, params):
        topic = params.get("topic", params.get("query", ""))
        try:
            import xml.etree.ElementTree as ET
            if topic:
                url = f"https://news.google.com/rss/search?q={urllib.parse.quote(topic)}&hl=en-US&gl=US&ceid=US:en"
            else:
                url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                tree = ET.parse(resp)
            root = tree.getroot()
            items = root.findall(".//item")[:8]
            if not items:
                return {"success": False, "result": "No news found. Try a different topic."}
            lines = []
            for item in items:
                title = item.findtext("title", "")
                source = item.findtext("source", "")
                if source:
                    lines.append(f"• [{source}] {title[:150]}")
                else:
                    lines.append(f"• {title[:150]}")
            return {"success": True, "result": (f"News about '{topic}':\n" if topic else "Top headlines:\n") + "\n".join(lines)}
        except Exception as e:
            return {"success": False, "result": f"News error: {e}"}


class ShortenTool(BaseTool):
    def execute(self, params):
        url = params.get("url", "")
        if not url:
            return {"success": False, "result": "No URL provided"}
        try:
            data = urllib.parse.urlencode({"url": url}).encode()
            req = urllib.request.Request("https://is.gd/create.php?format=simple",
                                         data=data,
                                         headers={"User-Agent": "Jarvis/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                short = resp.read().decode().strip()
            if short and not short.startswith("Error"):
                return {"success": True, "result": f"Shortened: {short}"}
            return {"success": False, "result": f"Shorten failed: {short}"}
        except Exception as e:
            return {"success": False, "result": f"Error: {e}"}


class IPGeoTool(BaseTool):
    def execute(self, params):
        ip = params.get("ip", params.get("query", ""))
        try:
            if ip:
                url = f"http://ip-api.com/json/{urllib.parse.quote(ip)}"
            else:
                url = "http://ip-api.com/json/"
            req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            if data.get("status") == "success":
                return {"success": True, "result":
                    f"IP: {data.get('query', 'N/A')}\n"
                    f"Location: {data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}\n"
                    f"ISP: {data.get('isp', 'N/A')}\n"
                    f"Lat/Lon: {data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}"}
            return {"success": False, "result": "Could not determine location"}
        except Exception as e:
            return {"success": False, "result": f"Error: {e}"}


class EmailTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "send")
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = params.get("smtp_server", "smtp.gmail.com")
            smtp_port = int(params.get("smtp_port", 587))
            username = params.get("username", "")
            password = params.get("password", "")
            
            if action == "send":
                to = params.get("to", "")
                subject = params.get("subject", "")
                body = params.get("body", "")
                if not all([to, subject, body, username, password]):
                    return {"success": False, "result": "Missing: to, subject, body, username, password"}
                
                msg = MIMEMultipart()
                msg["From"] = username
                msg["To"] = to
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))
                
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(username, password)
                    server.send_message(msg)
                return {"success": True, "result": f"Email sent to {to}"}
            
            elif action == "check":
                import imaplib
                mail = imaplib.IMAP4_SSL(params.get("imap_server", "imap.gmail.com"))
                mail.login(username, password)
                mail.select("inbox")
                _, data = mail.search(None, "UNSEEN")
                count = len(data[0].split()) if data[0] else 0
                mail.logout()
                return {"success": True, "result": f"Unread emails: {count}"}
            
            return {"success": False, "result": "Actions: send, check"}
        except Exception as e:
            return {"success": False, "result": f"Email error: {e}"}


class CalendarTool(BaseTool):
    def __init__(self):
        self.events_file = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "JarvisAssistant", "calendar.json")
        os.makedirs(os.path.dirname(self.events_file), exist_ok=True)
        if not os.path.exists(self.events_file):
            with open(self.events_file, "w") as f:
                json.dump([], f)
    
    def _load(self):
        with open(self.events_file, "r") as f:
            return json.load(f)
    
    def _save(self, events):
        with open(self.events_file, "w") as f:
            json.dump(events, f, indent=2)
    
    def execute(self, params):
        action = params.get("action", "list")
        try:
            events = self._load()
            now = datetime.datetime.now().isoformat()
            
            if action == "add":
                title = params.get("title", "")
                start = params.get("start", now)
                end = params.get("end", "")
                desc = params.get("description", "")
                if not title:
                    return {"success": False, "result": "Title required"}
                event = {"id": str(time.time()), "title": title, "start": start, "end": end, "description": desc}
                events.append(event)
                self._save(events)
                return {"success": True, "result": f"Event added: {title} at {start}"}
            
            elif action == "list":
                days = int(params.get("days", 7))
                cutoff = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
                upcoming = [e for e in events if e["start"] <= cutoff]
                upcoming.sort(key=lambda x: x["start"])
                if not upcoming:
                    return {"success": True, "result": "No upcoming events"}
                lines = [f"{e['start'][:16]} - {e['title']}" for e in upcoming[:20]]
                return {"success": True, "result": f"Upcoming ({len(upcoming)}):\n" + "\n".join(lines)}
            
            elif action == "delete":
                eid = params.get("id", "")
                events = [e for e in events if e["id"] != eid]
                self._save(events)
                return {"success": True, "result": f"Event {eid} deleted"}
            
            return {"success": False, "result": "Actions: add, list, delete"}
        except Exception as e:
            return {"success": False, "result": f"Calendar error: {e}"}


class ReminderTool(BaseTool):
    def __init__(self):
        self.reminders_file = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "JarvisAssistant", "reminders.json")
        os.makedirs(os.path.dirname(self.reminders_file), exist_ok=True)
        if not os.path.exists(self.reminders_file):
            with open(self.reminders_file, "w") as f:
                json.dump([], f)
        self._running = False
        self._thread = None
    
    def _load(self):
        with open(self.reminders_file, "r") as f:
            return json.load(f)
    
    def _save(self, reminders):
        with open(self.reminders_file, "w") as f:
            json.dump(reminders, f, indent=2)
    
    def execute(self, params):
        action = params.get("action", "list")
        try:
            reminders = self._load()
            
            if action == "add":
                text = params.get("text", "")
                when = params.get("when", "")
                if not text or not when:
                    return {"success": False, "result": "Need text and when (ISO datetime or seconds)"}
                try:
                    if when.isdigit():
                        trigger = datetime.datetime.now() + datetime.timedelta(seconds=int(when))
                    else:
                        trigger = datetime.datetime.fromisoformat(when)
                except:
                    return {"success": False, "result": "Invalid time format. Use seconds or ISO datetime"}
                reminder = {"id": str(time.time()), "text": text, "trigger": trigger.isoformat(), "done": False}
                reminders.append(reminder)
                self._save(reminders)
                self._start_monitor()
                return {"success": True, "result": f"Reminder set for {trigger.strftime('%Y-%m-%d %H:%M')}: {text}"}
            
            elif action == "list":
                pending = [r for r in reminders if not r["done"]]
                if not pending:
                    return {"success": True, "result": "No pending reminders"}
                lines = [f"{r['trigger'][:16]} - {r['text']}" for r in pending]
                return {"success": True, "result": f"Reminders ({len(pending)}):\n" + "\n".join(lines)}
            
            elif action == "clear":
                self._save([r for r in reminders if r["done"]])
                return {"success": True, "result": "Completed reminders cleared"}
            
            return {"success": False, "result": "Actions: add, list, clear"}
        except Exception as e:
            return {"success": False, "result": f"Reminder error: {e}"}
    
    def _start_monitor(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
    
    def _monitor(self):
        import win10toast
        toaster = win10toast.ToastNotifier()
        while self._running:
            time.sleep(10)
            reminders = self._load()
            now = datetime.datetime.now()
            changed = False
            for r in reminders:
                if not r["done"]:
                    trigger = datetime.datetime.fromisoformat(r["trigger"])
                    if now >= trigger:
                        try:
                            toaster.show_toast("JARVIS Reminder", r["text"], duration=10)
                        except:
                            pass
                        r["done"] = True
                        changed = True
            if changed:
                self._save(reminders)


class TimerTool(BaseTool):
    def __init__(self):
        self.timers = {}
    
    def execute(self, params):
        action = params.get("action", "start")
        name = params.get("name", "default")
        try:
            if action == "start":
                seconds = int(params.get("seconds", params.get("duration", 60)))
                end_time = time.time() + seconds
                self.timers[name] = {"end": end_time, "paused": False, "elapsed": 0}
                return {"success": True, "result": f"Timer '{name}' started for {seconds}s"}
            
            elif action == "pause":
                if name in self.timers and not self.timers[name]["paused"]:
                    self.timers[name]["elapsed"] += time.time() - self.timers[name]["end"] + self.timers[name]["elapsed"]
                    self.timers[name]["paused"] = True
                    return {"success": True, "result": f"Timer '{name}' paused"}
                return {"success": False, "result": "Timer not running"}
            
            elif action == "resume":
                if name in self.timers and self.timers[name]["paused"]:
                    self.timers[name]["end"] = time.time() + (self.timers[name]["elapsed"] - time.time())
                    self.timers[name]["paused"] = False
                    return {"success": True, "result": f"Timer '{name}' resumed"}
                return {"success": False, "result": "Timer not paused"}
            
            elif action == "stop":
                if name in self.timers:
                    elapsed = self.timers[name].get("elapsed", 0) + (time.time() - self.timers[name]["end"]) + self.timers[name].get("elapsed", 0)
                    del self.timers[name]
                    return {"success": True, "result": f"Timer '{name}' stopped after {int(elapsed)}s"}
                return {"success": False, "result": "Timer not found"}
            
            elif action == "status":
                if name in self.timers:
                    t = self.timers[name]
                    if t["paused"]:
                        remaining = t["elapsed"]
                    else:
                        remaining = t["end"] - time.time() + t.get("elapsed", 0)
                    return {"success": True, "result": f"Timer '{name}': {int(max(0, remaining))}s remaining"}
                return {"success": False, "result": "Timer not found"}
            
            elif action == "list":
                if not self.timers:
                    return {"success": True, "result": "No active timers"}
                lines = []
                for n, t in self.timers.items():
                    rem = t.get("elapsed", 0) + (t["end"] - time.time()) if not t["paused"] else t.get("elapsed", 0)
                    lines.append(f"{n}: {int(max(0, rem))}s {'(paused)' if t['paused'] else ''}")
                return {"success": True, "result": "Timers:\n" + "\n".join(lines)}
            
            return {"success": False, "result": "Actions: start, pause, resume, stop, status, list"}
        except Exception as e:
            return {"success": False, "result": f"Timer error: {e}"}


class TranslatorTool(BaseTool):
    def execute(self, params):
        text = params.get("text", "")
        target = params.get("target", "en")
        source = params.get("source", "en")
        if source == "auto":
            source = "en"
        if target == "auto":
            target = "en"
        if not text:
            return {"success": False, "result": "No text to translate"}
        try:
            url = "https://api.mymemory.translated.net/get"
            data = urllib.parse.urlencode({"q": text, "langpair": f"{source}|{target}"}).encode()
            req = urllib.request.Request(url, data=data, headers={"User-Agent": "Jarvis/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
            translated = result.get("responseData", {}).get("translatedText", "")
            if not translated:
                return {"success": False, "result": "Translation failed"}
            return {"success": True, "result": f"Translated ({source}→{target}):\n{translated}"}
        except Exception as e:
            return {"success": False, "result": f"Translation error: {e}"}


class CryptoTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "hash")
        data = params.get("data", "")
        algorithm = params.get("algorithm", "sha256")
        key = params.get("key", "")
        try:
            if action == "hash":
                h = hashlib.new(algorithm)
                h.update(data.encode())
                return {"success": True, "result": f"{algorithm.upper()}: {h.hexdigest()}"}
            
            elif action == "hmac":
                if not key:
                    return {"success": False, "result": "Key required for HMAC"}
                h = hmac.new(key.encode(), data.encode(), getattr(hashlib, algorithm))
                return {"success": True, "result": f"HMAC-{algorithm.upper()}: {h.hexdigest()}"}
            
            elif action == "encode":
                encoded = base64.b64encode(data.encode()).decode()
                return {"success": True, "result": f"Base64: {encoded}"}
            
            elif action == "decode":
                decoded = base64.b64decode(data).decode()
                return {"success": True, "result": f"Decoded: {decoded}"}
            
            elif action == "file_hash":
                if not os.path.exists(data):
                    return {"success": False, "result": "File not found"}
                h = hashlib.new(algorithm)
                with open(data, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                return {"success": True, "result": f"{algorithm.upper()}({os.path.basename(data)}): {h.hexdigest()}"}
            
            return {"success": False, "result": "Actions: hash, hmac, encode, decode, file_hash"}
        except Exception as e:
            return {"success": False, "result": f"Crypto error: {e}"}


class QRCodeTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "generate")
        data = params.get("data", "")
        try:
            import qrcode
            if action == "generate":
                if not data:
                    return {"success": False, "result": "No data provided"}
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                path = os.path.join(tempfile.gettempdir(), f"qrcode_{int(time.time())}.png")
                img.save(path)
                return {"success": True, "result": f"QR code saved: {path}"}
            
            elif action == "decode":
                from PIL import Image
                import pyzbar.pyzbar as pyzbar
                img_path = data
                if not os.path.exists(img_path):
                    return {"success": False, "result": "Image file not found"}
                img = Image.open(img_path)
                decoded = pyzbar.decode(img)
                if decoded:
                    return {"success": True, "result": f"Decoded: {decoded[0].data.decode()}"}
                return {"success": False, "result": "No QR code found in image"}
            
            return {"success": False, "result": "Actions: generate, decode"}
        except ImportError:
            return {"success": False, "result": "Install: pip install qrcode[pil] pyzbar"}
        except Exception as e:
            return {"success": False, "result": f"QR error: {e}"}


class WindowTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "list")
        try:
            import win32gui
            import win32con
            
            if action == "list":
                windows = []
                def enum_handler(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            windows.append(f"{hwnd}: {title[:80]}")
                win32gui.EnumWindows(enum_handler, None)
                return {"success": True, "result": f"Windows ({len(windows)}):\n" + "\n".join(windows[:30])}
            
            elif action == "get_rect":
                hwnd = int(params.get("hwnd", 0))
                if not hwnd:
                    return {"success": False, "result": "Need hwnd"}
                rect = win32gui.GetWindowRect(hwnd)
                l, t, r, b = rect
                return {"success": True, "result":
                    f"Window rect: left={l}, top={t}, right={r}, bottom={b}, "
                    f"width={r-l}, height={b-t}, center=({(l+r)//2}, {(t+b)//2})"}
            
            elif action == "maximize":
                hwnd = int(params.get("hwnd", 0))
                name = params.get("name", "").lower()
                if not hwnd and name:
                    hwnd = self._find_window(name)
                if not hwnd:
                    return {"success": False, "result": "Specify hwnd or window name"}
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                win32gui.SetForegroundWindow(hwnd)
                return {"success": True, "result": "Window maximized"}
            
            elif action == "minimize":
                hwnd = int(params.get("hwnd", 0))
                name = params.get("name", "").lower()
                if not hwnd and name:
                    hwnd = self._find_window(name)
                if not hwnd:
                    return {"success": False, "result": "Specify hwnd or window name"}
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                return {"success": True, "result": "Window minimized"}
            
            elif action == "restore":
                hwnd = int(params.get("hwnd", 0))
                name = params.get("name", "").lower()
                if not hwnd and name:
                    hwnd = self._find_window(name)
                if not hwnd:
                    return {"success": False, "result": "Specify hwnd or window name"}
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return {"success": True, "result": "Window restored"}
            
            elif action == "focus":
                hwnd = int(params.get("hwnd", 0))
                name = params.get("name", "").lower()
                if not hwnd and name:
                    hwnd = self._find_window(name)
                if not hwnd:
                    return {"success": False, "result": "Specify hwnd or window name"}
                win32gui.SetForegroundWindow(hwnd)
                return {"success": True, "result": "Window focused"}
            
            elif action == "close":
                hwnd = int(params.get("hwnd", 0))
                name = params.get("name", "").lower()
                if not hwnd and name:
                    hwnd = self._find_window(name)
                if not hwnd:
                    return {"success": False, "result": "Specify hwnd or window name"}
                win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return {"success": True, "result": "Window close sent"}
            
            elif action == "move":
                hwnd = int(params.get("hwnd", 0))
                name = params.get("name", "").lower()
                if not hwnd and name:
                    hwnd = self._find_window(name)
                if not hwnd:
                    return {"success": False, "result": "Specify hwnd or window name"}
                x = int(params.get("x", 0))
                y = int(params.get("y", 0))
                w = int(params.get("width", params.get("w", 800)))
                h = int(params.get("height", params.get("h", 600)))
                win32gui.SetWindowPos(hwnd, 0, x, y, w, h, win32con.SWP_NOZORDER)
                return {"success": True, "result": f"Window moved to ({x},{y}) size {w}x{h}"}
            
            return {"success": False, "result": "Actions: list, get_rect, maximize, minimize, restore, focus, close, move [name/hwnd]"}
        except ImportError:
            return {"success": False, "result": "pywin32 not installed"}
        except Exception as e:
            return {"success": False, "result": f"Window error: {e}"}

    def _find_window(self, name):
        import win32gui
        targets = []
        def enum_handler(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if name in title:
                    targets.append(hwnd)
        win32gui.EnumWindows(enum_handler, None)
        if targets:
            return targets[0]
        return 0


class AudioTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "volume")
        try:
            from pycaw.pycaw import AudioUtilities
            
            device = AudioUtilities.GetSpeakers()
            volume = device.EndpointVolume
            
            if action == "volume":
                level = params.get("level")
                if level is not None:
                    vol = max(0.0, min(1.0, float(level) / 100))
                    volume.SetMasterVolumeLevelScalar(vol, None)
                    return {"success": True, "result": f"Volume set to {level}%"}
                else:
                    current = int(volume.GetMasterVolumeLevelScalar() * 100)
                    return {"success": True, "result": f"Current volume: {current}%"}
            
            elif action == "mute":
                mute = params.get("mute", True)
                volume.SetMute(1 if mute else 0, None)
                return {"success": True, "result": f"Muted: {mute}"}
            
            elif action == "list_devices":
                devs = AudioUtilities.GetAllDevices()
                return {"success": True, "result": "Devices: " + ", ".join([d.FriendlyName for d in devs])}
            
            return {"success": False, "result": "Actions: volume, mute, list_devices"}
        except ImportError:
            return {"success": False, "result": "pycaw not installed: pip install pycaw comtypes"}
        except Exception as e:
            return {"success": False, "result": f"Audio error: {e}"}


class NetworkTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "info")
        try:
            import psutil
            if action == "info":
                addrs = psutil.net_if_addrs()
                stats = psutil.net_if_stats()
                io = psutil.net_io_counters()
                lines = [f"Interfaces: {len(addrs)}", f"Bytes sent: {_format_size(io.bytes_sent)}", f"Bytes recv: {_format_size(io.bytes_recv)}"]
                for name, addrs_list in addrs.items():
                    for addr in addrs_list:
                        if addr.family == 2:
                            lines.append(f"{name}: {addr.address}")
                return {"success": True, "result": "\n".join(lines)}
            
            elif action == "connections":
                conns = psutil.net_connections(kind="inet")
                lines = [f"{c.laddr.ip}:{c.laddr.port} -> {c.raddr.ip if c.raddr else '*'}:{c.raddr.port if c.raddr else '*'} [{c.status}]" for c in conns[:30]]
                return {"success": True, "result": "Connections:\n" + "\n".join(lines)}
            
            elif action == "ping":
                host = params.get("host", "8.8.8.8")
                import platform
                param = "-n" if platform.system().lower() == "windows" else "-c"
                cmd = ["ping", param, "4", host]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                return {"success": True, "result": result.stdout[-500:]}
            
            elif action == "speed":
                return {"success": False, "result": "Speed test not implemented (requires external API)"}
            
            return {"success": False, "result": "Actions: info, connections, ping, speed"}
        except ImportError:
            return {"success": False, "result": "psutil not installed"}
        except Exception as e:
            return {"success": False, "result": f"Network error: {e}"}


class ArchiveTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "create")
        paths = params.get("paths", [])
        archive = params.get("archive", "")
        try:
            import shutil
            import zipfile
            import tarfile
            
            if not paths:
                return {"success": False, "result": "No paths provided"}
            if not archive:
                return {"success": False, "result": "No archive name"}
            
            if action == "create":
                if archive.endswith(".zip"):
                    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
                        for p in paths:
                            if os.path.isdir(p):
                                for root, dirs, files in os.walk(p):
                                    for f in files:
                                        fp = os.path.join(root, f)
                                        zf.write(fp, os.path.relpath(fp, os.path.dirname(p)))
                            else:
                                zf.write(p, os.path.basename(p))
                    return {"success": True, "result": f"Created {archive} with {len(paths)} items"}
                
                elif archive.endswith(".tar.gz") or archive.endswith(".tgz"):
                    with tarfile.open(archive, "w:gz") as tf:
                        for p in paths:
                            tf.add(p, os.path.basename(p))
                    return {"success": True, "result": f"Created {archive}"}
                
                else:
                    return {"success": False, "result": "Supported: .zip, .tar.gz, .tgz"}
            
            elif action == "extract":
                dest = params.get("dest", ".")
                if archive.endswith(".zip"):
                    with zipfile.ZipFile(archive, "r") as zf:
                        zf.extractall(dest)
                elif archive.endswith(".tar.gz") or archive.endswith(".tgz"):
                    with tarfile.open(archive, "r:gz") as tf:
                        tf.extractall(dest)
                else:
                    return {"success": False, "result": "Supported: .zip, .tar.gz, .tgz"}
                return {"success": True, "result": f"Extracted {archive} to {dest}"}
            
            elif action == "list":
                files = []
                if archive.endswith(".zip"):
                    with zipfile.ZipFile(archive, "r") as zf:
                        files = zf.namelist()
                elif archive.endswith(".tar.gz") or archive.endswith(".tgz"):
                    with tarfile.open(archive, "r:gz") as tf:
                        files = tf.getnames()
                else:
                    return {"success": False, "result": "Supported: .zip, .tar.gz, .tgz"}
                return {"success": True, "result": f"Contents ({len(files)}):\n" + "\n".join(files[:50])}
            
            return {"success": False, "result": "Actions: create, extract, list"}
        except Exception as e:
            return {"success": False, "result": f"Archive error: {e}"}


class JsonTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "parse")
        data = params.get("data", "")
        path = params.get("path", "")
        try:
            if action == "parse":
                if not data:
                    return {"success": False, "result": "No JSON data"}
                parsed = json.loads(data)
                return {"success": True, "result": json.dumps(parsed, indent=2)[:3000]}
            
            elif action == "query":
                if not data or not path:
                    return {"success": False, "result": "Need data and path (e.g. $.store.book[0].author)"}
                parsed = json.loads(data)
                import jsonpath_ng
                expr = jsonpath_ng.parse(path)
                matches = [m.value for m in expr.find(parsed)]
                return {"success": True, "result": json.dumps(matches, indent=2)[:3000]}
            
            elif action == "validate":
                if not data:
                    return {"success": False, "result": "No JSON data"}
                json.loads(data)
                return {"success": True, "result": "Valid JSON"}
            
            elif action == "format":
                if not data:
                    return {"success": False, "result": "No JSON data"}
                parsed = json.loads(data)
                return {"success": True, "result": json.dumps(parsed, indent=2)}
            
            return {"success": False, "result": "Actions: parse, query, validate, format"}
        except ImportError:
            return {"success": False, "result": "jsonpath-ng not installed: pip install jsonpath-ng"}
        except json.JSONDecodeError as e:
            return {"success": False, "result": f"Invalid JSON: {e}"}
        except Exception as e:
            return {"success": False, "result": f"JSON error: {e}"}


class HashTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "string")
        data = params.get("data", "")
        algorithm = params.get("algorithm", "sha256")
        try:
            if action == "string":
                if not data:
                    return {"success": False, "result": "No data"}
                h = hashlib.new(algorithm)
                h.update(data.encode())
                return {"success": True, "result": f"{algorithm.upper()}: {h.hexdigest()}"}
            
            elif action == "file":
                if not os.path.exists(data):
                    return {"success": False, "result": "File not found"}
                h = hashlib.new(algorithm)
                with open(data, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
                return {"success": True, "result": f"{algorithm.upper()}({os.path.basename(data)}): {h.hexdigest()}"}
            
            elif action == "compare":
                expected = params.get("expected", "")
                h = hashlib.new(algorithm)
                h.update(data.encode())
                match = hmac.compare_digest(h.hexdigest(), expected.lower())
                return {"success": True, "result": f"Match: {match}"}
            
            return {"success": False, "result": "Actions: string, file, compare"}
        except Exception as e:
            return {"success": False, "result": f"Hash error: {e}"}


class OCRTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "image")
        path = params.get("path", params.get("image", ""))
        if not path or not os.path.exists(path):
            return {"success": False, "result": "Image file not found"}
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            if not text.strip():
                return {"success": True, "result": "No text detected"}
            return {"success": True, "result": text[:3000]}
        except ImportError:
            return {"success": False, "result": "OCR unavailable. Install: pip install pytesseract"}
        except Exception as e:
            msg = str(e).lower()
            if "tesseract" in msg and "path" in msg:
                return {"success": False, "result": "Tesseract not installed. OCR unavailable."}
            return {"success": False, "result": f"OCR error: {e}"}


class ScreenWatchTool(BaseTool):
    """Real-time screen monitoring - captures at 2fps, detects changes, latest frame always available"""

    def __init__(self):
        self._last_frame = None
        self._last_frame_ts = 0
        self._last_description = ""
        self._last_analysis_ts = 0
        self._running = True
        self._lock = threading.Lock()
        self._change_pct = 0.0
        self._frame_buffer = []
        self._monitor_idx = 1
        self._vision_model = "nvidia/nemotron-nano-12b-v2-vl:free"
        self._vision_fallbacks = [
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "google/gemma-4-26b-a4b-it:free",
        ]
        self._vision_idx = 0
        self._start_monitor()

    def _start_monitor(self):
        threading.Thread(target=self._capture_loop, daemon=True).start()

    def _capture_loop(self):
        import mss
        import numpy as np
        from PIL import Image
        import time
        try:
            with mss.mss() as sct:
                while self._running:
                    try:
                        mon = sct.monitors[self._monitor_idx] if self._monitor_idx < len(sct.monitors) else sct.monitors[1]
                        raw = np.array(sct.grab(mon))
                        img = Image.fromarray(raw[:, :, :3])
                        now = time.time()
                        with self._lock:
                            if self._last_frame is not None:
                                old = np.array(self._last_frame.resize((64, 48)), dtype=np.float32)
                                new = np.array(img.resize((64, 48)), dtype=np.float32)
                                diff = np.mean(np.abs(old - new)) / 255.0
                                self._change_pct = diff * 100
                            else:
                                self._change_pct = 100
                            self._last_frame = img
                            self._last_frame_ts = now
                            self._frame_buffer.append((now, img))
                            if len(self._frame_buffer) > 10:
                                self._frame_buffer.pop(0)
                    except Exception:
                        pass
                    time.sleep(0.5)
        except ImportError:
            pass

    def execute(self, params):
        action = params.get("action", "read")
        try:
            if action == "read":
                with self._lock:
                    description = self._last_description
                    change = self._change_pct
                    age = time.time() - self._last_analysis_ts if self._last_analysis_ts else 0
                    frame = self._last_frame
                if description:
                    return {"success": True, "result": f"[Screen {change:.0f}% change, {age:.0f}s ago]\n{description}"}
                if frame is None:
                    return {"success": False, "result": "Screen monitoring starting up, no frame captured yet. Try again in 1 second."}
                w, h = frame.size
                return {"success": True, "result": f"Screen: {w}x{h}, {change:.0f}% change since last check. Running vision analysis..."}

            elif action == "capture":
                prompt = params.get("prompt", "Describe this screen briefly.")
                return self._do_analyze(prompt)

            elif action == "start":
                self._running = True
                return {"success": True, "result": "Screen monitoring running at 2fps"}

            elif action == "stop":
                self._running = False
                return {"success": True, "result": "Screen monitoring stopped"}

            elif action == "status":
                with self._lock:
                    return {"success": True, "result":
                        f"Monitoring: {'active' if self._running else 'stopped'}\n"
                        f"Change: {self._change_pct:.0f}%\n"
                        f"Last analysis: {time.time() - self._last_analysis_ts:.0f}s ago\n"
                        f"Frame buffer: {len(self._frame_buffer)} frames"}

            return {"success": False, "result": "Actions: read, capture, start, stop, status"}
        except ImportError as e:
            return {"success": False, "result": f"Missing: {e}"}
        except Exception as e:
            return {"success": False, "result": f"Screen watch error: {e}"}

    def _do_analyze(self, prompt):
        with self._lock:
            if self._last_frame is None:
                return {"success": False, "result": "No frame captured yet"}
            img = self._last_frame.copy()
        # Return local description instantly (no API call)
        w, h = img.size
        import numpy as np
        arr = np.array(img.resize((16, 12)))
        avg = arr.mean(axis=(0, 1))
        brightness = "bright" if avg.mean() > 128 else "dim"
        dom = f"rgb({int(avg[0])},{int(avg[1])},{int(avg[2])})"
        change = self._change_pct if hasattr(self, '_change_pct') else 0
        result = f"Screen: {w}x{h}, {brightness}, dominant {dom}, {change:.0f}% change."
        # Fire-and-forget vision API to update cache for next read
        threading.Thread(target=self._analyze_via_api, args=(img, prompt), daemon=True).start()
        return {"success": True, "result": result}

    def _analyze_via_api(self, img, prompt):
        import tempfile, base64, requests, os, time
        path = os.path.join(tempfile.gettempdir(), f"sw_{int(time.time())}.png")
        img.save(path)
        try:
            api_key = os.environ.get("OPENROUTER_API_KEY", DEFAULT_API_KEY)
            base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            models_to_try = self._vision_fallbacks
            for model in models_to_try:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                    ]}],
                    "max_tokens": 256,
                    "stream": False,
                }
                try:
                    resp = requests.post(url, headers=headers, json=payload, timeout=5)
                    if resp.status_code == 429:
                        continue
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "")
                            if content:
                                with self._lock:
                                    self._last_description = content
                                    self._last_analysis_ts = time.time()
                                return
                except Exception:
                    continue
        finally:
            try: os.remove(path)
            except: pass


class InputControlTool(BaseTool):
    """Ultra-fast real-time mouse/keyboard using SendInput (reliable on modern Windows)"""
    
    MOUSE_BUTTONS = {"left": 0, "right": 1, "middle": 2}
    _INPUT_MOUSE = 0
    
    @staticmethod
    def _send_click(flags_down, flags_up, dx=0, dy=0):
        import ctypes
        from ctypes import wintypes
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INPUT_U(ctypes.Union):
            _fields_ = [("mi", MOUSEINPUT)]
        class INPUT(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("u", INPUT_U)]
        down = INPUT(0, INPUT_U(MOUSEINPUT(dx, dy, 0, flags_down, 0, None)))
        up = INPUT(0, INPUT_U(MOUSEINPUT(dx, dy, 0, flags_up, 0, None)))
        arr = (INPUT * 2)(down, up)
        ctypes.windll.user32.SendInput(2, arr, ctypes.sizeof(INPUT))

    VK_MAP = {
        "enter": 0x0D, "tab": 0x09, "shift": 0x10, "ctrl": 0x11, "alt": 0x12,
        "space": 0x20, "backspace": 0x08, "delete": 0x2E, "escape": 0x1B,
        "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
        "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
        "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74,
        "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79,
        "f11": 0x7A, "f12": 0x7B, "capslock": 0x14, "printscreen": 0x2C,
        "scrolllock": 0x91, "pause": 0x13, "insert": 0x2D,
        "win": 0x5B, "menu": 0x5D, "numlock": 0x90,
        "volumemute": 0xAD, "volumedown": 0xAE, "volumeup": 0xAF,
        "nexttrack": 0xB0, "prevtrack": 0xB1, "mediastop": 0xB2, "playpause": 0xB3,
        "browserback": 0xA6, "browserforward": 0xA7, "browserrefresh": 0xA8,
        "sleep": 0x5F, "zoom": 0xFB,
        "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
        "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
        "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45,
        "f": 0x46, "g": 0x47, "h": 0x48, "i": 0x49, "j": 0x4A,
        "k": 0x4B, "l": 0x4C, "m": 0x4D, "n": 0x4E, "o": 0x4F,
        "p": 0x50, "q": 0x51, "r": 0x52, "s": 0x53, "t": 0x54,
        "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58, "y": 0x59, "z": 0x5A,
        "semicolon": 0xBA, "equals": 0xBB, "comma": 0xBC, "minus": 0xBD,
        "period": 0xBE, "slash": 0xBF, "backtick": 0xC0,
        "lbracket": 0xDB, "backslash": 0xDC, "rbracket": 0xDD, "quote": 0xDE,
    }

    def execute(self, params):
        action = params.get("action", "")
        try:
            import win32api
            import win32con
            import win32gui
            
            if action == "move":
                x = int(params.get("x", 0))
                y = int(params.get("y", 0))
                win32api.SetCursorPos((x, y))
                return {"success": True, "result": f"Moved to ({x}, {y})"}
            
            elif action == "move_rel":
                dx = int(params.get("dx", 0))
                dy = int(params.get("dy", 0))
                cx, cy = win32api.GetCursorPos()
                win32api.SetCursorPos((cx + dx, cy + dy))
                return {"success": True, "result": f"Moved relative ({dx}, {dy})"}
            
            elif action == "click":
                button = params.get("button", "left").lower()
                b = self.MOUSE_BUTTONS.get(button, 0)
                x = params.get("x")
                y = params.get("y")
                if x is not None and y is not None:
                    win32api.SetCursorPos((int(x), int(y)))
                    import time; time.sleep(0.05)
                flags = [win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_RIGHTDOWN,
                         win32con.MOUSEEVENTF_MIDDLEDOWN][b]
                flags_up = [win32con.MOUSEEVENTF_LEFTUP, win32con.MOUSEEVENTF_RIGHTUP,
                           win32con.MOUSEEVENTF_MIDDLEUP][b]
                self._send_click(flags, flags_up)
                import time; time.sleep(0.03)
                clicks = params.get("clicks", 1)
                for _ in range(clicks - 1):
                    self._send_click(flags, flags_up)
                return {"success": True, "result": f"Clicked {button} {clicks}x"}
            
            elif action == "drag":
                x = int(params.get("x", 0))
                y = int(params.get("y", 0))
                dx = int(params.get("dx", 0))
                dy = int(params.get("dy", 0))
                button = params.get("button", "left").lower()
                b = self.MOUSE_BUTTONS.get(button, 0)
                flags = [win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_RIGHTDOWN,
                         win32con.MOUSEEVENTF_MIDDLEDOWN][b]
                flags_up = [win32con.MOUSEEVENTF_LEFTUP, win32con.MOUSEEVENTF_RIGHTUP,
                           win32con.MOUSEEVENTF_MIDDLEUP][b]
                win32api.SetCursorPos((x, y))
                self._send_click(flags, flags, dx=0, dy=0)
                import time; time.sleep(0.05)
                win32api.SetCursorPos((x + dx, y + dy))
                self._send_click(flags_up, flags_up, dx=0, dy=0)
                import time; time.sleep(0.03)
                return {"success": True, "result": f"Dragged ({dx}, {dy})"}
            
            elif action == "scroll":
                import ctypes
                clicks = int(params.get("clicks", 1))
                ctypes.windll.user32.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, clicks * 120, 0)
                return {"success": True, "result": f"Scrolled {clicks}"}
            
            elif action == "type":
                text = params.get("text", "")
                if not text:
                    return {"success": False, "result": "Need text"}
                for ch in text:
                    vk = win32api.VkKeyScan(ch)
                    vkey = vk & 0xFF
                    shift = (vk >> 8) & 1
                    if shift:
                        win32api.keybd_event(0x10, 0, 0, 0)
                    win32api.keybd_event(vkey, 0, 0, 0)
                    win32api.keybd_event(vkey, 0, win32con.KEYEVENTF_KEYUP, 0)
                    if shift:
                        win32api.keybd_event(0x10, 0, win32con.KEYEVENTF_KEYUP, 0)
                return {"success": True, "result": f"Typed {len(text)} chars"}
            
            elif action == "press":
                key = params.get("key", "").lower()
                vk = self.VK_MAP.get(key)
                if vk is None:
                    vk = ord(key.upper()) if len(key) == 1 else 0
                if not vk:
                    return {"success": False, "result": f"Unknown key: {key}"}
                win32api.keybd_event(vk, 0, 0, 0)
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                return {"success": True, "result": f"Pressed {key}"}
            
            elif action == "hotkey":
                keys = params.get("keys", [])
                mod_map = {"ctrl": 0x11, "alt": 0x12, "shift": 0x10, "win": 0x5B}
                mods_down = []
                for k in keys:
                    k = k.lower()
                    if k in mod_map:
                        vk = mod_map[k]
                        win32api.keybd_event(vk, 0, 0, 0)
                        mods_down.append(vk)
                for k in keys:
                    k = k.lower()
                    if k not in mod_map:
                        vk = self.VK_MAP.get(k, ord(k.upper()) if len(k) == 1 else 0)
                        if vk:
                            win32api.keybd_event(vk, 0, 0, 0)
                            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                for vk in reversed(mods_down):
                    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                return {"success": True, "result": f"Hotkey: {'+'.join(keys)}"}
            
            elif action == "keydown":
                key = params.get("key", "").lower()
                vk = self.VK_MAP.get(key, ord(key.upper()) if len(key) == 1 else 0)
                if not vk:
                    return {"success": False, "result": f"Unknown key: {key}"}
                win32api.keybd_event(vk, 0, 0, 0)
                return {"success": True, "result": f"Key down: {key}"}
            
            elif action == "keyup":
                key = params.get("key", "").lower()
                vk = self.VK_MAP.get(key, ord(key.upper()) if len(key) == 1 else 0)
                if not vk:
                    return {"success": False, "result": f"Unknown key: {key}"}
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                return {"success": True, "result": f"Key up: {key}"}
            
            elif action == "position":
                x, y = win32api.GetCursorPos()
                return {"success": True, "result": f"Mouse at ({x}, {y})"}
            
            elif action == "screenshot":
                import pyautogui
                path = params.get("path", os.path.join(tempfile.gettempdir(), f"screenshot_{int(time.time())}.png"))
                pyautogui.screenshot(path)
                return {"success": True, "result": f"Screenshot saved: {path}"}
            
            return {"success": False, "result": "Actions: move, move_rel, click, drag, scroll, type, press, hotkey, keydown, keyup, position, screenshot"}
        
        except ImportError:
            return {"success": False, "result": "win32api not installed (pywin32 required)"}
        except Exception as e:
            return {"success": False, "result": f"Input error: {e}"}


def _format_size(bytes_val):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def _format_time(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


class EditTool(BaseTool):
    """Edit files by exact string replacement (like opencode edit)"""
    def execute(self, params):
        path = params.get("filePath", params.get("path", ""))
        old = params.get("old", params.get("oldString", ""))
        new = params.get("new", params.get("newString", ""))
        replace_all = params.get("replaceAll", False)
        if not path or not old:
            return {"success": False, "result": "Need filePath and old string"}
        if new is None:
            return {"success": False, "result": "Need new string"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if replace_all:
                if old not in content:
                    return {"success": False, "result": "String not found in file"}
                new_content = content.replace(old, new)
            else:
                if content.count(old) > 1:
                    return {"success": False, "result": f"Found {content.count(old)} matches. Use replaceAll=True or provide more context"}
                if old not in content:
                    return {"success": False, "result": "String not found in file"}
                new_content = content.replace(old, new, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return {"success": True, "result": f"Edited {os.path.basename(path)}"}
        except Exception as e:
            return {"success": False, "result": f"Edit error: {e}"}


class GrepTool(BaseTool):
    """Search file contents using regex (like opencode grep)"""
    def execute(self, params):
        pattern = params.get("pattern", "")
        path = params.get("path", params.get("include", ""))
        if not pattern:
            return {"success": False, "result": "No pattern provided"}
        try:
            matches = []
            if path and os.path.isfile(path):
                files = [path]
            elif path and os.path.isdir(path):
                import fnmatch
                inc = params.get("include", "*")
                files = []
                for root, dirs, fnames in os.walk(path):
                    for f in fnmatch.filter(fnames, inc):
                        files.append(os.path.join(root, f))
                    if params.get("max_depth"):
                        depth = root.replace(path, "").count(os.sep)
                        if depth >= int(params["max_depth"]):
                            dirs.clear()
            else:
                files = []
                for root, dirs, fnames in os.walk("."):
                    inc = params.get("include", "*.{py,js,ts,jsx,tsx,html,css,json,md,txt}")
                    import fnmatch
                    for f in fnmatch.filter(fnames, inc):
                        files.append(os.path.join(root, f))
                    if len(files) >= 100:
                        break
            for fp in files:
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                short = fp[:100] if len(fp) > 100 else fp
                                matches.append(f"{short}:{i}: {line.rstrip()[:150]}")
                except Exception:
                    pass
                if len(matches) >= params.get("max_results", 50):
                    break
            if not matches:
                return {"success": True, "result": "No matches found"}
            return {"success": True, "result": f"Found {len(matches)} matches:\n" + "\n".join(matches[:params.get("max_results", 50)])}
        except Exception as e:
            return {"success": False, "result": f"Grep error: {e}"}


class GlobTool(BaseTool):
    """Find files by glob pattern (like opencode glob)"""
    def execute(self, params):
        pattern = params.get("pattern", "")
        path = params.get("path", ".")
        if not pattern:
            return {"success": False, "result": "No pattern provided"}
        try:
            import fnmatch
            matches = []
            if os.path.isfile(path):
                root = os.path.dirname(path) or "."
            else:
                root = path
            for r, dirs, fnames in os.walk(root):
                matches.extend(os.path.join(r, f) for f in fnmatch.filter(fnames, pattern))
                matches.extend(r + "/" for d in dirs if fnmatch.fnmatch(d, pattern))
                if len(matches) >= params.get("max_results", 100):
                    break
            matches.sort(key=lambda x: os.path.getmtime(x) if os.path.isfile(x) else 0, reverse=True)
            if not matches:
                return {"success": True, "result": "No files found"}
            lines = [f if os.path.isfile(f) else f"{f}/ (dir)" for f in matches[:params.get("max_results", 100)]]
            return {"success": True, "result": f"Found {len(matches)} files:\n" + "\n".join(lines)}
        except Exception as e:
            return {"success": False, "result": f"Glob error: {e}"}


class ApplyPatchTool(BaseTool):
    """Apply patch/diff to files"""
    def execute(self, params):
        patch_text = params.get("patchText", params.get("patch", params.get("text", "")))
        reverse = params.get("reverse", False)
        if not patch_text:
            return {"success": False, "result": "No patch text provided"}
        try:
            import subprocess
            with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
                f.write(patch_text)
                patch_path = f.name
            cmd = ["git", "apply"]
            if reverse:
                cmd.append("-R")
            cmd.append(patch_path)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            os.unlink(patch_path)
            if r.returncode == 0:
                return {"success": True, "result": "Patch applied successfully"}
            # Fallback: try patch command
            r2 = subprocess.run(["patch", "-p1"], input=patch_text, capture_output=True, text=True, timeout=30)
            if r2.returncode == 0:
                return {"success": True, "result": "Patch applied via patch command"}
            return {"success": False, "result": f"Patch failed: {r.stderr or r2.stderr}"[:500]}
        except Exception as e:
            return {"success": False, "result": f"Patch error: {e}"}


class WebFetchTool(BaseTool):
    """Fetch web content from a URL"""
    def execute(self, params):
        url = params.get("url", "")
        fmt = params.get("format", "text")
        if not url:
            return {"success": False, "result": "No URL provided"}
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JarvisAssistant/3.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            if fmt == "json" or url.endswith(".json"):
                return {"success": True, "result": json.loads(data.decode("utf-8"))}
            text = data.decode("utf-8", errors="replace")
            import html
            text = re.sub(r'<[^>]+>', ' ', html.unescape(text))
            text = re.sub(r'\s+', ' ', text).strip()
            return {"success": True, "result": text[:5000]}
        except Exception as e:
            return {"success": False, "result": f"Fetch error: {e}"}


class QuestionTool(BaseTool):
    """Ask user a question and return answer. Set pending question; answer checked on next input."""
    def __init__(self):
        self.pending_question = None
        self.pending_answer = None

    def execute(self, params):
        q = params.get("question", params.get("text", ""))
        options = params.get("options", [])
        if not q:
            return {"success": False, "result": "No question provided"}
        desc = q[:200]
        if options:
            desc += " Options: " + ", ".join(o.get("label", str(o)) if isinstance(o, dict) else str(o) for o in options)
        # Return the question - orchestrator will read it aloud
        return {"success": True, "result": f"QUESTION: {desc}", "_is_question": True}


class SkillTool(BaseTool):
    """Load a skill/instruction file (SKILL.md or custom)"""
    def execute(self, params):
        name = params.get("name", "")
        path = params.get("path", "")
        if path:
            skill_path = path
        elif name:
            skill_path = os.path.join(os.path.dirname(__file__), "..", f"{name}.md")
            if not os.path.exists(skill_path):
                skill_path = os.path.join(os.path.dirname(__file__), "..", "skills", f"{name}.md")
        else:
            return {"success": False, "result": "Need name or path"}
        if not os.path.exists(skill_path):
            return {"success": False, "result": f"Skill not found: {skill_path}"}
        try:
            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "result": f"Skill '{os.path.basename(skill_path)}':\n{content[:3000]}"}
        except Exception as e:
            return {"success": False, "result": f"Skill error: {e}"}


class TodoWriteTool(BaseTool):
    """Enhanced todo list management with task tracking (like opencode todowrite)"""
    def __init__(self):
        self.todo_file = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "JarvisAssistant", "todos.json")
        os.makedirs(os.path.dirname(self.todo_file), exist_ok=True)
        if not os.path.exists(self.todo_file):
            with open(self.todo_file, "w") as f:
                json.dump([], f)

    def _load(self):
        with open(self.todo_file, "r") as f:
            return json.load(f)

    def _save(self, todos):
        with open(self.todo_file, "w") as f:
            json.dump(todos, f, indent=2)

    def execute(self, params):
        action = params.get("action", params.get("status", "list"))
        todos = self._load()
        try:
            if action in ("add", "new"):
                content = params.get("content", params.get("task", ""))
                priority = params.get("priority", "medium")
                status = params.get("status", "pending")
                if not content:
                    return {"success": False, "result": "No task content"}
                todos.append({
                    "id": str(time.time()),
                    "content": content,
                    "priority": priority,
                    "status": status,
                    "created": datetime.datetime.now().isoformat()
                })
                self._save(todos)
                return {"success": True, "result": f"Todo added: {content}"}

            if action in ("list", "pending"):
                filter_status = params.get("status", "pending" if action == "pending" else None)
                items = [t for t in todos if not filter_status or t.get("status") == filter_status]
                if not items:
                    return {"success": True, "result": "No todos" if filter_status else f"No {filter_status} todos"}
                lines = [f"[{t.get('priority','m')[0].upper()}] {t['content']} (id:{t['id'][-6:]})" for t in items]
                return {"success": True, "result": "\n".join(lines)}

            if action in ("done", "complete", "finish"):
                task_id = params.get("id", "")
                for t in todos:
                    if t["id"] == task_id or t["id"].endswith(task_id):
                        t["status"] = "completed"
                        self._save(todos)
                        return {"success": True, "result": f"Completed: {t['content']}"}
                return {"success": False, "result": "Task not found"}

            if action == "in_progress":
                task_id = params.get("id", "")
                for t in todos:
                    if t["id"] == task_id or t["id"].endswith(task_id):
                        t["status"] = "in_progress"
                        self._save(todos)
                        return {"success": True, "result": f"In progress: {t['content']}"}
                return {"success": False, "result": "Task not found"}

            if action in ("remove", "delete"):
                task_id = params.get("id", "")
                todos = [t for t in todos if t["id"] != task_id and not t["id"].endswith(task_id)]
                self._save(todos)
                return {"success": True, "result": "Removed"}

            if action in ("clear", "clean"):
                self._save([])
                return {"success": True, "result": "All todos cleared"}

            return {"success": False, "result": "Actions: add, list, done, in_progress, remove, clear"}
        except Exception as e:
            return {"success": False, "result": f"Todo error: {e}"}


# ===== New Tools =====

class VolumeControlTool(BaseTool):
    """Get or set system volume level"""
    def execute(self, params):
        action = params.get("action", "get")
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from ctypes import cast, POINTER
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            if action == "get":
                level = volume.GetMasterVolumeLevelScalar() * 100
                mute = volume.GetMute()
                return {"success": True, "result": f"Volume: {level:.0f}%{' (muted)' if mute else ''}"}
            elif action == "set":
                pct = max(0, min(100, int(params.get("level", 50)))) / 100
                volume.SetMasterVolumeLevelScalar(pct, None)
                return {"success": True, "result": f"Volume set to {pct*100:.0f}%"}
            elif action == "mute":
                volume.SetMute(True, None)
                return {"success": True, "result": "Muted"}
            elif action == "unmute":
                volume.SetMute(False, None)
                return {"success": True, "result": "Unmuted"}
            return {"success": False, "result": "Actions: get, set, mute, unmute"}
        except Exception:
            if action == "get":
                return {"success": True, "result": "Volume: unknown (pycaw not available)"}
            if action == "mute":
                self._send_media_key(0xAD)
                return {"success": True, "result": "Toggled mute"}
            if action == "set":
                level = max(0, min(100, int(params.get("level", 50))))
                for _ in range(abs(level - 50) // 2):
                    self._send_media_key(0xAF if level > 50 else 0xAE)
                return {"success": True, "result": f"Adjusted volume toward {level}%"}
            return {"success": False, "result": "Volume control unavailable"}

    def _send_media_key(self, vk):
        import ctypes
        user32 = ctypes.windll.user32
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(vk, 0, 2, 0)


class MediaControlTool(BaseTool):
    """Control media playback (play/pause/next/prev)"""
    def execute(self, params):
        action = params.get("action", "play_pause")
        import ctypes
        user32 = ctypes.windll.user32
        keys = {
            "play_pause": 0xB3,
            "next": 0xB0,
            "prev": 0xB1,
            "stop": 0xB2,
        }
        vk = keys.get(action)
        if not vk:
            return {"success": False, "result": "Actions: play_pause, next, prev, stop"}
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(vk, 0, 2, 0)
        return {"success": True, "result": f"Media: {action}"}


class NotificationTool(BaseTool):
    """Send Windows toast notification"""
    def execute(self, params):
        title = params.get("title", "JARVIS")
        message = params.get("message", params.get("text", ""))[:256]
        duration = params.get("duration", 3)
        try:
            from win10toast import ToastNotifier
            n = ToastNotifier()
            n.show_toast(title, message, duration=duration, threaded=True)
            return {"success": True, "result": f"Notification sent: {message[:60]}..." if len(message) > 60 else f"Notification sent: {message}"}
        except ImportError:
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1000)
                return {"success": True, "result": "Notification shown via MessageBox"}
            except Exception:
                return {"success": False, "result": "Notification failed"}


class DiskTool(BaseTool):
    """Check disk, CPU, and RAM usage"""
    def execute(self, params):
        target = params.get("target", "all")
        results = []
        import psutil
        if target in ("all", "cpu"):
            pct = psutil.cpu_percent(interval=0.5)
            results.append(f"CPU: {pct:.0f}%")
        if target in ("all", "ram"):
            mem = psutil.virtual_memory()
            results.append(f"RAM: {mem.percent:.0f}% used ({mem.used // 1024**3}GB/{mem.total // 1024**3}GB)")
        if target in ("all", "disk"):
            for part in psutil.disk_partitions():
                if part.fstype:
                    usage = psutil.disk_usage(part.mountpoint)
                    results.append(f"{part.device}: {usage.percent:.0f}% ({usage.free // 1024**3}GB free)")
        if not results:
            return {"success": False, "result": "Specify: cpu, ram, disk, or all"}
        return {"success": True, "result": " | ".join(results)}


class WallpaperTool(BaseTool):
    """Set desktop wallpaper"""
    def execute(self, params):
        path = params.get("path", params.get("url", ""))
        style = params.get("style", "fill")
        if not path:
            return {"success": False, "result": "Path required"}
        if path.startswith("http://") or path.startswith("https://"):
            import urllib.request
            ext = path.rsplit(".", 1)[-1] if "." in path else "jpg"
            f = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
            fpath = f.name
            f.close()
            try:
                urllib.request.urlretrieve(path, fpath)
                path = fpath
            except Exception as e:
                return {"success": False, "result": f"Download failed: {e}"}
        else:
            fpath = path
        if not os.path.isfile(fpath):
            return {"success": False, "result": "File not found"}
        try:
            import ctypes
            SPI_SETDESKWALLPAPER = 20
            styles = {"fill": 10, "fit": 6, "stretch": 2, "tile": 0, "center": 0}
            key = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, fpath, 2)
            if key:
                return {"success": True, "result": f"Wallpaper set: {os.path.basename(fpath)}"}
            return {"success": False, "result": "Failed to set wallpaper"}
        except Exception as e:
            return {"success": False, "result": f"Error: {e}"}


class LockScreenTool(BaseTool):
    """Lock the workstation"""
    def execute(self, params):
        action = params.get("action", "lock")
        import ctypes
        if action == "lock":
            ctypes.windll.user32.LockWorkStation()
            return {"success": True, "result": "Workstation locked"}
        elif action == "logoff":
            ctypes.windll.user32.ExitWindowsEx(0, 0)
            return {"success": True, "result": "Logging off"}
        elif action == "sleep":
            ctypes.windll.user32.SetSuspendState(False, True, False)
            return {"success": True, "result": "Sleep mode"}
        return {"success": False, "result": "Actions: lock, logoff, sleep"}


class BrowserTool(BaseTool):
    """Open URL in default browser"""
    def execute(self, params):
        url = params.get("url", params.get("query", ""))
        new_tab = params.get("new_tab", True)
        if not url:
            return {"success": False, "result": "URL required"}
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        import webbrowser
        webbrowser.open(url, new=2 if new_tab else 0, autoraise=True)
        return {"success": True, "result": f"Opened: {url}"}


class EnvTool(BaseTool):
    """Get environment variables and system paths"""
    def execute(self, params):
        action = params.get("action", "get")
        name = params.get("name", params.get("var", ""))
        if action == "get":
            if name:
                val = os.environ.get(name, "")
                return {"success": True, "result": f"{name}={val}" if val else f"{name} not set"}
            return {"success": True, "result": "\n".join(f"{k}={v[:80]}" for k, v in sorted(os.environ.items())[:20])}
        elif action == "paths":
            paths = os.environ.get("PATH", "").split(os.pathsep)
            return {"success": True, "result": "\n".join(paths[:15])}
        elif action == "home":
            return {"success": True, "result": f"Home: {os.path.expanduser('~')}"}
        elif action == "temp":
            return {"success": True, "result": f"Temp: {tempfile.gettempdir()}"}
        return {"success": False, "result": "Actions: get [name], paths, home, temp"}


class ColorTool(BaseTool):
    """Convert between color formats (hex, rgb, hsl)"""
    def execute(self, params):
        fmt = params.get("format", params.get("to", "hex"))
        value = params.get("value", params.get("color", ""))
        if not value:
            return {"success": False, "result": "Color value required"}
        value = value.strip().lower()
        try:
            if value.startswith("#"):
                h = value.lstrip("#")
                r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            elif value.startswith("rgb"):
                nums = re.findall(r'\d+', value)
                r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
            elif value.startswith("hsl"):
                import colorsys
                nums = re.findall(r'[\d.]+', value)
                h, s, l = float(nums[0])/360, float(nums[1])/100, float(nums[2])/100
                r, g, b = [int(x*255) for x in colorsys.hls_to_rgb(h, l, s)]
            else:
                return {"success": False, "result": "Format: #hex, rgb(R,G,B), or hsl(H,S,L)"}
            if fmt == "hex":
                return {"success": True, "result": f"#{r:02x}{g:02x}{b:02x}"}
            if fmt == "rgb":
                return {"success": True, "result": f"rgb({r},{g},{b})"}
            if fmt == "hsl":
                import colorsys
                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                return {"success": True, "result": f"hsl({h*360:.0f},{s*100:.0f}%,{v*100:.0f}%)"}
            return {"success": True, "result": f"RGB({r},{g},{b}) HEX:#{r:02x}{g:02x}{b:02x}"}
        except Exception as e:
            return {"success": False, "result": f"Color error: {e}"}


class UnitTool(BaseTool):
    """Convert between units (temperature, length, weight, etc.)"""
    def execute(self, params):
        value = params.get("value", "0")
        fr = params.get("from", "").lower()
        to = params.get("to", "").lower()
        try:
            val = float(value)
        except (ValueError, TypeError):
            return {"success": False, "result": "Invalid numeric value"}
        if not fr or not to:
            return {"success": False, "result": "Specify 'from' and 'to' units"}
        conversions = {
            # Temperature
            ("c", "f"): lambda v: v * 9/5 + 32,
            ("f", "c"): lambda v: (v - 32) * 5/9,
            ("c", "k"): lambda v: v + 273.15,
            ("k", "c"): lambda v: v - 273.15,
            # Length
            ("m", "ft"): lambda v: v * 3.28084,
            ("ft", "m"): lambda v: v / 3.28084,
            ("km", "mi"): lambda v: v * 0.621371,
            ("mi", "km"): lambda v: v / 0.621371,
            ("cm", "in"): lambda v: v / 2.54,
            ("in", "cm"): lambda v: v * 2.54,
            # Weight
            ("kg", "lb"): lambda v: v * 2.20462,
            ("lb", "kg"): lambda v: v / 2.20462,
            ("g", "oz"): lambda v: v / 28.3495,
            ("oz", "g"): lambda v: v * 28.3495,
            # Data
            ("mb", "gb"): lambda v: v / 1024,
            ("gb", "mb"): lambda v: v * 1024,
        }
        fn = conversions.get((fr, to))
        if not fn:
            available = ", ".join(sorted(set(f"{a}→{b}" for a, b in conversions)))
            return {"success": False, "result": f"Unknown pair. Try: {available}"}
        result = fn(val)
        return {"success": True, "result": f"{val} {fr} = {result:.4f} {to}"}


class MathEvalTool(BaseTool):
    """Safe math expression evaluator with common functions"""
    def execute(self, params):
        expr = params.get("expression", params.get("expr", ""))
        if not expr:
            return {"success": False, "result": "Expression required"}
        try:
            import math as m
            allowed = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "sqrt": m.sqrt,
                "sin": m.sin, "cos": m.cos, "tan": m.tan,
                "asin": m.asin, "acos": m.acos, "atan": m.atan,
                "log": m.log, "log10": m.log10, "exp": m.exp,
                "pi": m.pi, "e": m.e,
            }
            result = eval(expr, {"__builtins__": {}}, allowed)
            return {"success": True, "result": f"{result}"}
        except Exception as e:
            return {"success": False, "result": f"Math error: {e}"}


class IdleTool(BaseTool):
    """Get system idle time and uptime"""
    def execute(self, params):
        import ctypes
        target = params.get("target", "all")
        results = []
        if target in ("all", "idle"):
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                secs = millis // 1000
                results.append(f"Idle: {secs // 60}m {secs % 60}s")
            else:
                results.append("Idle: unknown")
        if target in ("all", "uptime"):
            millis = ctypes.windll.kernel32.GetTickCount()
            secs = millis // 1000
            results.append(f"Uptime: {secs // 3600}h {(secs % 3600) // 60}m")
        if target in ("all", "os"):
            results.append(f"OS: {os.environ.get('OS', 'Windows')}")
        if target in ("all", "user"):
            results.append(f"User: {os.environ.get('USERNAME', '')}")
        return {"success": True, "result": " | ".join(results)}


class PublicIPTool(BaseTool):
    def execute(self, params):
        try:
            import urllib.request
            with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=10) as r:
                data = json.loads(r.read())
            return {"success": True, "result": data.get("ip", "unknown")}
        except Exception as e:
            return {"success": False, "result": f"IP error: {e}"}


class PingTool(BaseTool):
    def execute(self, params):
        host = params.get("host", "8.8.8.8")
        count = params.get("count", 4)
        try:
            param = "-n" if sys.platform == "win32" else "-c"
            r = subprocess.run(["ping", param, str(count), host], capture_output=True, text=True, timeout=30)
            out = r.stdout or r.stderr
            lines = [l.strip() for l in out.split("\n") if l.strip()]
            return {"success": True, "result": "; ".join(lines[-6:-1]) if len(lines) > 1 else out[:500]}
        except Exception as e:
            return {"success": False, "result": f"Ping error: {e}"}


class DNSTool(BaseTool):
    def execute(self, params):
        host = params.get("host", "")
        if not host:
            return {"success": False, "result": "Host required"}
        try:
            import socket
            ip = socket.gethostbyname(host)
            try:
                hostname, _, _ = socket.gethostbyaddr(ip)
                return {"success": True, "result": f"{host} → {ip} ({hostname})"}
            except Exception:
                return {"success": True, "result": f"{host} → {ip}"}
        except Exception as e:
            return {"success": False, "result": f"DNS error: {e}"}


class HostInfoTool(BaseTool):
    def execute(self, params):
        target = params.get("target", "")
        if not target:
            return {"success": False, "result": "Target required"}
        results = []
        try:
            import socket
            ip = socket.gethostbyname(target)
            results.append(f"IP: {ip}")
        except Exception:
            pass
        try:
            import subprocess
            r = subprocess.run(["curl", "-s", f"https://ipapi.co/{target}/json/"], capture_output=True, text=True, timeout=15)
            if r.stdout:
                data = json.loads(r.stdout)
                org = data.get("org", "")
                city = data.get("city", "")
                country = data.get("country_name", "")
                if city: results.append(f"Location: {city}, {country}")
                if org: results.append(f"ISP: {org}")
        except Exception:
            pass
        return {"success": True, "result": " | ".join(results) if results else "No info"}


class TimestampTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "now")
        try:
            if action == "now":
                return {"success": True, "result": str(int(time.time()))}
            elif action == "from_iso":
                iso = params.get("iso", "")
                ts = int(datetime.datetime.fromisoformat(iso).timestamp())
                return {"success": True, "result": str(ts)}
            elif action == "to_iso":
                ts = float(params.get("timestamp", "0"))
                dt = datetime.datetime.fromtimestamp(ts)
                return {"success": True, "result": dt.isoformat()}
            return {"success": False, "result": "Actions: now, from_iso, to_iso"}
        except Exception as e:
            return {"success": False, "result": f"Timestamp error: {e}"}


class TimezoneTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "list")
        try:
            import zoneinfo
            if action == "list":
                zones = sorted(zoneinfo.available_timezones())
                return {"success": True, "result": "Available timezones: " + ", ".join(zones[:30]) + ("..." if len(zones) > 30 else "")}
            elif action == "convert":
                tz_name = params.get("timezone", "UTC")
                tz = zoneinfo.ZoneInfo(tz_name)
                now = datetime.datetime.now(tz)
                return {"success": True, "result": f"Time in {tz_name}: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"}
            return {"success": False, "result": "Actions: list, convert"}
        except Exception as e:
            return {"success": False, "result": f"Timezone error: {e}"}


class DateCalcTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "diff")
        try:
            if action == "diff":
                d1 = datetime.datetime.fromisoformat(params.get("date1", ""))
                d2 = datetime.datetime.fromisoformat(params.get("date2", ""))
                diff = abs((d2 - d1).days)
                return {"success": True, "result": f"Difference: {diff} days"}
            elif action == "add":
                d = datetime.datetime.fromisoformat(params.get("date", datetime.datetime.now().isoformat()))
                days = int(params.get("days", 0))
                result = d + datetime.timedelta(days=days)
                return {"success": True, "result": result.strftime("%Y-%m-%d")}
            elif action == "weekday":
                d = datetime.datetime.fromisoformat(params.get("date", ""))
                return {"success": True, "result": d.strftime("%A")}
            return {"success": False, "result": "Actions: diff, add, weekday"}
        except Exception as e:
            return {"success": False, "result": f"Date error: {e}"}


class TextTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "upper")
        text = params.get("text", "")
        if not text:
            return {"success": False, "result": "Text required"}
        try:
            if action == "upper":
                return {"success": True, "result": text.upper()}
            elif action == "lower":
                return {"success": True, "result": text.lower()}
            elif action == "title":
                return {"success": True, "result": text.title()}
            elif action == "capitalize":
                return {"success": True, "result": text.capitalize()}
            elif action == "swapcase":
                return {"success": True, "result": text.swapcase()}
            elif action == "reverse":
                return {"success": True, "result": text[::-1]}
            elif action == "trim":
                return {"success": True, "result": text.strip()}
            elif action == "length":
                return {"success": True, "result": f"{len(text)} chars, {len(text.split())} words, {text.count(chr(10))+1} lines"}
            elif action == "wrap":
                width = int(params.get("width", 80))
                return {"success": True, "result": textwrap.fill(text, width)}
            elif action == "strip_lines":
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                return {"success": True, "result": "\n".join(lines)}
            return {"success": False, "result": "Actions: upper, lower, title, capitalize, swapcase, reverse, trim, length, wrap, strip_lines"}
        except Exception as e:
            return {"success": False, "result": f"Text error: {e}"}


class DiffTool(BaseTool):
    def execute(self, params):
        text1 = params.get("text1", "")
        text2 = params.get("text2", "")
        if not text1 or not text2:
            return {"success": False, "result": "Need text1 and text2"}
        try:
            import difflib
            lines1 = text1.splitlines(keepends=True)
            lines2 = text2.splitlines(keepends=True)
            diff = list(difflib.unified_diff(lines1, lines2, n=2))
            result = "".join(diff[:100])
            return {"success": True, "result": result or "No differences"}
        except Exception as e:
            return {"success": False, "result": f"Diff error: {e}"}


class SortTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "alpha")
        text = params.get("text", "")
        if not text:
            return {"success": False, "result": "Text required"}
        try:
            lines = text.split("\n")
            if action in ("alpha", "asc"):
                lines.sort()
            elif action == "desc":
                lines.sort(reverse=True)
            elif action == "numeric":
                nums = [float(l.strip()) for l in lines if l.strip()]
                nums.sort()
                return {"success": True, "result": "\n".join(str(n) for n in nums)}
            elif action == "length":
                lines.sort(key=len)
            elif action in ("unique", "uniq"):
                seen = []
                [seen.append(l) for l in lines if l not in seen]
                lines = seen
            elif action == "shuffle":
                random.shuffle(lines)
            elif action == "reverse":
                lines.reverse()
            return {"success": True, "result": "\n".join(lines)}
        except Exception as e:
            return {"success": False, "result": f"Sort error: {e}"}


class RegexTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "find")
        pattern = params.get("pattern", "")
        text = params.get("text", "")
        if not pattern or not text:
            return {"success": False, "result": "Need pattern and text"}
        try:
            if action == "find":
                matches = re.findall(pattern, text)
                return {"success": True, "result": f"Found {len(matches)}: " + ", ".join(str(m) for m in matches[:50])}
            elif action == "match":
                m = re.match(pattern, text)
                return {"success": True, "result": f"Match: {m.group()}" if m else "No match"}
            elif action == "search":
                m = re.search(pattern, text)
                return {"success": True, "result": f"Found: {m.group()}" if m else "Not found"}
            elif action == "replace":
                replacement = params.get("replacement", "")
                result = re.sub(pattern, replacement, text)
                return {"success": True, "result": result[:2000]}
            elif action == "split":
                parts = re.split(pattern, text)
                return {"success": True, "result": "\n".join(parts[:50])}
            return {"success": False, "result": "Actions: find, match, search, replace, split"}
        except Exception as e:
            return {"success": False, "result": f"Regex error: {e}"}


class UUIDTool(BaseTool):
    def execute(self, params):
        import uuid
        count = min(int(params.get("count", 1)), 50)
        results = [str(uuid.uuid4()) for _ in range(count)]
        return {"success": True, "result": "\n".join(results)}


class Base64Tool(BaseTool):
    def execute(self, params):
        action = params.get("action", "encode")
        text = params.get("text", "")
        if not text:
            return {"success": False, "result": "Text required"}
        try:
            if action == "encode":
                return {"success": True, "result": base64.b64encode(text.encode()).decode()}
            elif action == "decode":
                return {"success": True, "result": base64.b64decode(text).decode()}
            return {"success": False, "result": "Actions: encode, decode"}
        except Exception as e:
            return {"success": False, "result": f"Base64 error: {e}"}


class ConfirmTool(BaseTool):
    def execute(self, params):
        message = params.get("message", "Are you sure?")
        default = params.get("default", "yes")
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            result = messagebox.askyesno("JARVIS", message)
            root.destroy()
            return {"success": True, "result": "yes" if result else "no"}
        except Exception:
            return {"success": True, "result": default}


class PromptTool(BaseTool):
    def execute(self, params):
        message = params.get("message", "Enter text:")
        default = params.get("default", "")
        try:
            import tkinter as tk
            from tkinter import simpledialog
            root = tk.Tk()
            root.withdraw()
            result = simpledialog.askstring("JARVIS", message, initialvalue=default)
            root.destroy()
            return {"success": True, "result": result or default}
        except Exception as e:
            return {"success": False, "result": f"Prompt error: {e}"}


class ChooseTool(BaseTool):
    def execute(self, params):
        message = params.get("message", "Choose:")
        options = params.get("options", [])
        if isinstance(options, str):
            options = [o.strip() for o in options.split(",")]
        if not options:
            return {"success": False, "result": "No options provided"}
        try:
            import tkinter as tk
            from tkinter import simpledialog
            root = tk.Tk()
            root.withdraw()
            result = simpledialog.askstring("JARVIS", f"{message}\nOptions: {', '.join(options)}", initialvalue=options[0])
            root.destroy()
            return {"success": True, "result": result or options[0]}
        except Exception:
            return {"success": True, "result": options[0]}


class BeepTool(BaseTool):
    def execute(self, params):
        freq = int(params.get("frequency", params.get("freq", 880)))
        duration = int(params.get("duration", 200))
        try:
            import winsound
            winsound.Beep(freq, duration)
            return {"success": True, "result": f"Beep at {freq}Hz for {duration}ms"}
        except ImportError:
            try:
                print(f"\a", end="", flush=True)
                return {"success": True, "result": "Beep sent"}
            except Exception:
                return {"success": False, "result": "Beep not available"}


class SleepTool(BaseTool):
    def execute(self, params):
        seconds = float(params.get("seconds", params.get("duration", 1)))
        if seconds > 300:
            return {"success": False, "result": "Max 300 seconds"}
        time.sleep(seconds)
        return {"success": True, "result": f"Slept for {seconds}s"}


class AlarmTool(BaseTool):
    def __init__(self):
        self._alarms = []

    def execute(self, params):
        action = params.get("action", "set")
        try:
            if action == "set":
                seconds = int(params.get("seconds", 10))
                def _alarm(sec):
                    time.sleep(sec)
                    try:
                        import winsound
                        for _ in range(5):
                            winsound.Beep(880, 200)
                            time.sleep(0.2)
                    except Exception:
                        print("\a" * 5, end="", flush=True)
                threading.Thread(target=_alarm, args=(seconds,), daemon=True).start()
                return {"success": True, "result": f"Alarm set for {seconds}s"}
            return {"success": False, "result": "Actions: set"}
        except Exception as e:
            return {"success": False, "result": f"Alarm error: {e}"}


class StopwatchTool(BaseTool):
    def __init__(self):
        self._start = 0
        self._running = False

    def execute(self, params):
        action = params.get("action", "start")
        try:
            if action == "start":
                self._start = time.time()
                self._running = True
                return {"success": True, "result": "Stopwatch started"}
            elif action == "stop":
                if not self._running:
                    return {"success": True, "result": "Not running"}
                elapsed = time.time() - self._start
                self._running = False
                return {"success": True, "result": f"Stopped: {elapsed:.2f}s"}
            elif action == "lap":
                if not self._running:
                    return {"success": True, "result": "Not running"}
                elapsed = time.time() - self._start
                return {"success": True, "result": f"Lap: {elapsed:.2f}s"}
            elif action == "reset":
                self._start = 0
                self._running = False
                return {"success": True, "result": "Stopwatch reset"}
            return {"success": False, "result": "Actions: start, stop, lap, reset"}
        except Exception as e:
            return {"success": False, "result": f"Stopwatch error: {e}"}


class FileInfoTool(BaseTool):
    def execute(self, params):
        path = params.get("path", "")
        if not path:
            return {"success": False, "result": "Path required"}
        try:
            st = os.stat(path)
            info = f"Size: {st.st_size:,} bytes"
            info += f"\nModified: {datetime.datetime.fromtimestamp(st.st_mtime)}"
            info += f"\nCreated: {datetime.datetime.fromtimestamp(st.st_ctime)}"
            info += f"\nPermissions: {oct(st.st_mode)[-3:]}"
            if os.path.isdir(path):
                count = len(os.listdir(path))
                info += f"\nDirectory with {count} items"
            else:
                ext = os.path.splitext(path)[1]
                info += f"\nType: {ext.upper() if ext else 'Unknown'}"
            return {"success": True, "result": info}
        except Exception as e:
            return {"success": False, "result": f"File info error: {e}"}


class DirListTool(BaseTool):
    def execute(self, params):
        path = params.get("path", ".")
        pattern = params.get("pattern", "*")
        max_items = int(params.get("max", 200))
        try:
            items = sorted(os.listdir(path))
            if pattern != "*":
                import fnmatch
                items = [i for i in items if fnmatch.fnmatch(i, pattern)]
            items = items[:max_items]
            dirs = [i + "/" for i in items if os.path.isdir(os.path.join(path, i))]
            files = [i for i in items if not os.path.isdir(os.path.join(path, i))]
            result = f"Directory: {os.path.abspath(path)}\n"
            if dirs:
                result += "Dirs: " + ", ".join(dirs) + "\n"
            if files:
                result += "Files: " + ", ".join(files)
            return {"success": True, "result": result or "(empty)"}
        except Exception as e:
            return {"success": False, "result": f"Dir list error: {e}"}


class ImageInfoTool(BaseTool):
    def execute(self, params):
        path = params.get("path", "")
        if not path:
            return {"success": False, "result": "Path required"}
        try:
            from PIL import Image
            img = Image.open(path)
            info = f"Format: {img.format}"
            info += f"\nSize: {img.size[0]}x{img.size[1]}px"
            info += f"\nMode: {img.mode}"
            info += f"\nFile: {os.path.getsize(path):,} bytes"
            if hasattr(img, 'info') and img.info:
                exif = {k: str(v)[:80] for k, v in img.info.items()}
                info += f"\nMetadata: {json.dumps(exif, ensure_ascii=False)}"
            return {"success": True, "result": info}
        except Exception as e:
            return {"success": False, "result": f"Image error: {e}"}


class FactTool(BaseTool):
    def execute(self, params):
        try:
            import urllib.request
            with urllib.request.urlopen("https://uselessfacts.jsph.pl/api/v2/facts/random", timeout=10) as r:
                data = json.loads(r.read())
            return {"success": True, "result": data.get("text", "No fact found")}
        except Exception:
            try:
                facts = [
                    "A day on Venus is longer than a year on Venus.",
                    "Honey never spoils. Archaeologists found 3000-year-old honey in Egyptian tombs.",
                    "Octopuses have three hearts and blue blood.",
                    "Bananas are berries, but strawberries aren't.",
                    "A group of flamingos is called a 'flamboyance'.",
                    "The Eiffel Tower can be 15 cm taller during summer.",
                    "Wombat poop is cube-shaped.",
                    "The human nose can remember 50,000 different scents.",
                    "There are more trees on Earth than stars in the Milky Way.",
                    "The speed of light is about 299,792,458 m/s.",
                ]
                return {"success": True, "result": random.choice(facts)}
            except Exception as e:
                return {"success": False, "result": f"Fact error: {e}"}


class LyricTool(BaseTool):
    def execute(self, params):
        artist = params.get("artist", "")
        title = params.get("title", "")
        if not artist and not title:
            return {"success": False, "result": "Need artist or title"}
        try:
            q = urllib.parse.quote(f"{artist} {title}")
            with urllib.request.urlopen(f"https://api.lyrics.ovh/v1/{urllib.parse.quote(artist)}/{urllib.parse.quote(title)}", timeout=10) as r:
                data = json.loads(r.read())
            lyrics = data.get("lyrics", "")
            return {"success": True, "result": lyrics[:2000]}
        except Exception:
            return {"success": False, "result": "Lyrics not found"}


class HNReaderTool(BaseTool):
    def execute(self, params):
        category = params.get("category", "top")
        count = min(int(params.get("count", 10)), 30)
        try:
            import urllib.request
            ids_url = f"https://hacker-news.firebaseio.com/v0/{category}stories.json"
            with urllib.request.urlopen(ids_url, timeout=10) as r:
                ids = json.loads(r.read())[:count]
            stories = []
            for sid in ids:
                with urllib.request.urlopen(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10) as r:
                    item = json.loads(r.read())
                stories.append(f"[{item.get('score', 0)}] {item.get('title', '')} ({item.get('url', 'no url')[:60]})")
            return {"success": True, "result": f"HN {category} stories:\n" + "\n".join(stories)}
        except Exception as e:
            return {"success": False, "result": f"HN error: {e}"}


class RedditTool(BaseTool):
    def execute(self, params):
        subreddit = params.get("subreddit", "programming")
        category = params.get("category", "hot")
        count = min(int(params.get("count", 10)), 30)
        try:
            import urllib.request
            url = f"https://www.reddit.com/r/{subreddit}/{category}.json?limit={count}&raw_json=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            posts = data.get("data", {}).get("children", [])
            lines = []
            for p in posts:
                d = p.get("data", {})
                lines.append(f"[{d.get('score', 0)}] {d.get('title', '')}")
            return {"success": True, "result": f"r/{subreddit} {category}:\n" + "\n".join(lines)}
        except Exception as e:
            return {"success": False, "result": f"Reddit error: {e}"}


class WikipediaTool(BaseTool):
    def execute(self, params):
        query = params.get("query", "")
        if not query:
            return {"success": False, "result": "Query required"}
        try:
            import urllib.request, urllib.parse
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(query)
            req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/2.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            extract = data.get("extract", "")
            title = data.get("title", query)
            if not extract or "may refer to" in extract.lower()[:50]:
                return {"success": False, "result": f"'{query}' is ambiguous. Try a more specific query."}
            return {"success": True, "result": f"**{title}**\n{extract[:2000]}"}
        except urllib.error.HTTPError:
            return {"success": False, "result": f"No Wikipedia page found for '{query}'"}
        except Exception as e:
            return {"success": False, "result": f"Wikipedia error: {e}"}


class WeatherForecastTool(BaseTool):
    def execute(self, params):
        city = params.get("city", "")
        days = min(int(params.get("days", 3)), 7)
        if not city:
            return {"success": False, "result": "City required"}
        try:
            import urllib.request, urllib.parse
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
            with urllib.request.urlopen(geo_url, timeout=10) as r:
                geo = json.loads(r.read())
            if not geo.get("results"):
                return {"success": False, "result": f"City '{city}' not found"}
            loc = geo["results"][0]
            lat, lon = loc["latitude"], loc["longitude"]
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto&forecast_days={days}"
            with urllib.request.urlopen(w_url, timeout=10) as r:
                w = json.loads(r.read())
            daily = w.get("daily", {})
            dates = daily.get("time", [])
            tmax = daily.get("temperature_2m_max", [])
            tmin = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            codes = daily.get("weathercode", [])
            weather_names = {0:"Clear",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Foggy",51:"Drizzle",61:"Rain",71:"Snow",80:"Showers",95:"Thunderstorm"}
            result = f"Forecast for {city}:\n"
            for i in range(len(dates)):
                wc = weather_names.get(codes[i] if i < len(codes) else 0, "Unknown")
                result += f"  {dates[i]}: {tmin[i]}-{tmax[i]}C, {wc}, {precip[i]}mm rain\n"
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "result": f"Forecast error: {e}"}


class CurrencyTool(BaseTool):
    def execute(self, params):
        amount = float(params.get("amount", 1))
        from_cur = params.get("from", params.get("from_currency", "USD")).upper()
        to_cur = params.get("to", params.get("to_currency", "EUR")).upper()
        try:
            import urllib.request
            req = urllib.request.Request(f"https://api.exchangerate-api.com/v4/latest/{from_cur}",
                                          headers={"User-Agent": "Jarvis/2.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            rates = data.get("rates", {})
            if to_cur not in rates:
                return {"success": False, "result": f"No rate for {to_cur}"}
            rate = rates[to_cur]
            converted = amount * rate
            return {"success": True, "result": f"{amount} {from_cur} = {converted:.2f} {to_cur} (rate: {rate:.4f})"}
        except Exception as e:
            return {"success": False, "result": f"Currency error: {e}"}


class StockTool(BaseTool):
    def execute(self, params):
        symbol = params.get("symbol", "").upper()
        if not symbol:
            return {"success": False, "result": "Symbol required (e.g. AAPL)"}
        try:
            import urllib.request
            req = urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                                          headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            price = meta.get("regularMarketPrice", meta.get("previousClose", "N/A"))
            name = meta.get("exchangeName", "")
            currency = meta.get("currency", "USD")
            return {"success": True, "result": f"{symbol} ({name}): ${price} {currency}"}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return {"success": False, "result": "Stock API rate limited. Try again later."}
            return {"success": False, "result": f"Stock API error: {e.code}"}
        except Exception as e:
            return {"success": False, "result": f"Stock error: {e}"}


class MovieTool(BaseTool):
    def execute(self, params):
        title = params.get("title", "")
        if not title:
            return {"success": False, "result": "Title required"}
        try:
            q = urllib.parse.quote(title)
            req = urllib.request.Request(f"https://www.omdbapi.com/?t={q}&apikey=2c9d2e0e",
                                          headers={"User-Agent": "Jarvis/2.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            if data.get("Response") == "True":
                return {"success": True, "result": f"**{data.get('Title')}** ({data.get('Year')})\nRating: {data.get('imdbRating')}/10\nGenre: {data.get('Genre')}\nDirector: {data.get('Director')}\nPlot: {data.get('Plot', '')[:500]}"}
            return {"success": False, "result": data.get("Error", "Movie not found")}
        except Exception as e:
            return {"success": False, "result": f"Movie error: API unavailable. Try: {title}"}


class RecipeTool(BaseTool):
    def execute(self, params):
        query = params.get("query", "")
        if not query:
            return {"success": False, "result": "Query required"}
        try:
            q = urllib.parse.quote(query)
            with urllib.request.urlopen(f"https://www.themealdb.com/api/json/v1/1/search.php?s={q}", timeout=10) as r:
                data = json.loads(r.read())
            meals = data.get("meals", [])
            if not meals:
                return {"success": False, "result": "No recipes found"}
            meal = meals[0]
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                meas = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    ingredients.append(f"{meas} {ing}".strip())
            result = f"**{meal['strMeal']}** ({meal.get('strArea', '')} - {meal.get('strCategory', '')})\n"
            result += f"Ingredients: {', '.join(ingredients[:15])}\n"
            result += f"Instructions: {meal.get('strInstructions', '')[:500]}"
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "result": f"Recipe error: {e}"}


class RDJokeTool(BaseTool):
    def execute(self, params):
        try:
            import urllib.request
            with urllib.request.urlopen("https://official-joke-api.appspot.com/random_joke", timeout=10) as r:
                data = json.loads(r.read())
            return {"success": True, "result": f"{data.get('setup', '')} - {data.get('punchline', '')}"}
        except Exception:
            try:
                import urllib.request
                with urllib.request.urlopen("https://v2.jokeapi.dev/joke/Any?type=twopart", timeout=10) as r:
                    data = json.loads(r.read())
                return {"success": True, "result": f"{data.get('setup', '')} - {data.get('delivery', '')}"}
            except Exception as e:
                return {"success": False, "result": f"Joke error: {e}"}


class ShowTool(BaseTool):
    """Display text in a scrollable popup window"""
    def execute(self, params):
        text = params.get("text", params.get("content", ""))
        title = params.get("title", "JARVIS Viewer")
        if not text:
            return {"success": False, "result": "Text required"}
        try:
            import tkinter as tk
            from tkinter import scrolledtext
            top = tk.Toplevel()
            top.title(title)
            top.geometry("600x400")
            top.configure(bg="#060618")
            txt = scrolledtext.ScrolledText(top, wrap=tk.WORD, bg="#0a0a2e", fg="#c8e6ff",
                                            insertbackground="#00ddff", font=("Consolas", 10))
            txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            txt.insert("1.0", text)
            txt.config(state=tk.DISABLED)
            return {"success": True, "result": f"Opened window: {title}"}
        except Exception as e:
            return {"success": True, "result": text[:2000]}


class AlertTool(BaseTool):
    """Show notification alert with custom title/message/icon"""
    def execute(self, params):
        title = params.get("title", "JARVIS")
        message = params.get("message", params.get("text", ""))
        icon = params.get("icon", "info")
        try:
            icons = {"info": 0x40, "warn": 0x30, "error": 0x10, "question": 0x20}
            flags = icons.get(icon, 0x40) | 0x1000
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, flags)
            return {"success": True, "result": f"Alert shown: {title}"}
        except Exception:
            try:
                from win10toast import ToastNotifier
                ToastNotifier().show_toast(title, message, duration=5, threaded=True)
                return {"success": True, "result": f"Notification: {title}"}
            except Exception:
                return {"success": True, "result": f"[{icon.upper()}] {title}: {message[:200]}"}


class CsvTool(BaseTool):
    """Format CSV data as aligned table"""
    def execute(self, params):
        data = params.get("data", "")
        if not data:
            return {"success": False, "result": "CSV data required"}
        try:
            import csv, io
            reader = csv.reader(io.StringIO(data))
            rows = [row for row in reader if any(c.strip() for c in row)]
            if not rows:
                return {"success": False, "result": "Empty CSV"}
            col_widths = [max(len(cell) for cell in col) for col in zip(*rows)]
            lines = []
            for i, row in enumerate(rows):
                padded = [cell.ljust(col_widths[j]) for j, cell in enumerate(row)]
                lines.append(" | ".join(padded))
                if i == 0:
                    lines.append("-|-".join("-" * w for w in col_widths))
            return {"success": True, "result": "\n".join(lines)}
        except Exception as e:
            return {"success": False, "result": f"CSV error: {e}"}


class JsonFormatTool(BaseTool):
    """Format, validate, or query JSON data"""
    def execute(self, params):
        action = params.get("action", "format")
        data = params.get("data", "")
        if not data:
            return {"success": False, "result": "JSON data required"}
        try:
            parsed = json.loads(data)
            if action == "format":
                return {"success": True, "result": json.dumps(parsed, indent=2, ensure_ascii=False)[:5000]}
            elif action == "validate":
                return {"success": True, "result": "Valid JSON"}
            elif action == "minify":
                return {"success": True, "result": json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)}
            elif action == "query":
                import jsonpath_ng
                path = params.get("path", "$")
                expr = jsonpath_ng.parse(path)
                matches = [m.value for m in expr.find(parsed)]
                return {"success": True, "result": json.dumps(matches, indent=2, ensure_ascii=False)[:3000]}
            return {"success": False, "result": "Actions: format, validate, minify, query"}
        except json.JSONDecodeError as e:
            return {"success": False, "result": f"Invalid JSON: {e}"}
        except Exception as e:
            return {"success": False, "result": f"JSON error: {e}"}


class BrightnessTool(BaseTool):
    """Get/set screen brightness"""
    def execute(self, params):
        action = params.get("action", "get")
        import subprocess
        try:
            if action == "get":
                r = subprocess.run(["powershell", "-c", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"],
                                   capture_output=True, text=True, timeout=5)
                val = r.stdout.strip()
                return {"success": True, "result": f"Brightness: {val}%" if val else "N/A"}
            elif action == "set":
                pct = max(0, min(100, int(params.get("percent", params.get("value", 50)))))
                subprocess.run(["powershell", "-c", f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{pct})"],
                               capture_output=True, text=True, timeout=5)
                return {"success": True, "result": f"Brightness set to {pct}%"}
            return {"success": False, "result": "Actions: get, set"}
        except Exception as e:
            return {"success": False, "result": f"Brightness error: {e}"}


class EncodeTool(BaseTool):
    """Encode/decode various formats"""
    def execute(self, params):
        action = params.get("action", "rot13")
        text = params.get("text", "")
        if not text:
            return {"success": False, "result": "Text required"}
        try:
            if action == "rot13":
                return {"success": True, "result": text.translate(str.maketrans(
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                    "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))}
            elif action == "binary":
                return {"success": True, "result": " ".join(format(ord(c), "08b") for c in text)}
            elif action == "hex":
                return {"success": True, "result": text.encode().hex()}
            elif action == "octal":
                return {"success": True, "result": " ".join(format(ord(c), "03o") for c in text)}
            elif action == "morse":
                morse = {"A":".-","B":"-...","C":"-.-.","D":"-..","E":".","F":"..-.","G":"--.","H":"....","I":"..","J":".---",
                         "K":"-.-","L":".-..","M":"--","N":"-.","O":"---","P":".--.","Q":"--.-","R":".-.","S":"...","T":"-",
                         "U":"..-","V":"...-","W":".--","X":"-..-","Y":"-.--","Z":"--..","0":"-----","1":".----","2":"..---",
                         "3":"...--","4":"....-","5":".....","6":"-....","7":"--...","8":"---..","9":"----."}
                encoded = " ".join(morse.get(c.upper(), c) for c in text)
                return {"success": True, "result": encoded[:2000]}
            return {"success": False, "result": "Actions: rot13, binary, hex, octal, morse"}
        except Exception as e:
            return {"success": False, "result": f"Encode error: {e}"}


class ChartTool(BaseTool):
    """Generate ASCII bar chart from numbers"""
    def execute(self, params):
        data = params.get("data", "")
        if isinstance(data, str):
            try:
                entries = json.loads(data)
            except Exception:
                pairs = [p.split(":") for p in data.split(",") if ":" in p]
                entries = {k.strip(): float(v.strip()) for k, v in pairs}
        else:
            entries = data if isinstance(data, dict) else {}
        if not entries:
            return {"success": False, "result": "Data required (e.g. {'A':10,'B':20})"}
        max_val = max(entries.values()) or 1
        bar_width = 30
        lines = []
        for label, val in sorted(entries.items(), key=lambda x: -x[1]):
            bar_len = max(1, int((val / max_val) * bar_width))
            bar = "█" * bar_len
            lines.append(f"{str(label)[:10]:>10} | {bar} {val}")
        return {"success": True, "result": "\n".join(lines)}


class MarkdownRenderTool(BaseTool):
    """Strip markdown formatting to clean text"""
    def execute(self, params):
        text = params.get("text", "")
        if not text:
            return {"success": False, "result": "Text required"}
        try:
            text = re.sub(r'#{1,6}\s+', '', text)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            text = re.sub(r'`([^`]+)`', r'\1', text)
            text = re.sub(r'```.*?\n', '\n', text, flags=re.DOTALL)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            text = re.sub(r'>\s+', '', text)
            text = re.sub(r'[-*+]\s+', '', text)
            text = re.sub(r'\d+\.\s+', '', text)
            text = re.sub(r'\|', '', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            return {"success": True, "result": text.strip()[:3000]}
        except Exception as e:
            return {"success": False, "result": f"Render error: {e}"}


class ScreenResTool(BaseTool):
    """Get screen resolution and info"""
    def execute(self, params):
        try:
            import tkinter as tk
            root = tk.Tk()
            w = root.winfo_screenwidth()
            h = root.winfo_screenheight()
            root.destroy()
            return {"success": True, "result": f"Screen: {w}x{h}"}
        except Exception:
            try:
                import ctypes
                user32 = ctypes.windll.user32
                return {"success": True, "result": f"Screen: {user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"}
            except Exception:
                return {"success": False, "result": "Screen info unavailable"}


class CounterTool(BaseTool):
    """Simple increment/decrement/reset counter"""
    def __init__(self):
        self._counters = {}

    def execute(self, params):
        name = params.get("name", "default")
        action = params.get("action", "get")
        if name not in self._counters:
            self._counters[name] = 0
        try:
            if action == "get":
                return {"success": True, "result": f"Counter '{name}': {self._counters[name]}"}
            elif action == "inc":
                self._counters[name] += 1
                return {"success": True, "result": f"Counter '{name}': {self._counters[name]}"}
            elif action == "dec":
                self._counters[name] -= 1
                return {"success": True, "result": f"Counter '{name}': {self._counters[name]}"}
            elif action == "add":
                self._counters[name] += int(params.get("value", params.get("amount", 1)))
                return {"success": True, "result": f"Counter '{name}': {self._counters[name]}"}
            elif action == "reset":
                self._counters[name] = 0
                return {"success": True, "result": f"Counter '{name}' reset"}
            elif action == "list":
                if not self._counters:
                    return {"success": True, "result": "No counters"}
                return {"success": True, "result": "\n".join(f"{k}: {v}" for k, v in sorted(self._counters.items()))}
            return {"success": False, "result": "Actions: get, inc, dec, add, reset, list"}
        except Exception as e:
            return {"success": False, "result": f"Counter error: {e}"}


class ProgressTool(BaseTool):
    """Show a simple text progress bar"""
    def execute(self, params):
        current = int(params.get("current", params.get("value", 0)))
        total = int(params.get("total", params.get("max", 100)))
        width = int(params.get("width", params.get("size", 30)))
        label = params.get("label", "")
        if total <= 0:
            total = 100
        pct = min(100, max(0, (current / total) * 100))
        filled = int((current / total) * width)
        bar = "█" * filled + "░" * (width - filled)
        result = f"{label + ': ' if label else ''}[{bar}] {pct:.0f}% ({current}/{total})"
        return {"success": True, "result": result}


class ColorPickerTool(BaseTool):
    """Show a color picker dialog or convert between color formats"""
    def execute(self, params):
        action = params.get("action", "pick")
        try:
            if action == "pick":
                import tkinter as tk
                from tkinter import colorchooser
                root = tk.Tk()
                root.withdraw()
                color = colorchooser.askcolor(title="Pick a color", initialcolor="#00ddff")
                root.destroy()
                if color and color[0]:
                    r, g, b = [int(c) for c in color[0]]
                    return {"success": True, "result": f"RGB({r},{g},{b})  Hex: #{r:02x}{g:02x}{b:02x}"}
                return {"success": True, "result": "No color selected"}
            elif action == "rgb_to_hex":
                r, g, b = int(params.get("r", 0)), int(params.get("g", 0)), int(params.get("b", 0))
                return {"success": True, "result": f"#{r:02x}{g:02x}{b:02x}"}
            elif action == "hex_to_rgb":
                h = params.get("hex", "#000").lstrip("#")
                if len(h) == 3:
                    h = "".join(c*2 for c in h)
                r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                return {"success": True, "result": f"rgb({r},{g},{b})"}
            return {"success": False, "result": "Actions: pick, rgb_to_hex, hex_to_rgb"}
        except Exception as e:
            return {"success": False, "result": f"Color pick error: {e}"}


class BibliographyTool(BaseTool):
    def execute(self, params):
        style = params.get("style", "mla").lower()
        sources_str = params.get("sources", params.get("items", ""))
        if not sources_str:
            return {"success": False, "result": "Provide sources separated by | (author|title|publisher|year)"}
        entries = [s.strip() for s in sources_str.split("|") if s.strip()]
        lines = [f"Bibliography ({style.upper()}):"]
        for i in range(0, len(entries), 4):
            author = entries[i] if i < len(entries) else ""
            title = entries[i + 1] if i + 1 < len(entries) else ""
            publisher = entries[i + 2] if i + 2 < len(entries) else ""
            year = entries[i + 3] if i + 3 < len(entries) else ""
            if not title:
                continue
            if style == "mla":
                lines.append(f"  {author}. *{title}*. {publisher}, {year}." if author else f"  *{title}*. {publisher}, {year}.")
            elif style == "apa":
                lines.append(f"  {author} ({year}). *{title}*. {publisher}." if author else f"  ({year}). *{title}*. {publisher}.")
            elif style == "chicago":
                lines.append(f"  {author}. *{title}*. {publisher}, {year}." if author else f"  *{title}*. {publisher}, {year}.")
            else:
                lines.append(f"  {author} ({year}), {title}, {publisher}")
        return {"success": True, "result": "\n".join(lines)}


class EquationSolveTool(BaseTool):
    def execute(self, params):
        equation = params.get("equation", "").strip()
        if not equation:
            return {"success": False, "result": "Provide equation (e.g., 2x+3=7 or x^2-4=0)"}
        try:
            eq = re.sub(r'\^', '**', equation)
            eq = eq.replace("=", "-(") + ")" if "=" in eq else eq + "=0"
            eq = eq.replace("=0", "") if not eq.endswith(")") else eq
            # Linear: ax + b = 0
            if "x" in eq and "**" not in eq:
                # Parse as linear: solve for x
                expr = eq.replace("=0", "-0") if "=0" not in eq else eq
                expr = expr.replace("=0", "") if expr.endswith("=0") else expr.replace("=", "-(") + ")" if "=" in expr else expr
                # Try simple linear: ax + b = 0 -> x = -b/a
                simplified = expr.replace(" ", "").replace("x", "").replace("(", "").replace(")", "")
                return {"success": True, "result": f"To solve '{equation}':\n  Isolate x on one side\n  Use inverse operations\n  Solution format: x = value"}
            # Quadratic: ax^2 + bx + c = 0
            if "**2" in eq or "x^2" in equation:
                return {"success": True, "result": f"Quadratic equation: {equation}\n  Use the quadratic formula:\n  x = (-b ± √(b² - 4ac)) / 2a\n  First identify a, b, c from your equation"}
            return {"success": True, "result": f"Equation: {equation}\n  Solve step by step:\n  1. Simplify both sides\n  2. Use inverse operations\n  3. Check your answer"}
        except Exception as e:
            return {"success": False, "result": f"Equation error: {e}"}


# ════════════════════════════════════════════
# Student & Teacher Tools (33 tools)
# ════════════════════════════════════════════

_STUDY_DIR = os.path.join(os.path.expanduser("~"), ".jarvis_study")
os.makedirs(_STUDY_DIR, exist_ok=True)


class FlashcardTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "add")
        path = os.path.join(_STUDY_DIR, "flashcards.json")
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    cards = json.load(f)
            else:
                cards = []
            if action == "add":
                q, a = params.get("question", ""), params.get("answer", "")
                if not q or not a:
                    return {"success": False, "result": "Add: provide question + answer"}
                deck = params.get("deck", "default")
                cards.append({"question": q, "answer": a, "deck": deck, "box": 0})
                with open(path, "w") as f:
                    json.dump(cards, f)
                return {"success": True, "result": f"Added: {q[:50]}"}
            elif action == "quiz":
                deck = params.get("deck", "default")
                pool = [c for c in cards if c.get("deck", "default") == deck]
                if not pool:
                    return {"success": True, "result": "No cards in that deck"}
                random.shuffle(pool)
                n = min(int(params.get("count", 5)), len(pool))
                lines = [f"Flashcard Quiz ({n} questions):"]
                for c in pool[:n]:
                    lines.append(f"\nQ: {c['question']}\nA: ||{c['answer']}||")
                return {"success": True, "result": "\n".join(lines)}
            elif action == "list":
                deck = params.get("deck", "")
                pool = [c for c in cards if c.get("deck", "default") == deck] if deck else cards
                if not pool:
                    return {"success": True, "result": "No cards found"}
                lines = [f"Flashcards ({len(pool)} cards):"]
                for i, c in enumerate(pool, 1):
                    lines.append(f"{i}. [{c.get('deck','default')}] {c['question'][:60]}")
                return {"success": True, "result": "\n".join(lines)}
            elif action == "delete":
                deck = params.get("deck", "default")
                cards = [c for c in cards if c.get("deck", "default") != deck]
                with open(path, "w") as f:
                    json.dump(cards, f)
                return {"success": True, "result": f"Deleted deck: {deck}"}
            elif action == "stats":
                deck = params.get("deck", "default")
                pool = [c for c in cards if c.get("deck", "default") == deck]
                return {"success": True, "result": f"Deck '{deck}': {len(pool)} cards"}
            return {"success": False, "result": "Actions: add, quiz, list, delete, stats"}
        except Exception as e:
            return {"success": False, "result": f"Flashcard error: {e}"}


class QuizTool(BaseTool):
    def execute(self, params):
        topic = params.get("topic", params.get("subject", ""))
        count = min(int(params.get("count", 5)), 20)
        if not topic:
            return {"success": False, "result": "Provide a topic/subject"}
        questions = {
            "math": [
                ("What is the derivative of x²?", "2x"),
                ("What is π to 4 decimal places?", "3.1416"),
                ("What is the Pythagorean theorem?", "a² + b² = c²"),
                ("What is the quadratic formula?", "x = (-b ± √(b²-4ac))/2a"),
                ("What is sin²θ + cos²θ equal to?", "1"),
                ("What is log₁₀(100)?", "2"),
                ("What is the area of a circle?", "πr²"),
                ("What is 7! (7 factorial)?", "5040"),
            ],
            "science": [
                ("What is the chemical symbol for gold?", "Au"),
                ("What planet is closest to the sun?", "Mercury"),
                ("What gas do plants absorb?", "CO₂ (carbon dioxide)"),
                ("What is the speed of light?", "~3×10⁸ m/s"),
                ("What organ pumps blood?", "Heart"),
                ("What is H₂O?", "Water"),
                ("What element has atomic number 6?", "Carbon"),
                ("What force keeps planets in orbit?", "Gravity"),
            ],
            "history": [
                ("What year did WW2 end?", "1945"),
                ("Who discovered America in 1492?", "Christopher Columbus"),
                ("What empire was ruled by Julius Caesar?", "Roman Empire"),
                ("What wall separated Berlin?", "Berlin Wall"),
                ("Who wrote the Declaration of Independence?", "Thomas Jefferson"),
                ("What ancient wonder was in Giza?", "The Great Pyramid"),
            ],
            "english": [
                ("What is a synonym for 'happy'?", "Joyful"),
                ("What tense describes ongoing action?", "Present continuous"),
                ("What is a metaphor?", "Comparison without 'like/as'"),
                ("What is a protagonist?", "Main character"),
                ("What is alliteration?", "Same starting sound repetition"),
            ],
        }
        topic_lower = topic.lower()
        for key in questions:
            if key in topic_lower or topic_lower in key:
                pool = questions[key]
                random.shuffle(pool)
                n = min(count, len(pool))
                lines = [f"Quiz: {key.title()} ({n} questions)"]
                for i, (q, a) in enumerate(pool[:n], 1):
                    lines.append(f"{i}. {q}\n   → {a}")
                return {"success": True, "result": "\n\n".join(lines)}
        # Generate generic quiz
        lines = [f"Quiz: {topic} ({count} questions)\n"]
        for i in range(count):
            lines.append(f"{i+1}. What is a key concept in {topic}?")
        return {"success": True, "result": "\n".join(lines) + "\n\n(Add specific quiz topics: math, science, history, english)"}


class StudySetTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "create")
        path = os.path.join(_STUDY_DIR, "studysets.json")
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    sets = json.load(f)
            else:
                sets = {}
            if action == "create":
                name = params.get("name", "").strip()
                items_str = params.get("items", "")
                if not name or not items_str:
                    return {"success": False, "result": "Provide name + items (comma-separated)"}
                items = [i.strip() for i in items_str.split(",") if i.strip()]
                sets[name] = {"items": items, "created": time.time()}
                with open(path, "w") as f:
                    json.dump(sets, f)
                return {"success": True, "result": f"Study set '{name}' with {len(items)} items"}
            elif action == "list":
                if not sets:
                    return {"success": True, "result": "No study sets"}
                lines = [f"Study Sets ({len(sets)}):"]
                for name, data in sets.items():
                    lines.append(f"  • {name} ({len(data['items'])} items)")
                return {"success": True, "result": "\n".join(lines)}
            elif action == "view":
                name = params.get("name", "")
                if name not in sets:
                    return {"success": False, "result": f"Set '{name}' not found"}
                items = sets[name]["items"]
                lines = [f"Study Set: {name}\n"]
                for i, item in enumerate(items, 1):
                    lines.append(f"{i}. {item}")
                return {"success": True, "result": "\n".join(lines)}
            elif action == "delete":
                name = params.get("name", "")
                if name in sets:
                    del sets[name]
                    with open(path, "w") as f:
                        json.dump(sets, f)
                    return {"success": True, "result": f"Deleted: {name}"}
                return {"success": False, "result": f"Set '{name}' not found"}
            return {"success": False, "result": "Actions: create, list, view, delete"}
        except Exception as e:
            return {"success": False, "result": f"StudySet error: {e}"}


class GradeCalcTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "needed")
        if action == "needed":
            try:
                current = float(params.get("current", params.get("grade", 0)))
                desired = float(params.get("desired", params.get("target", 0)))
                weight = float(params.get("weight", params.get("exam_weight", 0)))
                if not (0 <= weight <= 100):
                    return {"success": False, "result": "Weight must be 0-100"}
                w = weight / 100.0
                needed = (desired - current * (1 - w)) / w
                if needed > 100:
                    return {"success": True, "result": f"Need {needed:.1f}% — impossible even with 100%"}
                elif needed < 0:
                    return {"success": True, "result": "You already have the grade locked in!"}
                return {"success": True, "result": f"Need {needed:.1f}% on the final to get {desired}%"}
            except (ValueError, ZeroDivisionError):
                return {"success": False, "result": "Provide: current, desired, weight"}
        elif action == "final":
            try:
                grades_str = params.get("grades", "")
                weights_str = params.get("weights", "")
                if not grades_str or not weights_str:
                    return {"success": False, "result": "Provide comma-separated grades and weights"}
                grades = [float(g.strip()) for g in grades_str.split(",")]
                weights = [float(w.strip()) for w in weights_str.split(",")]
                if len(grades) != len(weights):
                    return {"success": False, "result": "Same number of grades and weights required"}
                total = sum(g * w / 100 for g, w in zip(grades, weights))
                return {"success": True, "result": f"Grade: {total:.1f}%"}
            except Exception:
                return {"success": False, "result": "Grades and weights must be numbers"}
        return {"success": False, "result": "Actions: needed (what-if), final (weighted total)"}


class GPATool(BaseTool):
    def execute(self, params):
        action = params.get("action", "calculate")
        scale = float(params.get("scale", 4.0))
        if action == "calculate":
            grades_str = params.get("grades", "")
            hours_str = params.get("hours", params.get("credits", ""))
            if not grades_str:
                return {"success": False, "result": "Provide grades (letter or 0-4 values, comma-separated)"}
            grade_map = {"A+": 4.0, "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
                         "C+": 2.3, "C": 2.0, "C-": 1.7, "D+": 1.3, "D": 1.0, "F": 0.0}
            parts = [g.strip() for g in grades_str.split(",")]
            grades = []
            for g in parts:
                if g.upper() in grade_map:
                    grades.append(grade_map[g.upper()])
                else:
                    try:
                        grades.append(float(g))
                    except ValueError:
                        return {"success": False, "result": f"Invalid grade: {g}"}
            if hours_str:
                hours = [float(h.strip()) for h in hours_str.split(",")]
                if len(grades) != len(hours):
                    return {"success": False, "result": "Same number of grades and credit hours required"}
                total = sum(g * h for g, h in zip(grades, hours)) / sum(hours) * scale / 4.0
                return {"success": True, "result": f"GPA: {total:.2f} / {scale:.1f}"}
            else:
                total = sum(grades) / len(grades) * scale / 4.0
                return {"success": True, "result": f"GPA: {total:.2f} / {scale:.1f}"}
        elif action == "target":
            try:
                current_gpa = float(params.get("current_gpa", 0))
                target_gpa = float(params.get("target_gpa", 0))
                credits_so_far = float(params.get("credits_so_far", 0))
                new_credits = float(params.get("new_credits", 0))
                needed = (target_gpa * (credits_so_far + new_credits) - current_gpa * credits_so_far) / new_credits
                return {"success": True, "result": f"Need avg GPA of {needed:.2f} in {new_credits:.0f} new credits to reach {target_gpa:.2f}"}
            except (ValueError, ZeroDivisionError):
                return {"success": False, "result": "Provide: current_gpa, target_gpa, credits_so_far, new_credits"}
        return {"success": False, "result": "Actions: calculate, target"}


class AssignmentTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "add")
        path = os.path.join(_STUDY_DIR, "assignments.json")
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    assignments = json.load(f)
            else:
                assignments = []
            if action == "add":
                name = params.get("name", params.get("title", ""))
                due = params.get("due", params.get("due_date", ""))
                course = params.get("course", params.get("class", "General"))
                if not name or not due:
                    return {"success": False, "result": "Provide name + due date"}
                assignments.append({"name": name, "due": due, "course": course,
                                    "status": "pending", "created": time.time()})
                with open(path, "w") as f:
                    json.dump(assignments, f)
                return {"success": True, "result": f"Added: {name} (due {due})"}
            elif action == "list":
                if not assignments:
                    return {"success": True, "result": "No assignments"}
                course = params.get("course", "")
                pool = [a for a in assignments if not course or a.get("course") == course]
                pending = [a for a in pool if a.get("status") != "done"]
                done = [a for a in pool if a.get("status") == "done"]
                lines = [f"Assignments ({len(pool)} total, {len(pending)} pending):"]
                if pending:
                    lines.append("\nPending:")
                    for a in sorted(pending, key=lambda x: x.get("due", "")):
                        lines.append(f"  • {a['name']} — due {a['due']} [{a.get('course','General')}]")
                if done:
                    lines.append(f"\nCompleted ({len(done)}):")
                    for a in done:
                        lines.append(f"  ✓ {a['name']}")
                return {"success": True, "result": "\n".join(lines)}
            elif action == "done":
                name = params.get("name", params.get("title", ""))
                for a in assignments:
                    if a["name"].lower() == name.lower():
                        a["status"] = "done"
                        with open(path, "w") as f:
                            json.dump(assignments, f)
                        return {"success": True, "result": f"Completed: {a['name']}"}
                return {"success": False, "result": f"Assignment not found: {name}"}
            elif action == "delete":
                name = params.get("name", params.get("title", ""))
                assignments = [a for a in assignments if a["name"].lower() != name.lower()]
                with open(path, "w") as f:
                    json.dump(assignments, f)
                return {"success": True, "result": f"Deleted: {name}"}
            return {"success": False, "result": "Actions: add, list, done, delete"}
        except Exception as e:
            return {"success": False, "result": f"Assignment error: {e}"}


class StudyTimerTool(BaseTool):
    def __init__(self):
        self._timer_thread = None
        self._running = False
        self._remaining = 0

    def execute(self, params):
        action = params.get("action", "start")
        if action == "start":
            minutes = int(params.get("minutes", params.get("duration", 25)))
            self._remaining = minutes * 60
            self._running = True
            if not self._timer_thread or not self._timer_thread.is_alive():
                self._timer_thread = threading.Thread(target=self._run, daemon=True)
                self._timer_thread.start()
            return {"success": True, "result": f"Study timer: {minutes} min (Pomodoro). Focus!"}
        elif action == "stop":
            self._running = False
            return {"success": True, "result": "Timer stopped"}
        elif action == "status":
            if self._running:
                mins, secs = divmod(self._remaining, 60)
                return {"success": True, "result": f"Time remaining: {mins}:{secs:02d}"}
            return {"success": True, "result": "Timer not running"}

    def _run(self):
        while self._running and self._remaining > 0:
            time.sleep(1)
            self._remaining -= 1
        if self._running:
            self._running = False
            try:
                if os.name == 'nt':
                    import winsound
                    winsound.Beep(880, 500)
                    winsound.Beep(660, 500)
                else:
                    print("\a")
            except Exception:
                pass


class AttendanceTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "record")
        path = os.path.join(_STUDY_DIR, "attendance.json")
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = json.load(f)
            else:
                data = {"students": {}, "records": []}
            if action == "add_student":
                name = params.get("name", "").strip()
                if not name:
                    return {"success": False, "result": "Provide student name"}
                sid = params.get("id", name.lower().replace(" ", "_"))
                if sid in data["students"]:
                    return {"success": False, "result": f"Student '{name}' already exists"}
                data["students"][sid] = {"name": name, "added": time.time()}
                with open(path, "w") as f:
                    json.dump(data, f)
                return {"success": True, "result": f"Added student: {name}"}
            elif action == "record":
                sid = params.get("id", params.get("student", ""))
                date = params.get("date", datetime.date.today().isoformat())
                present = params.get("present", True)
                if isinstance(present, str):
                    present = present.lower() in ("true", "yes", "1", "present")
                if sid not in data["students"]:
                    return {"success": False, "result": f"Student not found. Use add_student first."}
                data["records"].append({"student_id": sid, "date": date, "present": present})
                with open(path, "w") as f:
                    json.dump(data, f)
                return {"success": True, "result": f"Recorded {'present' if present else 'absent'} for {data['students'][sid]['name']} on {date}"}
            elif action == "report":
                sid = params.get("id", params.get("student", ""))
                if sid:
                    if sid not in data["students"]:
                        return {"success": False, "result": f"Student not found: {sid}"}
                    records = [r for r in data["records"] if r["student_id"] == sid]
                    total = len(records)
                    present = sum(1 for r in records if r["present"])
                    pct = (present / total * 100) if total else 0
                    return {"success": True, "result": f"{data['students'][sid]['name']}: {present}/{total} ({pct:.0f}%)"}
                lines = ["Attendance Report:"]
                for sid, s in data["students"].items():
                    records = [r for r in data["records"] if r["student_id"] == sid]
                    total = len(records)
                    present = sum(1 for r in records if r["present"])
                    pct = (present / total * 100) if total else 0
                    lines.append(f"  {s['name']}: {present}/{total} ({pct:.0f}%)")
                return {"success": True, "result": "\n".join(lines)}
            elif action == "students":
                lines = [f"Students ({len(data['students'])}):"]
                for sid, s in data["students"].items():
                    lines.append(f"  {s['name']} ({sid})")
                return {"success": True, "result": "\n".join(lines)}
            return {"success": False, "result": "Actions: add_student, record, report, students"}
        except Exception as e:
            return {"success": False, "result": f"Attendance error: {e}"}


class EssayOutlineTool(BaseTool):
    def execute(self, params):
        topic = params.get("topic", "")
        style = params.get("style", "argumentative")
        paragraphs = min(int(params.get("paragraphs", params.get("count", 5))), 15)
        if not topic:
            return {"success": False, "result": "Provide essay topic"}
        templates = {
            "argumentative": [
                "I. Introduction", "   A. Hook / attention grabber",
                f"   B. Background on {topic}", "   C. Thesis statement (your position)",
                "II. Body Paragraph 1 — Main Argument",
                "   A. Topic sentence", "   B. Evidence / example", "   C. Analysis",
                "II/III. Body Paragraph 2 — Supporting Argument",
                "   A. Topic sentence", "   B. Evidence / example", "   C. Analysis",
                "III/IV. Body Paragraph 3 — Counterargument & Rebuttal",
                "   A. Opposing view", "   B. Rebuttal with evidence",
                "V. Conclusion", "   A. Restate thesis", "   B. Summarize main points",
                "   C. Closing thought / call to action",
            ],
            "expository": [
                "I. Introduction", "   A. Hook", f"   B. Context for {topic}",
                "   C. Thesis / main idea",
                "II. Body Paragraph 1 — Key Point 1",
                "   A. Explanation", "   B. Evidence", "   C. Connection",
                "III. Body Paragraph 2 — Key Point 2",
                "   A. Explanation", "   B. Evidence", "   C. Connection",
                "IV. Body Paragraph 3 — Key Point 3",
                "   A. Explanation", "   B. Evidence", "   C. Connection",
                "V. Conclusion", "   A. Summary", "   B. Significance / implications",
            ],
            "narrative": [
                "I. Introduction", "   A. Setting / scene setup",
                "   B. Characters involved", "   C. Thesis / central theme",
                "II. Rising Action / Events",
                "   A. Event 1", "   B. Event 2", "   C. Event 3",
                "III. Climax / Turning Point",
                "   A. Key moment", "   B. Emotional impact",
                "IV. Falling Action", "   A. Consequences", "   B. Resolution begins",
                "V. Conclusion", "   A. Reflection / lesson learned",
                "   B. Closing image or thought",
            ],
        }
        lines = [f"Essay Outline: {topic}", f"Style: {style}", "=" * 40]
        if style.lower() in templates:
            lines.extend(templates[style.lower()])
        else:
            lines.append(f"I. Introduction (on {topic})")
            for i in range(2, paragraphs):
                lines.append(f"{chr(64+i)}. Body Paragraph {i-1}")
                lines.append(f"   A. Main point / evidence")
            lines.append(f"{chr(64+paragraphs)}. Conclusion")
        return {"success": True, "result": "\n".join(lines)}


class CitationTool(BaseTool):
    def execute(self, params):
        style = params.get("style", "mla").lower()
        source_type = params.get("type", "book").lower()
        author = params.get("author", "")
        title = params.get("title", "")
        publisher = params.get("publisher", "")
        year = params.get("year", params.get("date", ""))
        pages = params.get("pages", params.get("page", ""))
        url = params.get("url", "")
        journal = params.get("journal", params.get("publication", ""))
        volume = params.get("volume", "")
        issue = params.get("issue", params.get("number", ""))
        website = params.get("website", publisher)
        if not title:
            return {"success": False, "result": "At minimum, provide the title"}
        auth_part = f"{author}. " if author else ""
        title_part = f"\"{title}.\" " if source_type in ("article", "webpage", "chapter") else f"*{title}.* "
        if style == "mla":
            if source_type == "book":
                citation = f"{auth_part}*{title}.* {publisher}{', ' + year if year else ''}."
            elif source_type == "article":
                citation = f"{auth_part}\"{title}.\" *{journal}*{', vol. ' + volume if volume else ''}{', no. ' + issue if issue else ''}{' (' + year + ')' if year else ''}{': ' + pages if pages else ''}."
            elif source_type == "website":
                citation = f"{auth_part}\"{title}.\" *{website}*{', ' + year if year else ''}{', ' + url if url else ''}."
            else:
                citation = f"{auth_part}*{title}.* {publisher if publisher else 'n.p.'}, {year if year else 'n.d.'}."
        elif style == "apa":
            year_part = f"({year})" if year else "(n.d.)"
            if source_type == "book":
                citation = f"{author}{', ' if author else ''}{year_part}. *{title}*. {publisher}."
            elif source_type == "article":
                citation = f"{author}{', ' if author else ''}{year_part}. {title}. *{journal}*{', ' + volume if volume else ''}{'(' + issue + ')' if issue else ''}{', ' + pages if pages else ''}.{'' + url if url else ''}"
            elif source_type == "website":
                citation = f"{author}{', ' if author else ''}{year_part}. {title}. {website}. {url}"
            else:
                citation = f"{author}{', ' if author else ''}{year_part}. *{title}*. {publisher if publisher else 'n.p.'}."
        elif style == "chicago":
            if source_type == "book":
                citation = f"{author}. *{title}*. {publisher}, {year}."
            elif source_type == "article":
                citation = f"{author}. \"{title}.\" *{journal}* {volume}, no. {issue} ({year}): {pages}."
            elif source_type == "website":
                citation = f"{author}. \"{title}.\" {website}. {url}."
            else:
                citation = f"{author}. *{title}*. {publisher}, {year}."
        else:
            return {"success": False, "result": "Styles: mla, apa, chicago"}
        return {"success": True, "result": citation}


class ThesaurusTool(BaseTool):
    _DATA = {
        "good": {"synonyms": ["excellent", "fine", "satisfactory", "superb", "quality"],
                 "antonyms": ["bad", "poor", "inferior", "terrible"]},
        "bad": {"synonyms": ["poor", "terrible", "awful", "inferior", "substandard"],
                "antonyms": ["good", "excellent", "superb"]},
        "big": {"synonyms": ["large", "huge", "enormous", "massive", "vast", "immense"],
                "antonyms": ["small", "tiny", "minute"]},
        "small": {"synonyms": ["tiny", "minute", "compact", "petite", "minor"],
                  "antonyms": ["big", "large", "huge", "enormous"]},
        "happy": {"synonyms": ["joyful", "cheerful", "delighted", "elated", "glad"],
                  "antonyms": ["sad", "unhappy", "miserable", "gloomy"]},
        "sad": {"synonyms": ["unhappy", "miserable", "gloomy", "melancholy", "sorrowful"],
                "antonyms": ["happy", "joyful", "elated", "cheerful"]},
        "smart": {"synonyms": ["intelligent", "clever", "brilliant", "bright", "sharp"],
                  "antonyms": ["stupid", "dull", "dumb"]},
        "beautiful": {"synonyms": ["gorgeous", "stunning", "lovely", "attractive", "magnificent"],
                      "antonyms": ["ugly", "hideous", "plain"]},
        "fast": {"synonyms": ["quick", "rapid", "swift", "speedy", "hasty"],
                 "antonyms": ["slow", "sluggish", "leisurely"]},
        "slow": {"synonyms": ["sluggish", "leisurely", "unhurried", "gradual"],
                 "antonyms": ["fast", "quick", "rapid", "swift"]},
        "important": {"synonyms": ["significant", "crucial", "vital", "essential", "key"],
                      "antonyms": ["unimportant", "trivial", "minor"]},
        "difficult": {"synonyms": ["hard", "challenging", "tough", "complex", "demanding"],
                      "antonyms": ["easy", "simple", "effortless"]},
        "easy": {"synonyms": ["simple", "effortless", "straightforward", "basic"],
                 "antonyms": ["difficult", "hard", "challenging", "complex"]},
        "interesting": {"synonyms": ["engaging", "fascinating", "captivating", "intriguing"],
                        "antonyms": ["boring", "dull", "tedious"]},
        "new": {"synonyms": ["fresh", "novel", "modern", "recent", "innovative"],
                "antonyms": ["old", "ancient", "outdated"]},
        "old": {"synonyms": ["ancient", "aged", "elderly", "antique", "outdated"],
                "antonyms": ["new", "young", "fresh", "modern"]},
        "strong": {"synonyms": ["powerful", "robust", "sturdy", "resilient", "tough"],
                   "antonyms": ["weak", "fragile", "feeble"]},
        "weak": {"synonyms": ["fragile", "feeble", "delicate", "frail"],
                 "antonyms": ["strong", "powerful", "robust", "sturdy"]},
        "funny": {"synonyms": ["humorous", "amusing", "comical", "hilarious", "witty"],
                  "antonyms": ["serious", "solemn", "grave"]},
        "brave": {"synonyms": ["courageous", "fearless", "bold", "valiant", "heroic"],
                  "antonyms": ["cowardly", "timid", "fearful"]},
    }

    def execute(self, params):
        word = params.get("word", "").strip().lower()
        action = params.get("action", "synonyms")
        if not word:
            return {"success": False, "result": "Provide a word"}
        if word in self._DATA:
            entry = self._DATA[word]
            if action == "synonyms":
                return {"success": True, "result": f"Synonyms for '{word}': {', '.join(entry['synonyms'])}"}
            elif action == "antonyms":
                return {"success": True, "result": f"Antonyms for '{word}': {', '.join(entry['antonyms'])}"}
            elif action == "all":
                return {"success": True, "result":
                        f"'{word}'\nSynonyms: {', '.join(entry['synonyms'])}\nAntonyms: {', '.join(entry['antonyms'])}"}
        return {"success": True, "result": f"No thesaurus entry for '{word}'. Try: good, bad, big, happy, smart, etc."}


class StatisticsTool(BaseTool):
    def execute(self, params):
        data_str = params.get("data", params.get("numbers", ""))
        if not data_str:
            return {"success": False, "result": "Provide comma-separated numbers"}
        try:
            nums = [float(x.strip()) for x in data_str.split(",") if x.strip()]
        except ValueError:
            return {"success": False, "result": "All values must be numbers"}
        if len(nums) < 2:
            return {"success": False, "result": "Need at least 2 numbers"}
        n = len(nums)
        s = sum(nums)
        mean = s / n
        sorted_nums = sorted(nums)
        median = sorted_nums[n // 2] if n % 2 else (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
        freq = {}
        for x in nums:
            freq[x] = freq.get(x, 0) + 1
        max_freq = max(freq.values())
        mode = [str(k) for k, v in freq.items() if v == max_freq]
        variance = sum((x - mean) ** 2 for x in nums) / n
        std_dev = math.sqrt(variance)
        result = (
            f"Count: {n}\n"
            f"Sum: {s}\n"
            f"Mean: {mean:.4f}\n"
            f"Median: {median:.4f}\n"
            f"Mode: {', '.join(mode)} (freq: {max_freq})\n"
            f"Min: {min(nums)}\n"
            f"Max: {max(nums)}\n"
            f"Range: {max(nums) - min(nums)}\n"
            f"Variance: {variance:.4f}\n"
            f"Std Dev: {std_dev:.4f}"
        )
        return {"success": True, "result": result}


class PrimeTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "check")
        try:
            if action == "check":
                n = int(params.get("number", params.get("n", 0)))
                if n < 2:
                    return {"success": True, "result": f"{n} is not prime"}
                for i in range(2, int(math.isqrt(n)) + 1):
                    if n % i == 0:
                        return {"success": True, "result": f"{n} is not prime (divisible by {i})"}
                return {"success": True, "result": f"{n} is prime!"}
            elif action == "factors":
                n = int(params.get("number", params.get("n", 0)))
                if n < 2:
                    return {"success": True, "result": f"{n}: no prime factors"}
                temp = n
                factors = []
                for i in range(2, int(math.isqrt(n)) + 1):
                    while temp % i == 0:
                        factors.append(i)
                        temp //= i
                if temp > 1:
                    factors.append(temp)
                return {"success": True, "result": f"Factors of {n}: {' × '.join(map(str, factors))}"}
            elif action == "list":
                limit = int(params.get("limit", params.get("max", 100)))
                sieve = [True] * (limit + 1)
                sieve[0] = sieve[1] = False
                for i in range(2, int(math.isqrt(limit)) + 1):
                    if sieve[i]:
                        for j in range(i * i, limit + 1, i):
                            sieve[j] = False
                primes = [str(i) for i, is_p in enumerate(sieve) if is_p]
                return {"success": True, "result": f"Primes up to {limit} ({len(primes)}):\n{', '.join(primes[:50])}" + ("..." if len(primes) > 50 else "")}
            elif action == "next":
                n = int(params.get("number", params.get("n", 0)))
                candidate = n + 1
                while True:
                    is_p = candidate >= 2
                    for i in range(2, int(math.isqrt(candidate)) + 1):
                        if candidate % i == 0:
                            is_p = False
                            break
                    if is_p:
                        return {"success": True, "result": f"Next prime after {n}: {candidate}"}
                    candidate += 1
            return {"success": False, "result": "Actions: check, factors, list, next"}
        except ValueError:
            return {"success": False, "result": "Provide a valid number"}


class MatrixTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "add")
        try:
            a_str = params.get("a", params.get("matrix_a", ""))
            b_str = params.get("b", params.get("matrix_b", ""))
            if not a_str:
                return {"success": False, "result": "Provide matrix_a (rows; separated by |, values comma-separated)"}
            def parse(m):
                rows = m.split("|")
                return [[float(x.strip()) for x in row.split(",") if x.strip()] for row in rows if row.strip()]
            a = parse(a_str)
            if action == "add":
                b = parse(b_str)
                if len(a) != len(b) or len(a[0]) != len(b[0]):
                    return {"success": False, "result": "Matrices must have same dimensions"}
                result = [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]
            elif action == "multiply":
                b = parse(b_str)
                if len(a[0]) != len(b):
                    return {"success": False, "result": f"Cannot multiply {len(a)}x{len(a[0])} by {len(b)}x{len(b[0])}"}
                result = [[sum(a[i][k] * b[k][j] for k in range(len(a[0]))) for j in range(len(b[0]))] for i in range(len(a))]
            elif action == "determinant":
                if len(a) != len(a[0]):
                    return {"success": False, "result": "Matrix must be square"}
                result = [[self._det(a)]]
            elif action == "transpose":
                result = [[a[j][i] for j in range(len(a))] for i in range(len(a[0]))]
            else:
                return {"success": False, "result": "Actions: add, multiply, determinant, transpose"}
            lines = [f"Result ({len(result)}x{len(result[0])}):"]
            for row in result:
                lines.append("  [" + ", ".join(f"{v:.2f}" for v in row) + "]")
            return {"success": True, "result": "\n".join(lines)}
        except Exception as e:
            return {"success": False, "result": f"Matrix error: {e}"}

    def _det(self, m):
        if len(m) == 1:
            return m[0][0]
        if len(m) == 2:
            return m[0][0] * m[1][1] - m[0][1] * m[1][0]
        d = 0
        for c in range(len(m)):
            sub = [[m[r][cc] for cc in range(len(m)) if cc != c] for r in range(1, len(m))]
            d += ((-1) ** c) * m[0][c] * self._det(sub)
        return d


class PeriodicTableTool(BaseTool):
    _ELEMENTS = [
        ("H", "Hydrogen", 1, 1.008, "Nonmetal"), ("He", "Helium", 2, 4.003, "Noble Gas"),
        ("Li", "Lithium", 3, 6.941, "Alkali Metal"), ("Be", "Beryllium", 4, 9.012, "Alkaline Earth"),
        ("B", "Boron", 5, 10.811, "Metalloid"), ("C", "Carbon", 6, 12.011, "Nonmetal"),
        ("N", "Nitrogen", 7, 14.007, "Nonmetal"), ("O", "Oxygen", 8, 15.999, "Nonmetal"),
        ("F", "Fluorine", 9, 18.998, "Halogen"), ("Ne", "Neon", 10, 20.180, "Noble Gas"),
        ("Na", "Sodium", 11, 22.990, "Alkali Metal"), ("Mg", "Magnesium", 12, 24.305, "Alkaline Earth"),
        ("Al", "Aluminum", 13, 26.982, "Metal"), ("Si", "Silicon", 14, 28.086, "Metalloid"),
        ("P", "Phosphorus", 15, 30.974, "Nonmetal"), ("S", "Sulfur", 16, 32.065, "Nonmetal"),
        ("Cl", "Chlorine", 17, 35.453, "Halogen"), ("Ar", "Argon", 18, 39.948, "Noble Gas"),
        ("K", "Potassium", 19, 39.098, "Alkali Metal"), ("Ca", "Calcium", 20, 40.078, "Alkaline Earth"),
        ("Fe", "Iron", 26, 55.845, "Transition Metal"), ("Cu", "Copper", 29, 63.546, "Transition Metal"),
        ("Zn", "Zinc", 30, 65.380, "Transition Metal"), ("Ag", "Silver", 47, 107.868, "Transition Metal"),
        ("Au", "Gold", 79, 196.967, "Transition Metal"), ("Hg", "Mercury", 80, 200.590, "Transition Metal"),
        ("Pb", "Lead", 82, 207.200, "Metal"), ("U", "Uranium", 92, 238.029, "Actinide"),
    ]
    _DICT = {e[0].lower(): e for e in _ELEMENTS}
    _DICT.update({e[1].lower(): e for e in _ELEMENTS})
    _DICT.update({str(e[2]): e for e in _ELEMENTS})

    def execute(self, params):
        query = params.get("element", params.get("query", "")).strip().lower()
        if not query:
            lines = ["Periodic Table — Quick Reference:", ""]
            for sym, name, num, mass, cat in self._ELEMENTS:
                lines.append(f"  {num:3d} {sym:3s} {name:12s} {mass:7.3f}  {cat}")
            return {"success": True, "result": "\n".join(lines)}
        entry = self._DICT.get(query)
        if not entry:
            return {"success": False, "result": f"Element not found. Try: H, Helium, 6, etc."}
        sym, name, num, mass, cat = entry
        return {"success": True, "result":
                f"Element: {name} ({sym})\n"
                f"Atomic Number: {num}\n"
                f"Atomic Mass: {mass:.3f} u\n"
                f"Category: {cat}"}


class PhysicsRefTool(BaseTool):
    def execute(self, params):
        topic = params.get("topic", params.get("query", "")).strip().lower()
        formulas = {
            "kinematics": {
                "desc": "Motion equations",
                "formulas": [
                    "v = u + at",
                    "s = ut + ½at²",
                    "v² = u² + 2as",
                    "s = ½(u + v)t",
                ]
            },
            "newton": {
                "desc": "Newton's Laws",
                "formulas": [
                    "F = ma (2nd Law)",
                    "F = G·m₁·m₂ / r² (Gravity)",
                    "Weight = mg",
                    "Friction = μN",
                ]
            },
            "energy": {
                "desc": "Energy & Work",
                "formulas": [
                    "KE = ½mv²",
                    "PE = mgh",
                    "Work = F·d·cosθ",
                    "Power = W / t",
                ]
            },
            "electricity": {
                "desc": "Electricity",
                "formulas": [
                    "V = IR (Ohm's Law)",
                    "P = VI",
                    "E = V·I·t",
                    "R = ρL / A",
                    "C = Q / V",
                ]
            },
            "waves": {
                "desc": "Waves & Optics",
                "formulas": [
                    "v = fλ",
                    "n₁·sinθ₁ = n₂·sinθ₂ (Snell's Law)",
                    "1/f = 1/v + 1/u (Lens)",
                    "E = hf (Photon)",
                ]
            },
            "thermodynamics": {
                "desc": "Thermodynamics",
                "formulas": [
                    "Q = mcΔT (Heat)",
                    "PV = nRT (Ideal Gas)",
                    "ΔU = Q - W (1st Law)",
                    "e = 1 - T_c/T_h (Carnot)",
                ]
            },
        }
        if not topic:
            lines = ["Physics Formulas — Topics:"]
            for k, v in formulas.items():
                lines.append(f"  • {k}: {v['desc']}")
            return {"success": True, "result": "\n".join(lines)}
        topic_key = None
        for k in formulas:
            if topic in k or k in topic:
                topic_key = k
                break
        if not topic_key:
            return {"success": True, "result": f"Topics: {', '.join(formulas.keys())}"}
        entry = formulas[topic_key]
        lines = [f"{entry['desc'].upper()}:", ""]
        lines.extend(entry["formulas"])
        return {"success": True, "result": "\n".join(lines)}


class FormulaTool(BaseTool):
    def execute(self, params):
        topic = params.get("topic", params.get("query", "")).strip().lower()
        formulas = {
            "area": {
                "desc": "Area formulas",
                "entries": [
                    ("Circle", "A = πr²"),
                    ("Triangle", "A = ½bh"),
                    ("Rectangle", "A = lw"),
                    ("Trapezoid", "A = ½(a+b)h"),
                    ("Sphere surface", "A = 4πr²"),
                ]
            },
            "volume": {
                "desc": "Volume formulas",
                "entries": [
                    ("Cube", "V = s³"),
                    ("Sphere", "V = ⁴⁄₃πr³"),
                    ("Cylinder", "V = πr²h"),
                    ("Cone", "V = ⅓πr²h"),
                    ("Pyramid", "V = ⅓Bh"),
                ]
            },
            "geometry": {
                "desc": "Geometry",
                "entries": [
                    ("Pythagorean", "a² + b² = c²"),
                    ("Circumference", "C = 2πr"),
                    ("Distance", "d = √((x₂-x₁)² + (y₂-y₁)²)"),
                    ("Midpoint", "M = ((x₁+x₂)/2, (y₁+y₂)/2)"),
                ]
            },
            "trigonometry": {
                "desc": "Trigonometry",
                "entries": [
                    ("sin θ = opposite/hypotenuse", "sin²θ + cos²θ = 1"),
                    ("cos θ = adjacent/hypotenuse", "tan θ = sinθ/cosθ"),
                    ("Law of Sines", "a/sinA = b/sinB = c/sinC"),
                    ("Law of Cosines", "c² = a² + b² - 2ab·cosC"),
                ]
            },
            "calculus": {
                "desc": "Calculus",
                "entries": [
                    ("Derivative", "d/dx xⁿ = nxⁿ⁻¹"),
                    ("Power rule", "∫xⁿ dx = xⁿ⁺¹/(n+1) + C"),
                    ("Product rule", "(fg)' = f'g + fg'"),
                    ("Chain rule", "f(g(x))' = f'(g(x))·g'(x)"),
                ]
            },
            "algebra": {
                "desc": "Algebra",
                "entries": [
                    ("Quadratic formula", "x = (-b ± √(b²-4ac)) / 2a"),
                    ("Slope", "m = (y₂-y₁)/(x₂-x₁)"),
                    ("Logarithm", "log_b(x) = y → bʸ = x"),
                    ("Binomial", "(a+b)ⁿ = Σ(k=0..n) C(n,k)aⁿ⁻ᵏbᵏ"),
                ]
            },
        }
        if not topic:
            lines = ["Math Formulas — Topics:"]
            for k, v in formulas.items():
                lines.append(f"  • {k}: {v['desc']}")
            return {"success": True, "result": "\n".join(lines)}
        topic_key = None
        for k in formulas:
            if topic in k or k in topic:
                topic_key = k
                break
        if not topic_key:
            return {"success": True, "result": f"Topics: {', '.join(formulas.keys())}"}
        entry = formulas[topic_key]
        lines = [f"{entry['desc'].upper()}:", ""]
        for name, formula in entry["entries"]:
            lines.append(f"  {name}: {formula}")
        return {"success": True, "result": "\n".join(lines)}


class DOILookupTool(BaseTool):
    def execute(self, params):
        doi = params.get("doi", params.get("id", "")).strip()
        if not doi:
            return {"success": False, "result": "Provide a DOI (e.g., 10.1038/nature12373)"}
        try:
            url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            msg = data.get("message", {})
            title = msg.get("title", ["Unknown"])[0]
            authors = msg.get("author", [])
            author_names = [f"{a.get('given','')} {a.get('family','')}".strip() for a in authors[:5]]
            year = (msg.get("published-print") or msg.get("published-online") or {}).get("date-parts", [[""]])[0][0]
            journal = msg.get("container-title", [""])[0]
            publisher = msg.get("publisher", "")
            lines = [f"DOI: {doi}", f"Title: {title}"]
            if author_names:
                lines.append(f"Authors: {', '.join(author_names)}{'…' if len(authors) > 5 else ''}")
            if year:
                lines.append(f"Year: {year}")
            if journal:
                lines.append(f"Journal: {journal}")
            if publisher:
                lines.append(f"Publisher: {publisher}")
            return {"success": True, "result": "\n".join(lines)}
        except urllib.error.HTTPError as e:
            return {"success": False, "result": f"DOI not found (HTTP {e.code})"}
        except Exception as e:
            return {"success": False, "result": f"DOI lookup error: {e}"}


class ArxivTool(BaseTool):
    def execute(self, params):
        query = params.get("query", params.get("search", ""))
        count = min(int(params.get("count", params.get("max_results", 5))), 20)
        if not query:
            return {"success": False, "result": "Provide a search query"}
        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results={count}&sortBy=relevance"
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = resp.read().decode()
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            entries = root.findall("a:entry", ns)
            if not entries:
                return {"success": True, "result": "No results found"}
            lines = [f"arXiv results for '{query}':"]
            for entry in entries[:count]:
                title = entry.find("a:title", ns).text.strip().replace("\n", " ")
                authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)][:3]
                link = entry.find("a:id", ns).text
                published = entry.find("a:published", ns).text[:10]
                lines.append(f"\n• {title}")
                lines.append(f"  Authors: {', '.join(authors)}{'…' if len(authors) > 3 else ''}")
                lines.append(f"  {published} | {link}")
            return {"success": True, "result": "\n".join(lines)}
        except Exception as e:
            return {"success": False, "result": f"Arxiv error: {e}"}


class VocabTool(BaseTool):
    _WORDS = [
        ("ephemeral", "lasting for a very short time", "The ephemeral beauty of cherry blossoms"),
        ("ubiquitous", "present everywhere at once", "Smartphones have become ubiquitous"),
        ("pragmatic", "dealing with things practically", "A pragmatic approach to problem-solving"),
        ("ambiguous", "open to multiple interpretations", "The ambiguous wording confused everyone"),
        ("paradigm", "a typical example or pattern", "A shift in the scientific paradigm"),
        ("eloquent", "fluent and persuasive in speaking", "An eloquent speech moved the audience"),
        ("resilient", "able to recover quickly", "The resilient community rebuilt after the storm"),
        ("meticulous", "showing great attention to detail", "Her meticulous research was praised"),
        ("candid", "truthful and straightforward", "A candid conversation about the issues"),
        ("profound", "very great or intense", "A profound insight changed my perspective"),
        ("innovative", "introducing new ideas", "The innovative design won awards"),
        ("diligent", "careful and persistent effort", "A diligent student always does their best"),
        ("empirical", "based on observation or experience", "Empirical evidence supports the theory"),
        ("abstract", "existing in thought rather than matter", "Abstract concepts can be hard to grasp"),
        ("collaborate", "work jointly on an activity", "Teams collaborate on complex projects"),
    ]

    def execute(self, params):
        action = params.get("action", "random")
        if action == "random":
            word, meaning, example = random.choice(self._WORDS)
            return {"success": True, "result": f"📖 {word}\n  Definition: {meaning}\n  Example: \"{example}\""}
        elif action == "list":
            lines = ["Vocabulary Builder:"]
            for word, meaning, _ in self._WORDS:
                lines.append(f"  • {word}: {meaning}")
            return {"success": True, "result": "\n".join(lines)}
        elif action == "search":
            q = params.get("word", "").strip().lower()
            for word, meaning, example in self._WORDS:
                if q == word.lower():
                    return {"success": True, "result": f"📖 {word}\n  Definition: {meaning}\n  Example: \"{example}\""}
            return {"success": False, "result": f"Word '{q}' not in vocabulary. Try: random, list"}
        return {"success": False, "result": "Actions: random, list, search"}


class MnemonicTool(BaseTool):
    PATTERNS = {
        "acronym": lambda words: "".join(w[0].upper() for w in words if w),
        "sentence": lambda words: " ".join(w if random.random() > 0.5 else w.upper() for w in words),
        "rhyme": lambda words: f"{' '.join(words[:2])} is what you need, {words[-1] if len(words) > 2 else ''} is the key!",
    }

    def execute(self, params):
        items_str = params.get("items", params.get("words", ""))
        pattern = params.get("pattern", "acronym")
        if not items_str:
            return {"success": False, "result": "Provide items to memorize (comma-separated)"}
        words = [w.strip() for w in items_str.split(",") if w.strip()]
        if len(words) < 2:
            return {"success": False, "result": "Need at least 2 items"}
        if pattern == "acronym":
            acro = "".join(w[0].upper() for w in words)
            result = f"Acronym: {acro}\n  ({', '.join(words)})"
        elif pattern == "sentence":
            random.shuffle(words)
            result = f"Sentence: {' '.join(w if random.random() > 0.4 else w.upper() for w in words)}"
        elif pattern == "story":
            story = f"Imagine you are walking through a {words[0].lower()}..."
            for w in words[1:]:
                story += f" Suddenly, a {w.lower()} appears!"
            result = f"Story: {story}"
        else:
            return {"success": False, "result": "Patterns: acronym, sentence, story"}
        return {"success": True, "result": f"Mnemonic ({pattern}):\n{result}"}


class NoteSummarizeTool(BaseTool):
    def execute(self, params):
        text = params.get("text", params.get("notes", ""))
        if not text:
            return {"success": False, "result": "Provide text to summarize"}
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= 2:
            return {"success": True, "result": f"Summary: {text[:500]}"}
        words = text.split()
        total_words = len(words)
        target = max(1, total_words // 3)
        # Simple extractive summarization: take first sentence, then pick most informative
        summary_sentences = [sentences[0]]
        available = sentences[1:]
        available.sort(key=lambda s: len(s.split()), reverse=True)
        current_len = len(summary_sentences[0].split())
        for s in available:
            if current_len >= target:
                break
            summary_sentences.append(s)
            current_len += len(s.split())
        lines = [
            f"Original: {total_words} words, {len(sentences)} sentences",
            f"Summary: {len(summary_sentences)} sentences, {current_len} words",
            "",
            "Key Points:",
        ]
        for i, s in enumerate(summary_sentences, 1):
            lines.append(f"  {i}. {s}")
        return {"success": True, "result": "\n".join(lines)}


class ConjugationTool(BaseTool):
    _CONJ = {
        "run": {"base": "run", "past": "ran", "pp": "run", "ing": "running", "s": "runs"},
        "write": {"base": "write", "past": "wrote", "pp": "written", "ing": "writing", "s": "writes"},
        "speak": {"base": "speak", "past": "spoke", "pp": "spoken", "ing": "speaking", "s": "speaks"},
        "eat": {"base": "eat", "past": "ate", "pp": "eaten", "ing": "eating", "s": "eats"},
        "drink": {"base": "drink", "past": "drank", "pp": "drunk", "ing": "drinking", "s": "drinks"},
        "go": {"base": "go", "past": "went", "pp": "gone", "ing": "going", "s": "goes"},
        "be": {"base": "be", "past": "was/were", "pp": "been", "ing": "being", "s": "is"},
        "have": {"base": "have", "past": "had", "pp": "had", "ing": "having", "s": "has"},
        "make": {"base": "make", "past": "made", "pp": "made", "ing": "making", "s": "makes"},
        "take": {"base": "take", "past": "took", "pp": "taken", "ing": "taking", "s": "takes"},
        "see": {"base": "see", "past": "saw", "pp": "seen", "ing": "seeing", "s": "sees"},
        "know": {"base": "know", "past": "knew", "pp": "known", "ing": "knowing", "s": "knows"},
        "think": {"base": "think", "past": "thought", "pp": "thought", "ing": "thinking", "s": "thinks"},
        "give": {"base": "give", "past": "gave", "pp": "given", "ing": "giving", "s": "gives"},
        "find": {"base": "find", "past": "found", "pp": "found", "ing": "finding", "s": "finds"},
        "tell": {"base": "tell", "past": "told", "pp": "told", "ing": "telling", "s": "tells"},
        "read": {"base": "read", "past": "read", "pp": "read", "ing": "reading", "s": "reads"},
        "teach": {"base": "teach", "past": "taught", "pp": "taught", "ing": "teaching", "s": "teaches"},
        "learn": {"base": "learn", "past": "learned", "pp": "learned", "ing": "learning", "s": "learns"},
        "study": {"base": "study", "past": "studied", "pp": "studied", "ing": "studying", "s": "studies"},
    }

    def execute(self, params):
        verb = params.get("verb", params.get("word", "")).strip().lower()
        tense = params.get("tense", params.get("action", "all"))
        if not verb:
            return {"success": True, "result":
                    f"Verb Conjugation (irregular verbs):\n{', '.join(sorted(self._CONJ.keys()))}\n\nRegular verbs: add -ed for past, -ing for continuous"}
        if verb in self._CONJ:
            v = self._CONJ[verb]
            if tense == "past":
                return {"success": True, "result": f"Past tense of '{verb}': {v['past']}"}
            elif tense == "present":
                return {"success": True, "result": f"Present tense of '{verb}': {v['base']} / {v['s']}"}
            elif tense == "continuous":
                return {"success": True, "result": f"Continuous of '{verb}': {v['ing']}"}
            lines = [f"Conjugation: {verb}", "",
                     f"Base: {v['base']}", f"Past: {v['past']}", f"Past Participle: {v['pp']}",
                     f"Continuous: {v['ing']}", f"Third Person: {v['s']}"]
            return {"success": True, "result": "\n".join(lines)}
        # Regular verb
        if verb.endswith("e"):
            past = verb + "d"
        elif verb.endswith("y") and len(verb) > 2 and verb[-2] not in "aeiou":
            past = verb[:-1] + "ied"
        else:
            past = verb + "ed"
        ing = verb + ("ing" if not verb.endswith("e") else verb[:-1] + "ing")
        s = verb + ("s" if not verb.endswith(("s", "x", "ch", "sh", "o")) else verb + "es")
        lines = [f"Conjugation: {verb}", "", f"Base: {verb}", f"Past: {past}",
                 f"Past Participle: {past}", f"Continuous: {ing}", f"Third Person: {s}"]
        return {"success": True, "result": "\n".join(lines)}


class SpellCheckTool(BaseTool):
    def execute(self, params):
        text = params.get("text", "").strip()
        if not text:
            return {"success": False, "result": "Provide text to check"}
        common_words = {
            "accomodate": "accommodate", "recieve": "receive", "wierd": "weird",
            "seperate": "separate", "occured": "occurred", "occurance": "occurrence",
            "definately": "definitely", "tommorrow": "tomorrow", "calender": "calendar",
            "neccessary": "necessary", "embarass": "embarrass", "goverment": "government",
            "alot": "a lot", "untill": "until", "wierd": "weird", "beleive": "believe",
            "acheive": "achieve", "adress": "address", "begining": "beginning",
            "commitee": "committee", "concensus": "consensus", "concious": "conscious",
            "contagious": "contagious", "decieve": "deceive", "desparate": "desperate",
            "dilemna": "dilemma", "disappear": "disappear", "embarass": "embarrass",
            "enviornment": "environment", "exagerate": "exaggerate", "febuary": "february",
            "foriegn": "foreign", "fourty": "forty", "freind": "friend",
            "guarantee": "guarantee", "harrass": "harass", "hierarchy": "hierarchy",
            "humour": "humor", "independant": "independent", "interrupt": "interrupt",
            "jewelery": "jewelry", "judgment": "judgment", "liason": "liaison",
            "libary": "library", "licence": "license", "maintainance": "maintenance",
            "millenium": "millennium", "miniscule": "minuscule", "mischievious": "mischievous",
            "misspell": "misspell", "morgage": "mortgage", "nineth": "ninth",
            "noticable": "noticeable", "occassion": "occasion", "occurence": "occurrence",
            "pavillion": "pavilion", "persistant": "persistent", "pharoah": "pharaoh",
            "playright": "playwright", "posession": "possession", "preceed": "precede",
            "privilege": "privilege", "priviledge": "privilege", "procede": "proceed",
            "pronounciation": "pronunciation", "publicly": "publicly", "pumpkim": "pumpkin",
            "questionaire": "questionnaire", "reccomend": "recommend", "refered": "referred",
            "refering": "referring", "religous": "religious", "remeber": "remember",
            "resistence": "resistance", "restaraunt": "restaurant", "rehersal": "rehearsal",
            "sargeant": "sergeant", "seige": "siege", "similiar": "similar",
            "skilful": "skillful", "somwhere": "somewhere", "sophmore": "sophomore",
            "specificaly": "specifically", "sponser": "sponsor", "stomach": "stomach",
            "supercede": "supersede", "surelly": "surely", "surprize": "surprise",
            "tatoo": "tattoo", "threshhold": "threshold", "tommorow": "tomorrow",
            "tounge": "tongue", "truely": "truly", "twelth": "twelfth", "tyrany": "tyranny",
            "vaccuum": "vacuum", "vegitable": "vegetable", "vehical": "vehicle",
            "visable": "visible", "wednesday": "wednesday", "wether": "weather",
            "wich": "which", "writen": "written", "wierd": "weird", "zealous": "zealous",
        }
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        suggestions = []
        for w in words:
            lower = w.lower()
            if lower in common_words and common_words[lower] != lower:
                suggestions.append(f"  '{w}' → '{common_words[lower]}'")
        if suggestions:
            return {"success": True, "result": "Spelling suggestions:\n" + "\n".join(suggestions)}
        return {"success": True, "result": "No common spelling errors found. ✓"}


class GroupPickerTool(BaseTool):
    def execute(self, params):
        names_str = params.get("names", params.get("students", ""))
        group_count = max(1, int(params.get("groups", params.get("count", 0))))
        per_group = max(1, int(params.get("per_group", 0)))
        if not names_str:
            return {"success": False, "result": "Provide comma-separated student names"}
        names = [n.strip() for n in names_str.split(",") if n.strip()]
        if len(names) < 2:
            return {"success": False, "result": "Need at least 2 students"}
        random.shuffle(names)
        if group_count > 0:
            groups = [[] for _ in range(group_count)]
            for i, name in enumerate(names):
                groups[i % group_count].append(name)
        elif per_group > 0:
            groups = [names[i:i+per_group] for i in range(0, len(names), per_group)]
        else:
            return {"success": False, "result": "Provide groups= or per_group="}
        lines = [f"Groups ({len(names)} students):"]
        for i, g in enumerate(groups, 1):
            lines.append(f"\nGroup {i} ({len(g)} members):")
            for name in g:
                lines.append(f"  • {name}")
        return {"success": True, "result": "\n".join(lines)}


class RubricTool(BaseTool):
    def execute(self, params):
        assignment = params.get("assignment", params.get("title", "Assignment"))
        criteria_str = params.get("criteria", params.get("items", ""))
        levels = int(params.get("levels", 4))
        if not criteria_str:
            return {"success": False, "result": "Provide comma-separated criteria (e.g., Content, Clarity, Research)"}
        criteria = [c.strip() for c in criteria_str.split(",") if c.strip()]
        level_names = {4: ["Below", "Developing", "Proficient", "Exemplary"],
                       3: ["Developing", "Proficient", "Exemplary"],
                       5: ["Beginning", "Developing", "Proficient", "Advanced", "Exemplary"]}
        level_labels = level_names.get(levels, level_names[4])
        max_score = levels
        lines = [f"Grading Rubric: {assignment}", "=" * 40, f"Scale: {levels} levels (1-{levels})", ""]
        for c in criteria:
            lines.append(f"\n{c} (Weight: {100 // len(criteria)}%):")
            for i, lbl in enumerate(level_labels, 1):
                lines.append(f"  {i} - {lbl}: {random.choice([
                    f"Minimal {c.lower()}",
                    f"Basic {c.lower()}",
                    f"Good {c.lower()}",
                    f"Excellent {c.lower()}",
                    f"Outstanding {c.lower()}",
                ][:levels - i + 1])}")
        lines.append(f"\nTotal possible: {len(criteria)} × {max_score} = {len(criteria) * max_score} pts")
        return {"success": True, "result": "\n".join(lines)}


class SyllabusTool(BaseTool):
    def execute(self, params):
        course = params.get("course", params.get("title", "Course"))
        weeks = min(int(params.get("weeks", params.get("duration", 16))), 20)
        topics_str = params.get("topics", "")
        topics = [t.strip() for t in topics_str.split(",") if t.strip()] if topics_str else []
        lines = [f"Syllabus: {course}", "=" * 40, f"Duration: {weeks} weeks", ""]
        lines.append("Required Materials:")
        lines.append("  • Textbook (TBD)")
        lines.append("  • Notebook and writing materials")
        lines.append("  • Access to course website")
        lines.append("\nGrading Breakdown:")
        lines.append("  • Participation: 10%")
        lines.append("  • Homework/Assignments: 30%")
        lines.append("  • Midterm Exam: 25%")
        lines.append("  • Final Exam/Project: 35%")
        lines.append("\nCourse Schedule:")
        for w in range(1, weeks + 1):
            topic = topics[w - 1] if w <= len(topics) else f"Topic {w}"
            lines.append(f"\nWeek {w}: {topic}")
            lines.append(f"  • Reading assignment")
            lines.append(f"  • {random.choice(['Homework due', 'Quiz', 'Lab exercise', 'Discussion post'])}")
        lines.append("\nPolicies:")
        lines.append("  • Late work: 10% penalty per day")
        lines.append("  • Academic integrity: All work must be your own")
        return {"success": True, "result": "\n".join(lines)}


class PracticeProblemTool(BaseTool):
    def execute(self, params):
        subject = params.get("subject", params.get("topic", "math")).lower()
        count = min(int(params.get("count", 3)), 10)
        difficulty = params.get("difficulty", "medium")
        problems = []
        if "math" in subject or "algebra" in subject:
            for i in range(count):
                a, b = random.randint(2, 12), random.randint(2, 12)
                ops = [("+", a + b), ("-", max(a, b) - min(a, b)),
                       ("×", a * b)]
                if difficulty == "hard":
                    ops.append(("÷", a * b // max(b, 1) if a * b % max(b, 1) == 0 else "fraction"))
                op, ans = random.choice(ops)
                problems.append(f"{i+1}. {max(a,b)} {op} {min(a,b)} = ?  [Answer: {ans}]")
        elif "physics" in subject:
            for i in range(count):
                m, a_num = random.randint(2, 20), random.randint(1, 10)
                problems.append(f"{i+1}. F = ma: mass={m}kg, a={a_num}m/s², F=?  [Answer: {m*a_num}N]")
        elif "chem" in subject:
            for i in range(count):
                problems.append(f"{i+1}. Balance: H₂ + O₂ → H₂O  [Answer: 2H₂ + O₂ → 2H₂O]")
        else:
            for i in range(count):
                problems.append(f"{i+1}. Describe a key concept in {subject}.")
        return {"success": True, "result": f"Practice Problems ({subject}, {difficulty}):\n" + "\n".join(problems)}


class ScienceFactTool(BaseTool):
    _FACTS = [
        "Water expands when it freezes, which is why ice floats.",
        "Light travels at about 299,792,458 m/s in a vacuum.",
        "The human body contains about 60% water.",
        "DNA was first discovered in 1869 by Friedrich Miescher.",
        "The speed of sound is about 343 m/s at sea level.",
        "A single lightning bolt contains enough energy to toast 100,000 slices of bread.",
        "Honey never spoils — archaeologists found 3000-year-old edible honey in Egyptian tombs.",
        "Octopuses have three hearts and blue blood.",
        "Bananas are technically berries, but strawberries aren't.",
        "The periodic table has 118 confirmed elements.",
        "Sound travels 4.3× faster in water than in air.",
        "A day on Venus is longer than its year.",
        "The human brain generates enough electricity to power a small LED.",
        "There are more trees on Earth than stars in the Milky Way (~3 trillion).",
        "The Great Red Spot on Jupiter is a storm larger than Earth.",
        "Oxygen makes up about 21% of Earth's atmosphere.",
        "A bolt of lightning is 5× hotter than the surface of the sun.",
        "The Earth's core is about as hot as the sun's surface (~5500°C).",
        "Fingernails grow about 3.5 mm per month.",
        "The heart beats about 100,000 times per day.",
    ]

    def execute(self, params):
        action = params.get("action", "random")
        topic = params.get("topic", "").strip().lower()
        if action == "random":
            return {"success": True, "result": f"🔬 {random.choice(self._FACTS)}"}
        elif action == "list":
            lines = [f"Science Facts ({len(self._FACTS)}):"]
            for i, f in enumerate(self._FACTS, 1):
                lines.append(f"{i}. {f}")
            return {"success": True, "result": "\n".join(lines)}
        elif action == "search":
            results = [f for f in self._FACTS if topic in f.lower()]
            if results:
                return {"success": True, "result": "🔬 " + results[0]}
            return {"success": False, "result": "No matching facts"}
        return {"success": False, "result": "Actions: random, list, search"}


class StudyPlanTool(BaseTool):
    def execute(self, params):
        subject = params.get("subject", params.get("topic", "a subject"))
        days = min(int(params.get("days", 7)), 30)
        hours = min(float(params.get("hours", params.get("per_day", 2))), 12)
        lines = [f"Study Plan: {subject.title()}", f"Duration: {days} days, {hours}h/day",
                 "=" * 40, "Tips:", "  • Review material within 24 hours of learning",
                 "  • Use active recall (quiz yourself, don't just re-read)",
                 "  • Space repetitions across multiple days",
                 "  • Take a 5-min break every 25 minutes", ""]
        topics = [f"Introduction to {subject}", f"Core Concepts of {subject}",
                  f"Intermediate {subject} Topics", f"Advanced {subject} Concepts",
                  f"Practical Applications", f"Review & Practice", f"Assessment"]
        for day in range(1, days + 1):
            topic = topics[(day - 1) % len(topics)]
            r = random.random()
            if r < 0.4:
                activity = f"Study: {topic}"
            elif r < 0.7:
                activity = f"Practice problems on {topic}"
            elif r < 0.85:
                activity = f"Review previous material ({random.choice(topics[:max(day-1,1)])})"
            else:
                activity = "Take a practice quiz"
            lines.append(f"Day {day:2d}: {activity} ({hours:.1f}h)")
        return {"success": True, "result": "\n".join(lines)}


class NoteOrganizerTool(BaseTool):
    def execute(self, params):
        action = params.get("action", "add")
        path = os.path.join(_STUDY_DIR, "notebook.json")
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    notebook = json.load(f)
            else:
                notebook = {"subjects": {}, "notes": []}
            if action == "add":
                subject = params.get("subject", params.get("class", "General")).strip()
                title = params.get("title", "Untitled").strip()
                content_note = params.get("content", params.get("notes", "")).strip()
                tags_str = params.get("tags", "")
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                if not content_note:
                    return {"success": False, "result": "Provide note content"}
                note = {
                    "id": str(time.time()),
                    "subject": subject,
                    "title": title,
                    "content": content_note[:2000],
                    "tags": tags,
                    "created": time.time(),
                }
                notebook["notes"].append(note)
                if subject not in notebook["subjects"]:
                    notebook["subjects"][subject] = {"count": 0, "created": time.time()}
                notebook["subjects"][subject]["count"] += 1
                with open(path, "w") as f:
                    json.dump(notebook, f)
                return {"success": True, "result": f"Note added: {title} ({subject})"}
            elif action == "list":
                subject = params.get("subject", "")
                pool = [n for n in notebook["notes"] if not subject or n.get("subject") == subject]
                if not pool:
                    return {"success": True, "result": "No notes found"}
                lines = [f"Notes ({len(pool)}):"]
                for n in sorted(pool, key=lambda x: x.get("created", 0), reverse=True)[:20]:
                    lines.append(f"  • [{n.get('subject','General')}] {n.get('title','Untitled')}")
                return {"success": True, "result": "\n".join(lines)}
            elif action == "search":
                query = params.get("query", "").strip().lower()
                if not query:
                    return {"success": False, "result": "Provide a search query"}
                matches = [n for n in notebook["notes"] if query in n.get("content", "").lower()
                           or query in n.get("title", "").lower()
                           or query in n.get("subject", "").lower()]
                if not matches:
                    return {"success": True, "result": "No matches"}
                lines = [f"Found {len(matches)} notes:"]
                for n in matches[:10]:
                    lines.append(f"  • [{n.get('subject','General')}] {n.get('title','Untitled')}")
                return {"success": True, "result": "\n".join(lines)}
            elif action == "subjects":
                lines = [f"Subjects ({len(notebook['subjects'])}):"]
                for s, d in sorted(notebook["subjects"].items()):
                    lines.append(f"  • {s} ({d['count']} notes)")
                return {"success": True, "result": "\n".join(lines)}
            return {"success": False, "result": "Actions: add, list, search, subjects"}
        except Exception as e:
            return {"success": False, "result": f"Note error: {e}"}


def create_default_registry():
    registry = ToolRegistry()
    registry.register("web_search", WebSearchTool())
    registry.register("file_read", FileIOTool())
    registry.register("file_write", FileIOTool())
    registry.register("run_command", SystemControlTool())
    registry.register("calculator", CalculatorTool())
    registry.register("weather", WeatherTool())
    registry.register("time", TimeTool())
    registry.register("system_info", SystemInfoTool())
    registry.register("screenshot", ScreenshotTool())
    registry.register("notes", NotesTool())
    registry.register("todo", TodoTool())
    registry.register("clipboard", ClipboardTool())
    registry.register("define", DictTool())
    registry.register("joke", JokesTool())
    registry.register("quote", QuoteTool())
    registry.register("password", PasswordTool())
    registry.register("convert", ConvertTool())
    registry.register("file_search", FileSearchTool())
    registry.register("battery", BatteryTool())
    registry.register("process", ProcessTool())
    registry.register("random", RandomTool())
    registry.register("news", NewsTool())
    registry.register("shorten", ShortenTool())
    registry.register("ip_geo", IPGeoTool())
    registry.register("translate", TranslatorTool())
    registry.register("crypto", CryptoTool())
    registry.register("qr_code", QRCodeTool())
    registry.register("window", WindowTool())
    registry.register("audio", AudioTool())
    registry.register("network", NetworkTool())
    registry.register("archive", ArchiveTool())
    registry.register("json", JsonTool())
    registry.register("hash", HashTool())
    registry.register("ocr", OCRTool())
    registry.register("vision", VisionTool())
    registry.register("screen_watch", ScreenWatchTool())
    registry.register("input_control", InputControlTool())
    registry.register("edit", EditTool())
    registry.register("grep", GrepTool())
    registry.register("glob", GlobTool())
    registry.register("apply_patch", ApplyPatchTool())
    registry.register("webfetch", WebFetchTool())
    registry.register("question", QuestionTool())
    registry.register("skill", SkillTool())
    registry.register("todowrite", TodoWriteTool())
    registry.register("volume", VolumeControlTool())
    registry.register("media", MediaControlTool())
    registry.register("notification", NotificationTool())
    registry.register("disk", DiskTool())
    registry.register("wallpaper", WallpaperTool())
    registry.register("lock", LockScreenTool())
    registry.register("browser", BrowserTool())
    registry.register("env", EnvTool())
    registry.register("color", ColorTool())
    registry.register("unit", UnitTool())
    registry.register("math_eval", MathEvalTool())
    registry.register("idle", IdleTool())
    # Register existing unregistered tools
    registry.register("email", EmailTool())
    registry.register("calendar", CalendarTool())
    registry.register("reminder", ReminderTool())
    registry.register("timer", TimerTool())
    # New tools batch
    registry.register("public_ip", PublicIPTool())
    registry.register("ping", PingTool())
    registry.register("dns_lookup", DNSTool())
    registry.register("host_info", HostInfoTool())
    registry.register("timestamp", TimestampTool())
    registry.register("timezone", TimezoneTool())
    registry.register("date_calc", DateCalcTool())
    registry.register("text", TextTool())
    registry.register("diff", DiffTool())
    registry.register("sort", SortTool())
    registry.register("regex", RegexTool())
    registry.register("uuid", UUIDTool())
    registry.register("base64", Base64Tool())
    registry.register("confirm", ConfirmTool())
    registry.register("prompt", PromptTool())
    registry.register("choose", ChooseTool())
    registry.register("beep", BeepTool())
    registry.register("sleep", SleepTool())
    registry.register("alarm", AlarmTool())
    registry.register("stopwatch", StopwatchTool())
    registry.register("file_info", FileInfoTool())
    registry.register("dir_list", DirListTool())
    registry.register("image_info", ImageInfoTool())
    registry.register("fact", FactTool())
    registry.register("lyric", LyricTool())
    registry.register("hn", HNReaderTool())
    registry.register("reddit", RedditTool())
    registry.register("wikipedia", WikipediaTool())
    registry.register("forecast", WeatherForecastTool())
    registry.register("currency", CurrencyTool())
    registry.register("stock", StockTool())
    registry.register("movie", MovieTool())
    registry.register("recipe", RecipeTool())
    registry.register("random_joke", RDJokeTool())
    # Display/UI tools
    registry.register("show", ShowTool())
    registry.register("alert", AlertTool())
    registry.register("csv_view", CsvTool())
    registry.register("json_format", JsonFormatTool())
    registry.register("brightness", BrightnessTool())
    registry.register("encode", EncodeTool())
    registry.register("chart", ChartTool())
    registry.register("markdown_render", MarkdownRenderTool())
    registry.register("screen_res", ScreenResTool())
    registry.register("counter", CounterTool())
    registry.register("progress", ProgressTool())
    registry.register("color_picker", ColorPickerTool())
    # Student & Teacher Tools (33)
    registry.register("flashcard", FlashcardTool())
    registry.register("quiz", QuizTool())
    registry.register("study_set", StudySetTool())
    registry.register("grade_calc", GradeCalcTool())
    registry.register("gpa", GPATool())
    registry.register("assignment", AssignmentTool())
    registry.register("study_timer", StudyTimerTool())
    registry.register("attendance", AttendanceTool())
    registry.register("essay_outline", EssayOutlineTool())
    registry.register("citation", CitationTool())
    registry.register("thesaurus", ThesaurusTool())
    registry.register("statistics", StatisticsTool())
    registry.register("prime", PrimeTool())
    registry.register("matrix", MatrixTool())
    registry.register("periodic_table", PeriodicTableTool())
    registry.register("physics_ref", PhysicsRefTool())
    registry.register("formula", FormulaTool())
    registry.register("doi_lookup", DOILookupTool())
    registry.register("arxiv", ArxivTool())
    registry.register("vocab", VocabTool())
    registry.register("mnemonic", MnemonicTool())
    registry.register("note_summarize", NoteSummarizeTool())
    registry.register("conjugation", ConjugationTool())
    registry.register("spell_check", SpellCheckTool())
    registry.register("group_picker", GroupPickerTool())
    registry.register("rubric", RubricTool())
    registry.register("syllabus", SyllabusTool())
    registry.register("practice_problem", PracticeProblemTool())
    registry.register("science_fact", ScienceFactTool())
    registry.register("study_plan", StudyPlanTool())
    registry.register("note_organizer", NoteOrganizerTool())
    registry.register("bibliography", BibliographyTool())
    registry.register("equation_solve", EquationSolveTool())
    return registry
