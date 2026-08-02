#!/usr/bin/env bash
# Launch all three processes in one container: Ollama, the FastAPI backend, and the Nuxt
# frontend. If any one exits, tear the container down so the orchestrator can restart it.
set -euo pipefail

MODEL="${DEMO_OPENAI_MODEL:-qwen2.5:3b}"

echo "[start] launching Ollama…"
ollama serve &

# Wait for the Ollama server to accept requests.
for _ in $(seq 1 60); do
  ollama list >/dev/null 2>&1 && break
  sleep 1
done

# The model is baked into the image; pull only if it was overridden at runtime.
if ! ollama list | awk 'NR>1 {print $1}' | grep -qx "${MODEL}"; then
  echo "[start] model ${MODEL} not present — pulling…"
  ollama pull "${MODEL}"
fi

echo "[start] launching backend on :8000…"
( cd /app/backend && exec uvicorn agentic_ui_demo.main:app --host 0.0.0.0 --port 8000 ) &

echo "[start] launching frontend on :3000…"
( cd /app/frontend && exec node .output/server/index.mjs ) &

echo "[start] all services up — frontend :3000 · backend :8000 · ollama :11434 (internal)"

# Exit (and stop the container) as soon as any service exits.
wait -n
echo "[start] a service exited — shutting the container down"
exit 1
