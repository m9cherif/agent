"""Agent Orchestrator with fast ReAct loop for JARVIS"""

import json
import re
import threading


PLAN_PROMPT_EXTRA = """
You are in PLAN MODE. Describe the steps you would take but DO NOT execute any tools.
Explain your plan clearly, listing each step and what tool you would use.
When the user switches to BUILD mode, you can execute."""

BUILD_PROMPT = """You are JARVIS — a fully autonomous AI agent with unlimited tool calls. Call user "boss". Be concise.
You have FULL mouse + keyboard control via input_control. Use it for ALL frontend/UI tasks.
You can use as many tools as needed in sequence — there is no limit.

For seeing what's on screen in REAL TIME:
- screen_watch(read): instantly returns what's currently visible on screen (continuously monitored)
- screen_watch(capture): takes a fresh screenshot and returns vision analysis
- screen_watch(start): begin continuous screen monitoring (describes changes as they happen)
- screen_watch(stop): stop continuous monitoring

Examples:
User: what is 2+2?
Assistant: {"tool":"calculator","params":{"expression":"2+2"}}
User: time?
Assistant: {"tool":"time","params":{}}
User: weather in London
Assistant: {"tool":"weather","params":{"location":"London"}}
User: read README.md
Assistant: {"tool":"file_read","params":{"path":"README.md","action":"read"}}
User: find files with .py extension
Assistant: {"tool":"glob","params":{"pattern":"*.py"}}
User: search for "function" in main.py
Assistant: {"tool":"grep","params":{"pattern":"function","path":"main.py"}}
User: fetch https://example.com
Assistant: {"tool":"webfetch","params":{"url":"https://example.com"}}
User: hello
Assistant: Hello boss! How can I help?

For ANY screen interaction (windows, menus, buttons, dialogs, taskbar, system tray):
1. window(list) to find target name & hwnd
2. window(get_rect, hwnd=ID) for position/size/center coordinates
3. input_control(move, x=CX, y=CY) then input_control(click) to interact
4. Or keyboard: input_control(type, text), input_control(press, key), input_control(hotkey, keys=[])

input_control: move(x,y), move_rel(dx,dy), click(button,x,y), right/double click, drag(x,y,dx,dy), scroll(clicks), type(text), press(key), hotkey(keys[]), keydown/up(key), position, screenshot.

Keys: enter, tab, shift, ctrl, alt, space, backspace, delete, escape, arrows, home, end, pageup/down, f1-f12, capslock, printscreen, insert, win, menu, volume/nexttrack/playpause, browserback/forward/refresh, sleep, zoom, 0-9, a-z, + symbols by name.

For file operations: file_read(path), file_write(path,content), edit(filePath,old,new[,replaceAll]), grep(pattern[,path]), glob(pattern), file_search(query).

All tools: calculator, time, weather, window(list/get_rect/maximize/minimize/restore/focus/close/move), input_control(FULL), web_search, system_info, battery, disk(cpu/ram/disk), idle(uptime/idle), volume(get/set/mute), media(play_pause/next/prev), browser(url), notification, wallpaper, lock(lock/sleep), env, color(hex/rgb/hsl), unit(convert), math_eval, notes, todo, todowrite, define, joke, quote, random, convert, translate, audio, network, screenshot, vision, ocr, clipboard, crypto, qr_code, json, hash, archive, news, shorten, ip_geo, process, file_search, password, file_read, file_write, run_command, edit, grep, glob, apply_patch, webfetch, question, skill, screen_watch.

window action guide:
- list → shows visible windows with hwnd + title
- maximize(hwnd or name) → full-screen the window
- minimize(hwnd or name) → minimize to taskbar
- focus(hwnd or name) → bring to front
- close(hwnd or name) → close window
- move(hwnd or name, x, y, width, height) → resize and reposition
- get_rect(hwnd) → get position & center coordinates

For math use calculator or math_eval. For answers use direct text. You have unlimited tool calls — keep going until the task is done."""


