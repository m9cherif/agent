# JARVIS - Windows AI Desktop Assistant

A modular, agent-based desktop assistant for Windows with OpenRouter AI backend, voice pipeline, and extensible tool system.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                    JARVIS Core                    │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │
│  │   Tray   │  │   Chat   │  │   Settings     │ │
│  │  Manager │  │   Panel  │  │   Dialog       │ │
│  └────┬─────┘  └────┬─────┘  └───────┬────────┘ │
│       │              │               │           │
│  ┌────▼──────────────▼───────────────▼────────┐ │
│  │           Agent Orchestrator               │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │ │
│  │  │ ReAct    │  │ Tool     │  │ Memory   │ │ │
│  │  │ Loop     │  │ Registry │  │ Store    │ │ │
│  │  └──────────┘  └──────────┘  └──────────┘ │ │
│  └───────────────────┬────────────────────────┘ │
│                      │                          │
│  ┌───────────────────▼────────────────────────┐ │
│  │              AI Engine                      │ │
│  │  ┌──────────────────────────────────────┐  │ │
│  │  │         OpenRouter Client            │  │ │
│  │  │  POST /api/v1/chat/completions       │  │ │
│  │  └──────────────────────────────────────┘  │ │
│  └───────────────────┬────────────────────────┘ │
│                      │                          │
│  ┌───────────────────▼────────────────────────┐ │
│  │              Tools Layer                    │ │
│  │  WebSearch │ FileIO │ System │ Calculator  │ │
│  │  Desktop Auto │ Browser Auto │ Plugin Sys │ │
│  └───────────────────┬────────────────────────┘ │
│                      │                          │
│  ┌───────────────────▼────────────────────────┐ │
│  │           Voice Pipeline (Python)          │ │
│  │  Sherpa ONNX │ Whisper.cpp │ Coqui Piper   │ │
│  │  (Wake Word)  │    (STT)    │    (TTS)     │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Prerequisites

- Windows 10/11 64-bit
- Visual Studio 2022 (with C++ tools)
- CMake 3.20+
- Qt 6.5+
- Python 3.10+
- OpenRouter API key (free tier available)

## Quick Start

```bash
# 1. Clone and setup
git clone <repo> && cd jarvis
scripts\install_deps.bat

# 2. Configure API key
copy .env.example .env
# Edit .env with your OPENROUTER_API_KEY

# 3. Build
scripts\build.bat

# 4. Download voice models (optional)
scripts\download_models.bat

# 5. Run
dist\Jarvis.exe
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | - |
| `OPENROUTER_BASE_URL` | API base URL | `https://openrouter.ai/api/v1` |
| `JARVIS_MODEL` | LLM model | `openrouter/free` |
| `JARVIS_GOVERNANCE_LEVEL` | Security level (0-2) | `1` |

## Voice Pipeline

- **Wake Word**: Sherpa-ONNX detects "Hey Jarvis"
- **STT**: Whisper.cpp transcribes speech to text
- **TTS**: Coqui Piper synthesizes responses

```bash
# Test components individually
python src/python/jarvis_voice/wake_word.py
python src/python/jarvis_voice/stt_engine.py --duration 5
python src/python/jarvis_voice/tts_engine.py "Hello, I am JARVIS"
```

## Tool System

Tools are registered in the agent orchestrator and called via the ReAct loop:

| Tool | Description |
|------|-------------|
| `web_search` | DuckDuckGo search |
| `file_read` | Read file contents |
| `file_write` | Write to files |
| `run_command` | Execute system commands |
| `calculator` | Evaluate math expressions |
| `browser` | Playwright browser automation |
| `desktop` | PyAutoGUI desktop control |

## Plugin System

Plugins live in `plugins/` with a `manifest.json`:

```json
{
    "name": "my_skill",
    "version": "1.0.0",
    "entry_point": "plugin.py",
    "type": "python",
    "tools": [{"name": "my_tool", "description": "..."}]
}
```

## Security

Governance levels control tool access:
- **0 (Low)**: All tools allowed
- **1 (Medium)**: Destructive actions blocked (default)
- **2 (High)**: Read-only tools, system commands blocked

Credentials are encrypted with XOR + Base64 using a derived key.

## Project Structure

```
src/jarvis/          # C++ Qt application
  core/              # Config, Agent, ReAct, ToolRegistry
  ai/                 # AIEngine, OpenRouterClient
  ui/                # MainWindow, ChatPanel, Settings, Tray
  tools/             # WebSearch, FileIO, System, Calculator
  memory/            # SQLite MemoryStore
  security/          # Governance, CredentialManager
  plugins/           # PluginLoader
  voice/             # VoicePipeline (C++ process bridge)

src/python/          # Python workers
  jarvis_voice/      # Wake word, STT, TTS
  jarvis_tools/      # Desktop, Browser, System automation

tests/               # C++ and Python tests
scripts/             # Build, install, package scripts
plugins/             # Plugin examples
```

## Development

```bash
# Run C++ tests
cmake -B build -DBUILD_TESTING=ON
cmake --build build
build\tests\CppTests\Release\TestJarvis.exe

# Run Python tests
pytest tests/PythonTests/ -v

# Package
scripts\package.bat --portable
```

## Roadmap

- **MVP**: Voice interaction, chat UI, agent logic, LLM backend, basic tools, memory, security
- **v1**: Desktop/browser automation, plugin system, screen context, multi-user
- **Future**: Voice cloning, proactive assistant, cross-device, AR integration

## License

MIT
