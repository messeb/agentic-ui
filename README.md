# Agentic UI — Approaches Overview

## Demo workspace

A runnable scaffold for all 8 approaches lives in [`demo/`](./demo/README.md) — Python/FastAPI (uv) + Vue/Nuxt, Docker, and CI. It wires the shared manifest → backend → frontend end-to-end, with every approach left as a clearly marked stub (the `/demo` endpoint returns `501` on purpose). It's a starting point to implement the approaches, not an implementation.

```bash
cd demo && docker compose up --build   # frontend :3000 · backend :8000/docs
```
