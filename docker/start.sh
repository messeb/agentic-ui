#!/usr/bin/env bash
# Launch the two processes in one container: the FastAPI backend and the Nuxt frontend.
# The backend talks to a remote chat-completions API (OpenAI / Azure OpenAI) configured via env.
# If any process exits, tear the container down so the orchestrator can restart it.
set -euo pipefail

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "[start] note: OPENAI_API_KEY is not set — the model approaches return 503 until you set it."
fi

echo "[start] backend (internal) on :8000…"
( cd /app/backend && exec uvicorn agentic_ui_demo.main:app --host 0.0.0.0 --port 8000 ) &

echo "[start] app on :${NITRO_PORT:-8080} (Nuxt serves the UI and proxies /api → backend)…"
( cd /app/frontend && exec node .output/server/index.mjs ) &

echo "[start] up — open http://localhost:${NITRO_PORT:-8080}"

# Exit (and stop the container) as soon as either service exits.
wait -n
echo "[start] a service exited — shutting the container down"
exit 1