class AgentOrchestrator:
    def __init__(self, ai_engine, tool_registry, memory_store, governance):
        self.ai = ai_engine
        self.tools = tool_registry
        self.memory = memory_store
        self.governance = governance
        self.max_iterations = 100
        self._callbacks = {}
        self._iteration = 0
        self.mode = "build"

    def set_mode(self, mode):
        self.mode = mode
        self._emit("mode_change", mode)

    def get_mode(self):
        return self.mode

    def _on_chunk(self, text):
        self._emit("partial", text)

    def on(self, event, callback):
        self._callbacks[event] = callback

    def _emit(self, event, *args):
        cb = self._callbacks.get(event)
        if cb:
            cb(*args)

    def process_input(self, user_input):
        self._iteration = 0

        # Handle /commands
        if user_input.startswith("/"):
            self._handle_command(user_input)
            return

        self.memory.add_entry("user", user_input)
        self._emit("thinking", "Processing...")
        self._react_loop(user_input)

    def _handle_command(self, cmd):
        parts = cmd.strip().split()
        command = parts[0].lower()
        args = parts[1:]

        if command == "/help":
            self._emit("response", "Commands: /help, /clear, /new, /save [name], /load [name], /sessions, /plan, /build, /model <name>, /undo, /mode")
        elif command == "/clear":
            self.memory.clear_conversation()
            self._emit("response", "Conversation cleared.")
        elif command == "/new":
            self.memory.new_session()
            self._emit("response", "New session started.")
        elif command == "/save":
            name = args[0] if args else None
            path = self.memory.save_session(name)
            self._emit("response", f"Session saved: {path}")
        elif command == "/load":
            if not args:
                self._emit("response", "Usage: /load <session_name>")
                return
            ok, msg = self.memory.load_session(args[0])
            self._emit("response", msg)
        elif command == "/sessions":
            sessions = self.memory.list_sessions()
            if not sessions:
                self._emit("response", "No saved sessions.")
                return
            lines = [f"{s['name']} ({s['messages']} msgs)" for s in sessions[:10]]
            self._emit("response", "Sessions:\n" + "\n".join(lines))
        elif command == "/plan":
            self.set_mode("plan")
            self._emit("response", "Switched to PLAN mode. I'll describe steps without executing.")
        elif command == "/build":
            self.set_mode("build")
            self._emit("response", "Switched to BUILD mode. I'll execute tools.")
        elif command == "/model":
            if not args:
                self._emit("response", f"Current model: {self.ai.get_model()}")
                return
            self.ai.set_model(args[0])
            self._emit("response", f"Model set to {args[0]}")
        elif command == "/undo":
            self._emit("response", "Undo not implemented in this version.")
        elif command == "/mode":
            self._emit("response", f"Current mode: {self.mode.upper()}")
        else:
            self._emit("response", f"Unknown command: {command}. Try /help")

    def _get_system_prompt(self):
        base = BUILD_PROMPT
        if self.mode == "plan":
            base += PLAN_PROMPT_EXTRA
        return base

    def _react_loop(self, user_input):
        self._iteration += 1
        if self._iteration > self.max_iterations:
            self._emit("response", "Max iterations reached.")
            return

        messages = [{"role": "system", "content": self._get_system_prompt()}]
        for h in self.memory.get_history(8):
            messages.append(h)
        messages.append({"role": "user", "content": user_input})

        def on_complete(success, response):
            if not success:
                self._emit("error", response)
                return
            if not response or not response.strip():
                self.memory.add_entry("assistant", "Done.")
                self._emit("response", "Done.")
                return

            action = self._parse_action(response)
            if action:
                self._execute_tool(action)
            else:
                self.memory.add_entry("assistant", response)
                self._emit("response", response)

        try:
            self.ai.send_message(messages, on_chunk=self._on_chunk, on_complete=on_complete)
        except Exception as e:
            self._emit("error", f"Loop error: {e}")

    def _parse_action(self, text):
        if not text:
            return None
        idx = 0
        while True:
            start = text.find('{', idx)
            if start == -1:
                break
            depth = 0
            for i in range(start, len(text)):
                c = text[i]
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        raw = text[start:i+1]
                        try:
                            obj = json.loads(raw)
                            if isinstance(obj, dict) and "tool" in obj and "params" in obj:
                                return {"tool": str(obj["tool"]), "params": obj["params"]}
                        except json.JSONDecodeError:
                            pass
                        idx = i + 1
                        break
            else:
                break
        return None

    def _execute_tool(self, action):
        tool_name = action.get("tool", "")
        params = action.get("params", {})

        if self.mode == "plan":
            desc = f"[PLAN] Would use {tool_name} with params: {json.dumps(params, ensure_ascii=False)[:200]}"
            self.memory.add_entry("assistant", desc)
            self._emit("response", desc)
            return

        allowed, reason = self.governance.is_action_allowed(tool_name, params)
        if not allowed:
            self.memory.add_entry("assistant", f"{tool_name} blocked: {reason}")
            self._react_loop("The tool was blocked. Try a different approach.")
            return

        tool = self.tools.get(tool_name)
        if not tool:
            self.memory.add_entry("assistant", f"Tool '{tool_name}' not found")
            self._react_loop("The tool is not available. Try a different tool or give the answer directly.")
            return

        self._emit("thinking", f"Running {tool_name}...")
        try:
            result = tool.execute(params)
        except Exception as e:
            self.memory.add_entry("user", f"Tool {tool_name} crashed: {e}\nTry a different approach.")
            self._react_loop("The tool crashed. Try a different approach.")
            return
        self._emit("tool_result", tool_name, str(result)[:200])

        if isinstance(result, dict) and result.get("_is_question"):
            text = result.get("result", "")
            self.memory.add_entry("assistant", text)
            self._emit("response", text)
            return

        self.memory.add_entry("user", f"[{tool_name}] {result}")
        self._react_loop("Continue. Use another tool or give the answer.")
