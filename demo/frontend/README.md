# Frontend — Agentic UI Demo

Standalone Nuxt 3 app (managed with **pnpm**) that lists the 8 Agentic UI approaches and links each
to a detail page with a stubbed "Run demo" button (which calls the backend and shows the intentional
`501`).

The approaches manifest is **vendored** at `shared/approaches.json` (kept in sync with
`../shared/approaches.json` via `make sync-manifest`), so this app is self-contained.

## Run (standalone)

```bash
corepack enable        # provides pnpm
pnpm install
pnpm dev               # http://localhost:3000
```

Point it at a non-default backend with:

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000 pnpm dev
```

## Structure

- `composables/useApproaches.ts` — reads the vendored manifest (`@shared/approaches.json`).
- `pages/index.vue` — the catalog.
- `pages/approaches/[id].vue` — per-approach detail + demo trigger. Implement an approach here.
- `types/approach.ts` — types mirroring the manifest.

> `pnpm-workspace.yaml` only carries the build allowlist (esbuild etc.) that pnpm 11 requires — this
> is a single-package app, not a monorepo.
