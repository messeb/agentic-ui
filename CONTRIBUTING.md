# Contributing

Thanks for your interest! This repo is a **scaffold** for the 8 Agentic UI approaches. The demo
workspace lives in [`demo/`](./demo/README.md).

## Getting started

The workspace has two **standalone** apps — `demo/backend` (uv) and `demo/frontend` (pnpm):

```bash
cd demo
make setup        # syncs the manifest, installs backend (uv) + frontend (pnpm)
```

Run the stack with `make dev-backend` + `make dev-frontend`, or `docker compose up --build`.

## Before you open a PR

Run the same checks CI runs:

```bash
cd demo
make check        # manifest-sync + ruff + pytest + (frontend) eslint/typecheck
```

- `demo/shared/approaches.json` is the canonical contract. It is vendored into each app
  (`backend/src/agentic_ui_demo/data/` and `frontend/shared/`). After editing it, run
  `make sync-manifest`. If you change the contract's shape, update the types in
  `frontend/types/approach.ts` and the Pydantic models in `backend/.../models.py`.
- **Never put API keys in the frontend.** The backend proxies all model calls.
- Conventional Commits are appreciated (`feat:`, `fix:`, `docs:`, `chore:`).

## Implementing an approach

Open an "Implement an approach" issue, then:

1. Set the approach `status` to `in-progress` in the manifest.
2. Implement the backend `run_demo` handler and the frontend detail page.
3. Add tests. Flip `status` to `implemented`.

One approach per PR, please — it keeps reviews focused.

## Code style

- Python: `ruff` (lint + format), type hints, small focused modules.
- Vue/TS: `eslint` (Nuxt config), `<script setup lang="ts">`, typed props.
