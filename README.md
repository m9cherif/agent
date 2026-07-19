# J.A.R.V.I.S

> Fully autonomous AI desktop assistant with voice, vision, and 57+ tools.

## 🚀 One-Command Setup

```bash
# Windows (open Command Prompt as Admin):
python setup.py

# Kali Linux / Debian:
python3 setup.py
```

**That's it.** The API key is built-in — it works immediately after setup.

---

## Manual Setup

### Windows
```
requirements.bat
python -m jarvis_app.main
```

### Kali Linux
```
chmod +x requirements.sh && sudo ./requirements.sh
python3 run_jarvis.py
```

## Use your own API key

Edit `.env` and set:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```
Get a free key at [openrouter.ai/keys](https://openrouter.ai/keys).

---

## What it does

- **Talk to it** — British male JARVIS voice, listens and responds
- **Sees your screen** — Real-time vision, frame change detection
- **Controls your PC** — Mouse, keyboard, windows, volume, media, files, browser
- **57 tools** — web search, calculator, weather, notes, todo, clipboard, OCR, QR codes, translation, crypto prices, news, and more
- **Iron Man HUD** — Animated eye with radar sweep, targeting reticle, data readouts

## Voice commands

Say these **instantly** (no AI delay):
- `"click"` / `"right click"` / `"double click"`
- `"move mouse to 500 300"`
- `"scroll down 5"`

## Default model

`google/gemini-2.0-flash-exp:free` (fast, correct JSON tool calls)

## License

MIT
