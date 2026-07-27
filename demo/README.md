# Agentic UI — Demo Workspace

A **best-in-class starting point** for building the [8 Agentic UI approaches](../README.md).
Everything is wired end-to-end — a shared manifest, a FastAPI backend, a Nuxt frontend, Docker,
and CI — but **no approach is implemented**. Each one is a clearly marked stub you fill in.

> Looking for the conceptual overview of the 8 approaches? See the [root README](../README.md).

### ✅ Implemented approaches (reference implementations)

Two of the eight are fully built; the rest remain stubs.

| # | Approach | Highlights | Route |
|---|----------|-----------|-------|
| 1 | Conversational chatbot | OpenAI streaming over SSE, incremental Markdown + code highlighting, smart auto-scroll | `/approaches/conversational-chatbot` |
| 2 | Function / Tool Calling | Agent loop (reason→act→observe), tool dispatcher, **human-in-the-loop permission** for side-effect tools, transparent step-by-step timeline | `/approaches/tool-calling` |

```bash
export OPENAI_API_KEY=sk-...     # global env; the backend proxies it, the frontend never sees it
make dev-backend                 # terminal 1
make dev-frontend                # terminal 2 → open http://localhost:3000
```

Without a key the backends return `503` and the panels show a clear message. Key files:
- #1 — `backend/…/routers/chat.py`, `frontend/composables/useChat.ts`, `frontend/components/ChatPanel.vue`
- #2 — `backend/…/routers/tools.py`, `backend/…/tools/flights.py`, `frontend/composables/useToolChat.ts`, `frontend/components/ToolChatPanel.vue`

## Two standalone apps

`backend/` and `frontend/` are **independent** — each builds, runs, tests, and containerizes on
its own (no shared build context, no monorepo tooling required). The manifest is the one thing they
share: it lives in `shared/approaches.json` (canonical) and is vendored into each app.

| Layer | Tech |
|-------|------|
| Backend | Python 3.12 · FastAPI · **uv** (standalone) · pytest · ruff |
| Frontend | **Vue 3 / Nuxt 3** · TypeScript · Tailwind · **pnpm** · ESLint |
| Contract | `shared/approaches.json` → vendored into each app via `make sync-manifest` |
| Ops | Docker (per-app) + docker-compose · Makefile · GitHub Actions CI |

## Architecture

```
        shared/approaches.json   ← canonical source of the 8 approaches
                 │  make sync-manifest (copies into each app)
        ┌────────┴─────────┐
        ▼                  ▼
 backend/…/data/     frontend/shared/
 approaches.json     approaches.json
        │                  │
   FastAPI backend    Nuxt frontend
   /api/approaches    catalog + detail pages
   /api/.../demo→501  "Run demo" → calls backend → shows 501
       (stub)                 (stub)
```

The `/demo` endpoint and each detail page are the two places you implement an approach.
The `501 Not Implemented` response is intentional and asserted by the test suite.

## Quickstart

### Option A — local

```bash
# from demo/
make setup                    # syncs manifest, installs backend (uv) + frontend (pnpm)

# two terminals:
make dev-backend              # http://localhost:8000/docs
make dev-frontend             # http://localhost:3000
```

Or per app, standalone:

```bash
cd backend  && uv sync && uv run agentic-ui-demo          # backend only
cd frontend && corepack enable && pnpm install && pnpm dev # frontend only
```

### Option B — Docker

```bash
# from demo/
docker compose up --build
# Frontend http://localhost:3000 · Backend http://localhost:8000/docs
```

## Common tasks

```bash
make help            # list all targets
make check           # manifest-sync + lint + test (what CI runs)
make sync-manifest   # re-vendor shared/approaches.json into both apps
make test            # backend tests with coverage
```

## Layout

```
demo/
├── shared/approaches.json                       # ← canonical contract (edit here first)
├── backend/                                      # standalone FastAPI app (uv)
│   ├── pyproject.toml · uv.lock · Dockerfile
│   └── src/agentic_ui_demo/
│       ├── main.py                               # app factory
│       ├── registry.py                           # loads the vendored manifest
│       ├── data/approaches.json                  # ← vendored copy (make sync-manifest)
│       └── routers/approaches.py                 # ← implement run_demo() per approach
├── frontend/                                     # standalone Nuxt app (pnpm)
│   ├── package.json · pnpm-lock.yaml · Dockerfile
│   ├── shared/approaches.json                    # ← vendored copy (make sync-manifest)
│   └── pages/approaches/[id].vue                 # ← implement the UI per approach
├── docker-compose.yml
└── Makefile
```

## How to implement an approach (the intended workflow)

1. Edit `shared/approaches.json`, set the approach `status` to `in-progress`, run `make sync-manifest`.
2. Backend: replace the `501` branch in `routers/approaches.py::run_demo` with real logic
   (stream tokens, dispatch tool calls, return component descriptors, …). Keep model/API keys
   server-side.
3. Frontend: build the interaction in `pages/approaches/[id].vue`.
4. Add tests; flip `status` to `implemented`.

Each approach is isolated — implement them in any order, one at a time.
