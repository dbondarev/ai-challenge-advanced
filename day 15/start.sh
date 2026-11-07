#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
umask 077
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
export DAY15_HOST=127.0.0.1
export DAY15_PORT="${DAY15_PORT:-8787}"
export UPSTREAM_URL="${UPSTREAM_URL:-http://127.0.0.1:11434/v1/chat/completions}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5-coder:7b}"
export PYTHONDONTWRITEBYTECODE=1
exec python3 server.py
