# Backend — Agentic UI Demo

Standalone FastAPI service that exposes the 8 Agentic UI approaches. Every approach is a **stub**:
metadata is served, but the `.../demo` endpoint returns `501 Not Implemented` on purpose — this repo
is the *starting point*, not the implementation.

The approaches manifest is **vendored** at `src/agentic_ui_demo/data/approaches.json` (kept in sync
with `../shared/approaches.json` via `make sync-manifest` from the workspace root), so this app is
fully self-contained.

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

## Test / lint

```bash
uv run pytest --cov
uv run ruff check .
```

## Where to implement an approach

Replace the `NotImplemented` response in `src/agentic_ui_demo/routers/approaches.py::run_demo`
with real logic, and build the matching UI in `../frontend/pages/approaches/<id>.vue`.
Override the manifest path with `DEMO_APPROACHES_MANIFEST` if needed.
