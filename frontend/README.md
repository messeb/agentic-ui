# Frontend — Agentic UI Patterns

Standalone Nuxt 3 app (managed with **pnpm**) that lists the 8 Agentic UI approaches and gives each a
**dedicated, fully-implemented detail page** at `pages/approaches/<id>.vue`. A catch-all
`pages/approaches/[id].vue` remains as a scaffold — it renders the backend's intentional `501` only for
an approach id that has no dedicated page yet.

The approaches manifest lives at `shared/approaches.json` (imported via the `@shared` alias), so this
app is self-contained.

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

The frontend **never sees the model API key** — all model calls go through the backend proxy.

## Structure

- `composables/useApproaches.ts` — reads the vendored manifest (`@shared/approaches.json`).
- `composables/use*.ts` — one composable per approach (`useChat`, `useToolChat`, `useAdaptive`, …).
- `pages/index.vue` — the catalog / evolution narrative.
- `pages/approaches/<id>.vue` — the per-approach demo pages (one each).
- `pages/approaches/[id].vue` — catch-all scaffold (unimplemented ids → `501`).
- `components/` — per-approach panels + the `catalog/` component library used by #3.
- `types/approach.ts` — types mirroring the manifest.

> `pnpm-workspace.yaml` only carries the build allowlist (esbuild etc.) that pnpm 11 requires — this
> is a single-package app, not a monorepo.
