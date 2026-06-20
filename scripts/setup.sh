#!/usr/bin/env bash
set -e

echo "=== LocalMind Setup ==="

# 1. Python venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" --quiet

# 2. Env file
cp -n .env.example .env || true

# 3. Check Ollama
if command -v ollama &>/dev/null; then
  echo "✓ Ollama found"
  echo "Pulling models (may take a while on first run)..."
  ollama pull llama3.2:3b
  ollama pull nomic-embed-text
else
  echo "⚠ Ollama not found. Install from https://ollama.com then run:"
  echo "  ollama pull llama3.2:3b && ollama pull nomic-embed-text"
fi

echo ""
echo "=== Done. Run: ==="
echo "  source .venv/bin/activate"
echo "  uvicorn src.api.server:app --reload --port 8000"
