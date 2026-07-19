"""JARVIS Tools - 35+ tools for web, file, system, utilities"""

import json
import os
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
            url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode({
                "q": query, "format": "json", "no_html": "1", "skip_disambig": "1"
            })
            req = urllib.request.Request(url, headers={"User-Agent": "JarvisAssistant/2.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                abstract = data.get("Abstract", "") or data.get("AbstractText", "")
                source = data.get("AbstractSource", "")
                heading = data.get("Heading", "")
                if not abstract:
                    topics = data.get("RelatedTopics", [])
                    if topics:
                        first = topics[0]
                        if isinstance(first, dict):
                            text = first.get("Text", first.get("Result", ""))
                            abstract = re.sub(r'<[^>]+>', '', text)
                result = abstract or "No results found"
                if heading:
                    result = f"**{heading}**\n{result}"
                if source:
                    result += f"\n*Source: {source}*"
                return {"success": True, "result": result}
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
            # Use RSS-to-JSON via DuckDuckGo or similar free sources
            query = topic if topic else "latest news"
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/2.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            results = []
            heading = data.get("Heading", "")
            abstract = data.get("Abstract", "") or data.get("AbstractText", "")
            if heading and abstract:
                results.append(f"• {heading}: {abstract[:200]}")
            related = data.get("RelatedTopics", [])
            for r in related[:5]:
                if isinstance(r, dict):
                    text = r.get("Text", r.get("Result", ""))
                    text = re.sub(r'<[^>]+>', '', text)
                    if text:
                        results.append(f"• {text[:200]}")
            if results:
                return {"success": True, "result": (f"News about '{topic}':\n" if topic else "Top stories:\n") + "\n".join(results)}
            return {"success": False, "result": "No news found. Try a different topic."}
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
            url = f"https://www.reddit.com/r/{subreddit}/{category}.json?limit={count}"
            req = urllib.request.Request(url, headers={"User-Agent": "JarvisAssistant/2.0"})
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
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
            extract = data.get("extract", "")
            if not extract:
                return {"success": True, "result": "No summary available"}
            return {"success": True, "result": f"**{data.get('title', query)}**\n{extract[:2000]}"}
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
                result += f"  {dates[i]}: {tmin[i]}–{tmax[i]}°C, {wc}, {precip[i]}mm rain\n"
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
            with urllib.request.urlopen(f"https://api.frankfurter.app/latest?from={from_cur}&to={to_cur}", timeout=10) as r:
                data = json.loads(r.read())
            rate = data.get("rates", {}).get(to_cur, 1)
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
            with urllib.request.urlopen(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", timeout=10) as r:
                data = json.loads(r.read())
            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            price = meta.get("regularMarketPrice", meta.get("previousClose", "N/A"))
            name = meta.get("exchangeName", "")
            currency = meta.get("currency", "USD")
            return {"success": True, "result": f"{symbol} ({name}): ${price} {currency}"}
        except Exception as e:
            return {"success": False, "result": f"Stock error: {e}"}


class MovieTool(BaseTool):
    def execute(self, params):
        title = params.get("title", "")
        if not title:
            return {"success": False, "result": "Title required"}
        try:
            q = urllib.parse.quote(title)
            with urllib.request.urlopen(f"https://www.omdbapi.com/?t={q}&apikey=2c9d2e0e", timeout=10) as r:
                data = json.loads(r.read())
            if data.get("Response") == "False":
                return {"success": False, "result": data.get("Error", "Movie not found")}
            return {"success": True, "result": f"**{data.get('Title')}** ({data.get('Year')})\nRating: {data.get('imdbRating')}/10\nGenre: {data.get('Genre')}\nDirector: {data.get('Director')}\nPlot: {data.get('Plot', '')[:500]}"}
        except Exception as e:
            return {"success": False, "result": f"Movie error: {e}"}


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
    return registry
