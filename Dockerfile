# syntax=docker/dockerfile:1
#
# One self-contained image on a SINGLE port: Nuxt frontend + FastAPI backend in one container (the
# Nuxt server proxies /api to the co-located backend). Talks to any OpenAI-compatible chat API
# (chat-API-agnostic) — configured at runtime, nothing baked in.
#
#   docker build -t agentic-ui-patterns .
#   docker run --rm -p 8080:8080 \
#     -e OPENAI_API_KEY=sk-... \
#     -e OPENAI_MODEL=gpt-4o-mini \
#     -e OPENAI_BASE_URL=<endpoint>   # optional; omit for OpenAI's default host
#     agentic-ui-patterns
#
#   → App http://localhost:8080  (API under http://localhost:8080/api, docs at /api/docs)

############################ 1. Build the Nuxt frontend → .output ############################
# Node 25 no longer bundles corepack, so install the pinned pnpm directly.
FROM node:25-slim AS frontend
RUN npm install -g pnpm@11.9.0
WORKDIR /app
# Copy the whole app before install: the `postinstall` (nuxt prepare) needs nuxt.config + source.
COPY frontend/ ./
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
RUN pnpm run build

############################ 2. Runtime: backend (uv) + frontend node server ############################
FROM python:3.14-slim AS runtime
# libatomic1: the Node 25 binary copied from the frontend stage links against libatomic.so.1.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates libatomic1 \
 && rm -rf /var/lib/apt/lists/*
# uv for the Python backend; the Node binary (no npm) to serve the Nuxt build.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=frontend /usr/local/bin/node /usr/local/bin/node

# --- Backend ---
WORKDIR /app/backend
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/backend/.venv/bin:$PATH"
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src ./src
RUN uv sync --frozen --no-dev

# --- Frontend build output ---
WORKDIR /app/frontend
COPY --from=frontend /app/.output ./.output

# --- Runtime config ---
# Single port 8080: the Nuxt server listens on 8080 and proxies /api to the backend on 8000
# (internal). The browser hits same-origin /api, so NUXT_PUBLIC_API_BASE is empty. LLM
# endpoint/key/model come from `docker run -e ...` (nothing baked in).
ENV DEMO_ENVIRONMENT=docker \
    DEMO_HOST=0.0.0.0 DEMO_PORT=8000 \
    NUXT_PUBLIC_API_BASE= \
    NITRO_HOST=0.0.0.0 NITRO_PORT=8080 \
    NODE_ENV=production

COPY docker/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8080/api/health || exit 1
ENTRYPOINT ["/usr/local/bin/start.sh"]
