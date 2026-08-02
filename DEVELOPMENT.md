# Agentic UI — Development Guide

A **best-in-class reference implementation** of the [8 Agentic UI approaches](./README.md).
Everything is wired end-to-end — a shared manifest, a FastAPI backend, a Nuxt frontend, Docker,
and CI — and **all eight approaches are fully implemented**, each with its own backend router and
frontend page. (A generic scaffold endpoint remains as a template for adding a 9th — see
[Adding a new approach](#adding-a-new-approach).)

> Looking for the conceptual overview of the 8 approaches? See the [root README](./README.md).
> All commands below run **from the repository root**.

### ✅ Implemented approaches (reference implementations)

**All eight approaches are fully built.**

| # | Approach | Highlights | Route |
|---|----------|-----------|-------|
| 1 | Conversational chatbot | OpenAI streaming over SSE, incremental Markdown + code highlighting, smart auto-scroll | `/approaches/conversational-chatbot` |
| 2 | Function / Tool Calling | Agent loop (reason→act→observe), tool dispatcher, **human-in-the-loop permission** for side-effect tools, transparent step-by-step timeline | `/approaches/tool-calling` |
| 3 | Component selection | **Structured Output** picks components from a catalog (flight results, status, ancillary offers, booking request); a renderer instantiates hand-built Vue components. **Combined with a real booking call** (#2's shared flight state): select a flight → enter passenger → book; adding ancillaries are real backend calls folded into the booking total | `/approaches/component-selection` |
| 4 | Generative UI (sandboxed code) | The model **generates JavaScript** (Structured Output) that renders **arbitrary UI** — table, chart, cards, whatever fits — directly into a **locked-down iframe** (`allow-scripts` without `allow-same-origin`, CSP `connect-src 'none'`, no external resources). Data comes only via a `postMessage`→`loadFlights` bridge; isolation makes free-form rendering safe. Backend never executes the code | `/approaches/sandboxed-code` |
| 5 | Server-streamed UI (RSC/v0) | The model composes a page from **server-side render tools**; the **server renders** each component to a **real HTML fragment** and **streams the fragments** over SSE; the client just mounts them progressively. The component set is **web components** (`<flight-card>` custom elements) — framework-agnostic, unlike #3's Vue-only components. *Framework-native equivalent of RSC `streamUI` — which Vercel has paused* | `/approaches/server-streamed-ui` |
| 6 | Intent-based adaptive UI | **No chat.** Implicit telemetry (hover dwell, clicks, sort taps) → a deterministic **inference layer** scores intent (price / time / urgency / explore) → the UI **re-ranks flights and emphasizes/hides widgets**. Transparent rationale shown to counter opacity; needs no API key | `/approaches/intent-adaptive` |
| 7 | Agentic frontend ("UI as toolbox") | A **goal** drives the whole app: every UI mutation is a flat tool; a **generic dispatcher** applies each call as a **state patch**; the **stateless** backend rebuilds the prompt from live state each turn; filtering stays deterministic in the frontend; **`book` is HITL-gated**; every action gets visible highlight + **`aria-live`** | `/approaches/agentic-frontend` |
| 8 | Protocol-decoupled (MCP · MCP-UI · AG-UI) | The UI is a **pure function of a typed AG-UI event stream** (lifecycle / text / tool-call / state). State syncs via **`STATE_SNAPSHOT` + `STATE_DELTA`** (RFC-6902 JSON Patch); a tool result can carry an **MCP-UI `ui://`** HTML resource rendered in a sandboxed iframe that `postMessage`s intents back. Includes a live event inspector | `/approaches/protocol-decoupled` |

```bash
export OPENAI_API_KEY=sk-...     # global env; the backend proxies it, the frontend never sees it
make dev-backend                 # terminal 1
make dev-frontend                # terminal 2 → open http://localhost:3000
```

Without a key the backends return `503` and the panels show a clear message. Key files:
- #1 — `backend/…/routers/chat.py`, `frontend/composables/useChat.ts`, `frontend/components/ChatPanel.vue`
- #2 — `backend/…/routers/tools.py`, `backend/…/tools/flights.py`, `frontend/composables/useToolChat.ts`, `frontend/components/ToolChatPanel.vue`
- #3 — `backend/…/routers/components.py`, `frontend/components/catalog/*.vue`, `frontend/components/CatalogRenderer.vue`, `frontend/composables/useComponentChat.ts`
- #4 — `backend/…/routers/generative.py`, `frontend/components/SandboxRunner.vue` (the sandbox), `frontend/composables/useGenerativeUi.ts`
- #5 — `backend/…/routers/rsc.py` (HTML fragments), `frontend/components/RscHtmlStream.vue` (progressive mount), `frontend/plugins/webcomponents.client.ts` (`<flight-card>`), `frontend/composables/useRscStream.ts`
- #6 — `backend/…/routers/adaptive.py` (scoring layer), `frontend/composables/useAdaptive.ts`, `frontend/components/IntentPanel.vue` + `AdaptiveFlightCard.vue` + `AdaptiveWidget.vue`
- #7 — `backend/…/routers/agent.py` (stateless step), `frontend/composables/useAgentApp.ts` (store + dispatcher + loop), `frontend/components/Agent*.vue`
- #8 — `backend/…/routers/protocol.py` (AG-UI event stream), `frontend/composables/useProtocol.ts` (client + JSON Patch), `frontend/components/McpUiFrame.vue` + `ProtocolInspector.vue`

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
   per-approach       one dedicated page per approach
   routers (8)        (pages/approaches/<id>.vue)
```

Each approach owns a **dedicated backend router** (`routers/chat.py`, `tools.py`, `rsc.py`, …) and a
**dedicated frontend page** (`pages/approaches/<id>.vue`) — see the [Key files](#-implemented-approaches-reference-implementations)
list above. A generic `/api/approaches/{id}/demo` endpoint and a catch-all `pages/approaches/[id].vue`
remain as a **scaffold template**: they return `501 Not Implemented` and are only reached for an
approach id that has no dedicated page yet (handy for adding a 9th).

## Quickstart

### Option A — local

```bash
# from the repo root
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

The backend is **chat-API-agnostic** — it speaks the OpenAI chat-completions API to whatever
endpoint you point it at. Three variables, all `OPENAI_*`:

| Variable | Meaning |
|---|---|
| `OPENAI_API_KEY` | the API key |
| `OPENAI_MODEL` | the model (or deployment) name — default `gpt-4o-mini` |
| `OPENAI_BASE_URL` | the endpoint (optional; omit for OpenAI's default host) |

Point `OPENAI_BASE_URL` at anything that speaks the OpenAI chat API — OpenAI, **Azure OpenAI's
OpenAI-compatible v1 endpoint**, or a local server (Ollama, vLLM, LM Studio).

### Option B — Docker Compose (two services)

```bash
# from the repo root — set the key in your shell or a .env file next to the compose
OPENAI_API_KEY=sk-...  docker compose up --build
# Frontend http://localhost:3000 · Backend http://localhost:8000/docs
```

Compose passes `OPENAI_API_KEY` / `OPENAI_MODEL` / `OPENAI_BASE_URL` through to the backend. Best for
local development (separate, restartable services). Without a key the model approaches return `503`.

### Option C — single self-contained image on ONE port (deploy on its own)

The root `Dockerfile` builds **one image** with the FastAPI backend + Nuxt frontend on a **single
port (8080)** — the Nuxt server serves the UI and proxies `/api` to the co-located backend
(`docker/start.sh` runs both; if either exits, the container stops so your orchestrator restarts it).
Small (no model baked in), talks to whatever OpenAI-compatible endpoint you configure at run time.

```bash
docker build -t agentic-ui-patterns .
docker run --rm -p 8080:8080 \
  -e OPENAI_API_KEY=sk-... \
  -e OPENAI_MODEL=gpt-4o-mini \
  agentic-ui-patterns
# → http://localhost:8080   (API at /api, docs at /api/docs)
# add -e OPENAI_BASE_URL=<endpoint> to target Azure's v1 endpoint, a local server, etc.
```

> Prefer a fully offline image with the model baked in? Point `OPENAI_BASE_URL` at a local
> OpenAI-compatible server, or bundle one — earlier revisions embedded Ollama + a small model
> (see git history).

## Common tasks

```bash
make help            # list all targets
make check           # manifest-sync + lint + test (what CI runs)
make sync-manifest   # re-vendor shared/approaches.json into both apps
make test            # backend tests with coverage
```

## Layout

```
. (repo root)
├── README.md                                    # conceptual overview of the 8 approaches
├── DEVELOPMENT.md                               # this file
├── sources/                                     # source articles (git-ignored)
├── shared/approaches.json                       # ← canonical contract (edit here first)
├── backend/                                      # standalone FastAPI app (uv)
│   ├── pyproject.toml · uv.lock · Dockerfile
│   └── src/agentic_ui_demo/
│       ├── main.py                               # app factory (registers all routers)
│       ├── registry.py                           # loads the vendored manifest
│       ├── data/approaches.json                  # ← vendored copy (make sync-manifest)
│       └── routers/                              # one router per approach + approaches.py (scaffold)
├── frontend/                                     # standalone Nuxt app (pnpm)
│   ├── package.json · pnpm-lock.yaml · Dockerfile
│   ├── shared/approaches.json                    # ← vendored copy (make sync-manifest)
│   ├── pages/approaches/<id>.vue                 # one dedicated page per approach
│   └── pages/approaches/[id].vue                 # catch-all scaffold (unimplemented ids → 501)
├── docker-compose.yml
└── Makefile
```

## Adding a new approach

All eight approaches are implemented; to add a **9th**, follow the same pattern the existing ones use:

1. Edit `shared/approaches.json` (add the entry, `status: "in-progress"`), run `make sync-manifest`.
2. Backend: add a dedicated `routers/<id>.py` and register it in `main.py` (stream tokens, dispatch
   tool calls, return component descriptors, …). Keep model/API keys server-side. The generic
   `routers/approaches.py::run_demo` (returns `501`) is the template to copy from.
3. Frontend: add a dedicated `pages/approaches/<id>.vue`. Until it exists, the catch-all
   `pages/approaches/[id].vue` shows the `501` scaffold response.
4. Add tests; flip `status` to `implemented`.

Each approach is isolated — they were built in any order, one at a time.
