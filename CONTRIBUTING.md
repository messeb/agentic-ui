# Contributing

Thanks for your interest! This repo is a **reference implementation** of the 8 Agentic UI
approaches (all fully built). See [`DEVELOPMENT.md`](./DEVELOPMENT.md) for the full dev guide.

## Getting started

The repo has two **standalone** apps — `backend/` (uv) and `frontend/` (pnpm). All commands run
**from the repo root**:

```bash
make setup        # syncs the manifest, installs backend (uv) + frontend (pnpm)
```

Run the stack with `make dev-backend` + `make dev-frontend`, or `docker compose up --build`.

## Before you open a PR

Run the same checks CI runs:

```bash
make check        # manifest-sync + ruff + pytest + (frontend) eslint/typecheck
```

- `shared/approaches.json` is the canonical contract. It is vendored into each app
  (`backend/src/agentic_ui_demo/data/` and `frontend/shared/`). After editing it, run
  `make sync-manifest`. If you change the contract's shape, update the types in
  `frontend/types/approach.ts` and the Pydantic models in `backend/.../models.py`.
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
