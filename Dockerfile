# syntax=docker/dockerfile:1
#
# All-in-one, SLIM, self-contained image: Ollama (CPU-only, model baked in) + FastAPI backend +
# Nuxt frontend, in one container. Deployable on its own — no external API key, no runtime network.
#
#   docker build --provenance=false -t agentic-ui-patterns .
#   docker run --rm -p 3000:3000 -p 8000:8000 agentic-ui-patterns
#   → Frontend http://localhost:3000 · Backend http://localhost:8000/docs
#
# Defaults to qwen2.5:3b (~1.9 GB) — reliable tool calling for the agentic approaches.
# For a chat-only / even smaller image (weaker tool calling), pick a smaller model:
#   docker build --provenance=false --build-arg MODEL=qwen2.5:1.5b -t agentic-ui-patterns .

############################ 1. Build the Nuxt frontend → .output ############################
FROM node:22-slim AS frontend
RUN corepack enable
WORKDIR /app
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm run build

############################ 2. Strip Ollama to CPU-only (drops ~3.5 GB of GPU libs) ##########
FROM ollama/ollama:latest AS ollama
RUN rm -rf /usr/lib/ollama/cuda_* /usr/lib/ollama/*jetpack* /usr/lib/ollama/rocm*

############################ 3. Slim runtime ############################
FROM ubuntu:24.04 AS runtime
ARG MODEL=qwen2.5:3b
ENV DEBIAN_FRONTEND=noninteractive

# Minimal runtime deps: curl (healthcheck), TLS certs, and the C++/OpenMP libs ggml needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl libstdc++6 libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# Just the binaries we need — no npm, no apt Node, no GPU stack.
COPY --from=frontend /usr/local/bin/node /usr/local/bin/node
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=ollama /usr/bin/ollama /usr/bin/ollama
COPY --from=ollama /usr/lib/ollama /usr/lib/ollama
ENV LD_LIBRARY_PATH=/usr/lib/ollama

# --- Backend (Python via uv; uv fetches a managed CPython) ---
WORKDIR /app/backend
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    PATH="/app/backend/.venv/bin:$PATH"
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --frozen --no-dev

# --- Frontend build output ---
WORKDIR /app/frontend
COPY --from=frontend /app/.output ./.output

# --- Bake the model into the image so the container is fully self-contained/offline ---
ENV OLLAMA_HOST=0.0.0.0:11434
RUN ollama serve & \
    for i in $(seq 1 30); do ollama list >/dev/null 2>&1 && break; sleep 1; done && \
    ollama pull "${MODEL}"

# --- Runtime config: the backend talks to the in-container Ollama ---
ENV OPENAI_API_KEY=ollama \
    OPENAI_BASE_URL=http://localhost:11434/v1 \
    DEMO_OPENAI_MODEL=${MODEL} \
    DEMO_ENVIRONMENT=docker \
    DEMO_CORS_ORIGINS='["http://localhost:3000","http://127.0.0.1:3000"]' \
    DEMO_HOST=0.0.0.0 DEMO_PORT=8000 \
    NUXT_PUBLIC_API_BASE=http://localhost:8000 \
    NITRO_HOST=0.0.0.0 NITRO_PORT=3000 \
    NODE_ENV=production

COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 3000 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1
ENTRYPOINT ["/usr/local/bin/start.sh"]
