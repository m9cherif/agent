# JARVIS Architecture

## Overview

JARVIS follows a modular architecture with five primitives:
**Intelligence**, **Engine**, **Agents**, **Tools & Memory**, and **UI**.

```
┌──────────────────────────────────────────────────────────┐
│                     JARVIS SYSTEM                         │
├──────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐   │
│  │                   UI LAYER                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │   │
│  │  │ Tray Icon│  │   Chat   │  │    Settings    │  │   │
│  │  │ (Qt)     │  │   Panel  │  │    Dialog      │  │   │
│  │  └──────────┘  └──────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│                         │                                │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │               AGENT ORCHESTRATOR                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │   │
│  │  │  ReAct   │  │   Tool   │  │    Memory      │  │   │
│  │  │   Loop   │  │ Registry │  │     Store      │  │   │
│  │  │          │  │          │  │   (SQLite)     │  │   │
│  │  └──────────┘  └──────────┘  └────────────────┘  │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                                │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │                 AI ENGINE                         │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │           OpenRouter Client                │  │   │
│  │  │  POST https://openrouter.ai/api/v1/        │  │   │
│  │  │       chat/completions                     │  │   │
│  │  │  Headers: Authorization: Bearer <key>      │  │   │
│  │  │           Content-Type: application/json   │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │      Local Fallback (Ollama/llama.cpp)     │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                                │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │               TOOLS LAYER                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │   │
│  │  │ Web      │ │  File    │ │  System  │         │   │
│  │  │ Search   │ │  I/O     │ │  Control │         │   │
│  │  ├──────────┤ ├──────────┤ ├──────────┤         │   │
│  │  │Calculatr │ │ Desktop  │ │  Browser │         │   │
│  │  │          │ │  Auto    │ │  Auto    │         │   │
│  │  └──────────┘ └──────────┘ └──────────┘         │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │           Plugin System (MCP)              │  │   │
│  │  └────────────────────────────────────────────┘  │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                                │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │              VOICE PIPELINE                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │   │
│  │  │  Sherpa  │  │ Whisper  │  │    Coqui       │  │   │
│  │  │  ONNX    │  │  .cpp    │  │    Piper       │  │   │
│  │  │ Wake Word│  │   STT    │  │     TTS        │  │   │
│  │  └──────────┘  └──────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│                         │                                │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │              SECURITY LAYER                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │   │
│  │  │Governance│  │  Creds   │  │   Audit Log    │  │   │
│  │  │  Levels  │  │ Manager  │  │                │  │   │
│  │  └──────────┘  └──────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## Component Details

### 1. UI Layer (C++/Qt Widgets)
- **TrayManager**: System tray icon with context menu (show/hide, settings, quit)
- **ChatPanel**: Scrolling chat interface with message history
- **SettingsDialog**: API key, model selection, voice toggle, governance level
- **MainWindow**: Central coordinator, status bar, tool activity log

### 2. Agent Orchestrator (C++)
- **ReAct Loop**: Thought-Action-Observation cycle for tool use
- **Tool Registry**: Maps tool names to implementations
- **Memory Store**: SQLite-backed conversation history and preferences

### 3. AI Engine (C++/Qt Network)
- **OpenRouter Client**: HTTP POST to `/api/v1/chat/completions`
- Supports streaming and non-streaming responses
- Configurable model, base URL, API key
- Fallback model support (e.g., `openrouter/free`)

### 4. Tools Layer (C++ + Python)
- **C++ Tools**: WebSearch, FileIO, SystemControl, Calculator
- **Python Tools**: Desktop automation (pyautogui), Browser automation (Playwright)
- **Plugin System**: Loads Python modules with manifest.json

### 5. Voice Pipeline (Python)
- **Sherpa-ONNX**: Wake word detection ("Hey Jarvis")
- **Whisper.cpp**: Speech to text transcription
- **Coqui Piper**: Text to speech synthesis
- Communicates with C++ via stdout JSON protocol

### 6. Memory (SQLite)
- Conversations table with session tracking
- Preferences key-value store
- Context storage for cross-session memory

### 7. Security
- Governance levels (0=low, 1=medium, 2=high)
- Path sanitization (blocks system dir writes)
- Credential encryption (XOR + Base64)
- Audit logging through signal/slot

## Data Flow

1. User speaks → Sherpa detects wake word → Whisper STT → text
2. User types text → ChatPanel → AgentOrchestrator.processUserInput()
3. ReAct Loop: LLM call → parse response → if tool action, execute tool
4. Tool result → back to LLM → final response → display + TTS
5. All interactions logged to SQLite MemoryStore

## API Integration

```http
POST https://openrouter.ai/api/v1/chat/completions
Authorization: Bearer <api_key>
Content-Type: application/json

{
  "model": "openrouter/free",
  "messages": [
    {"role": "system", "content": "You are JARVIS..."},
    {"role": "user", "content": "What's the weather?"}
  ],
  "max_tokens": 4096,
  "stream": false
}
```

## Model Files

| Model | Source | Size | Purpose |
|-------|--------|------|---------|
| Sherpa ONNX | github.com/k2-fsa/sherpa-onnx | ~10MB | Wake word detection |
| Whisper ggml | hugging.co/ggerganov/whisper.cpp | ~50MB | Speech-to-text |
| Piper ONNX | hugging.co/rhasspy/piper-voices | ~20MB | Text-to-speech |
