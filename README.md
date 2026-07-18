# J.A.R.V.I.S — Autonomous AI Desktop Assistant

Voice-first AI assistant with real-time screen vision, mouse/keyboard control, and 57+ tools. Powered by OpenRouter.

## Features

- **Voice Interface** — British male JARVIS voice (edge-tts), SAPI fallback
- **Real-time Screen Vision** — Background 2fps capture, frame differencing, change detection
- **Full Desktop Control** — Mouse move/click/drag/scroll, keyboard type/hotkeys via `SendInput`
- **57+ Tools** — Screen watch, window management, file ops, web search, OCR, calculator, weather, notes, todo, crypto, QR, clipboard, translation, and more
- **Unlimited Tool Chaining** — AI calls tools recursively until your task is done
- **Iron Man HUD** — Animated eye, radar sweep, rotating hex, scanning arcs, data readouts
- **Sound Effects** — Startup chime, message/thinking/done/error sounds

## Quick Start

```bash
# Windows
requirements.bat

# Kali Linux / Debian
chmod +x requirements.sh && ./requirements.sh
```

```bash
# Configure API key
copy .env.example .env
# Edit .env — set OPENROUTER_API_KEY

# Launch
python -m jarvis_app.main
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key (required) | — |
| `OPENROUTER_BASE_URL` | API endpoint | `https://openrouter.ai/api/v1` |
| `JARVIS_MODEL` | LLM model | `google/gemini-2.0-flash-exp:free` |
| `JARVIS_GOVERNANCE_LEVEL` | Security (0=all, 1=blocked, 2=read-only) | `1` |

## Tools

`web_search`, `file_read`, `file_write`, `run_command`, `calculator`, `weather`, `time`, `system_info`, `screenshot`, `vision`, `ocr`, `screen_watch`, `input_control`, `window(list/maximize/minimize/focus/close/move)`, `volume`, `media`, `notification`, `disk(cpu/ram/disk)`, `idle`, `browser`, `wallpaper`, `lock`, `env`, `color`, `unit`, `math_eval`, `notes`, `todo`, `todowrite`, `clipboard`, `define`, `joke`, `quote`, `random`, `convert`, `translate`, `audio`, `network`, `crypto`, `qr_code`, `json`, `hash`, `archive`, `news`, `shorten`, `ip_geo`, `process`, `file_search`, `password`, `edit`, `grep`, `glob`, `apply_patch`, `webfetch`, `question`, `skill`, `battery` — **57 total**

## Voice Commands

- "click" / "right click" / "double click" — instant mouse actions (bypasses AI)
- "move mouse to X Y" — instant cursor movement
- "scroll up/down N" — instant scroll

## Security

Governance levels control tool access:
- **0 (Low)** — All tools allowed
- **1 (Medium)** — Destructive actions blocked (default)
- **2 (High)** — Read-only tools, system commands blocked

## License

MIT
