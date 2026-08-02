# Contributing

Thanks for your interest! This repo is a **reference implementation** of the 8 Agentic UI
approaches (all fully built). See the [README](./README.md#running-the-demo) for the full dev guide.

## Getting started

The repo has two **standalone** apps — `backend/` (uv) and `frontend/` (pnpm). All commands run
**from the repo root**:

```bash
make setup        # installs backend (uv) + frontend (pnpm)
```

Run the stack with `make dev-backend` + `make dev-frontend`, or `make docker` (single-image build).

## Before you open a PR

Run the same checks CI runs:

```bash
make check        # ruff + pytest + (frontend) eslint/typecheck
```

- The approaches manifest lives in each app: `backend/src/agentic_ui_demo/data/approaches.json`
  and `frontend/shared/approaches.json`. If you change the contract's shape, update **both** copies,
  the types in `frontend/types/approach.ts`, and the Pydantic models in `backend/.../models.py`.
- **Never put API keys in the frontend.** The backend proxies all model calls.
- Conventional Commits are appreciated (`feat:`, `fix:`, `docs:`, `chore:`).

## Implementing an approach

Open an "Implement an approach" issue, then:

1. Set the approach `status` to `in-progress` in the manifest.
2. Add a dedicated backend router (`backend/…/routers/<id>.py`) and a frontend page
   (`frontend/pages/approaches/<id>.vue`).
3. Add tests. Flip `status` to `implemented`.

One approach per PR, please — it keeps reviews focused.

## Code style

- Python: `ruff` (lint + format), type hints, small focused modules.
- Vue/TS: `eslint` (Nuxt config), `<script setup lang="ts">`, typed props.
