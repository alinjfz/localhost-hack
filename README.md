# LocalMind — Fully Offline Persistent AI Agent

> Built for the **Localhost: On-Device Agent Hackathon** · June 20, 2026

An autonomous AI agent that runs **entirely offline** on your device. No internet. No cloud. Just local inference, persistent knowledge-graph memory, and tool use.

## Architecture

```
┌─────────────────────────────────────┐
│           Web UI (port 8000)        │
└──────────────┬──────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────┐
│         FastAPI Server              │
│         src/api/server.py           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Agent Core Loop             │
│  • Ollama / Exo Labs (inference)    │
│  • Cognee  (knowledge-graph memory) │
│  • Overmind (trace collection)      │
│  • Tools: files, python, datetime   │
└─────────────────────────────────────┘
```

## Track Partners Used

| Partner | How |
|---|---|
| **Exo Labs** | Local LLM inference (Llama 3.2 or DeepSeek) |
| **Cognee** | Persistent knowledge-graph memory across sessions |
| **Overmind** | Agent trace collection for post-hoc fine-tuning |

## Quick Start

```bash
# 1. Install Ollama → https://ollama.com
ollama pull llama3.2:3b
ollama pull nomic-embed-text

# 2. Setup
bash scripts/setup.sh
source .venv/bin/activate

# 3. Run
uvicorn src.api.server:app --reload --port 8000

# 4. Open http://localhost:8000
```

## Environment

Copy `.env.example` → `.env` and adjust as needed.

To use **Exo Labs** instead of Ollama:
```
LLM_PROVIDER=exo
EXO_BASE_URL=http://localhost:52415
```

## Tests

```bash
pytest tests/ -v
```
