# syntax=docker/dockerfile:1
# Standalone: build from this directory.
#   docker build -t agentic-ui-demo-backend .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    DEMO_RELOAD=false \
    DEMO_HOST=0.0.0.0 \
    DEMO_PORT=8000 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependency layer (cached until pyproject/lock changes).
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Application source (includes the vendored manifest under src/.../data/).
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

# Run as non-root.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/health').status==200 else 1)"

CMD ["uvicorn", "agentic_ui_demo.main:app", "--host", "0.0.0.0", "--port", "8000"]
