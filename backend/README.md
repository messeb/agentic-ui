# Backend — Agentic UI Patterns

Standalone FastAPI service exposing the 8 Agentic UI approaches. **All eight are implemented** — each
has its own router under `src/agentic_ui_demo/routers/` (`chat.py`, `tools.py`, `components.py`,
`generative.py`, `rsc.py`, `adaptive.py`, `agent.py`, `protocol.py`). A generic
`routers/approaches.py::run_demo` returns `501` and stays only as a scaffold for adding a 9th.

The approaches manifest lives at `src/agentic_ui_demo/data/approaches.json`, so this app is fully
self-contained.

## Run (standalone)

```bash
uv sync
uv run agentic-ui-demo
# or
uv run uvicorn agentic_ui_demo.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health
- Approaches: http://localhost:8000/api/approaches

## Configuration (chat-API-agnostic)

The backend speaks the OpenAI chat-completions API to whatever endpoint you point it at — OpenAI,
Azure OpenAI's v1 endpoint, or a local server (Ollama / vLLM / LM Studio). Three `OPENAI_*` vars:

| Variable | Meaning |
|---|---|
| `OPENAI_API_KEY` | the API key (model approaches return `503` without it; #6 needs none) |
| `OPENAI_MODEL` | the model / deployment name — default `gpt-4o-mini` |
| `OPENAI_BASE_URL` | the endpoint (optional; omit for OpenAI's default host) |

## Test / lint

```bash
uv run pytest --cov
uv run ruff check .
```

## Adding a 9th approach

Copy an existing router (not the `501` scaffold) — e.g. `routers/tools.py` — register it in
`main.py`, and build the matching UI in `../frontend/pages/approaches/<id>.vue`. Keep API keys
server-side. Override the manifest path with `DEMO_APPROACHES_MANIFEST` if needed.
