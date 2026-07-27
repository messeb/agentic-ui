# Agentic UI — Approaches Overview

A practical map of the ways an AI/LLM can drive, generate, or adapt a user interface — from a chatbot that only *talks* to a frontend the agent fully *operates*.

Use it to pick the right approach for a feature and understand what each one costs to build and run.

> **Bottom line:** Match the approach to the interaction, not to the hype. Most products need only a chatbot (#1) or tool calling (#2); reach for generative or fully agentic approaches (#4–#7) only when the value clearly outweighs their cost, latency, and governance burden. These approaches **compose** — a real product usually stacks several (e.g. tool calling that also returns components), so this is a menu, not a single bet.

## The mental model

Every approach is a variation on one loop:

```
user input ──▶ [ AI reasoning ] ──▶ output that changes the UI ──▶ result fed back
```

What differs between approaches is **three things**:

- **Input** — what the AI receives (typed text, voice, or implicit telemetry) and how much app context comes with it.
- **Output** — what the AI produces (text, a structured action, a component choice, generated code, or a layout decision).
- **Authority** — how much the AI is allowed to *do* vs. merely *suggest*.

The list runs from least to most agentic. The higher entries let the AI talk; the lower ones let it act on and generate the interface itself.

## At a glance

| # | Approach | Input | Output | Agentic level |
|---|----------|-------|--------|:---:|
**They stack, they aren't exclusive.** Approaches build on each other: #3–#5 and #7 all rely on the tool/function-calling mechanism of #2, a chat surface (#1) can render selected components (#3), and #8 is a transport layer that can carry any of the others. Read the list as capabilities to combine, not options to choose between.

---

## The approaches in detail

Each card follows the same shape: **Input → Output → How it works → What you need → Best for → Trade-offs.**

### 1. Conversational chatbot / sidebar

- **Input:** User's natural-language message plus conversation history (optionally augmented with retrieved documents / RAG context).
- **Output:** A streamed natural-language answer, usually rendered as Markdown with code highlighting.
- **How it works:** The prompt is sent to the LLM; tokens stream back over SSE (Server-Sent Events) and are appended to the last message as they arrive. The UI renders Markdown incrementally and auto-scrolls while the user is at the bottom.
- **What you need:** An LLM API, a thin proxy backend to hide the API key, a streaming transport (SSE), and a Markdown/code renderer. No access to app state or actions.
- **Best for:** Q&A, help, search, drafting, explanation.
- **Trade-offs:** ➕ Simplest to build; familiar UX; streaming hides latency; low risk (the model only talks). ➖ Doesn't change how the app is used — the user still does all the work; no live data or actions.


## Engineering comparison

Qualitative ratings to weigh the operational cost of each approach. **Lower is cheaper/safer/easier** except where noted.

| # | Approach | Maturity | Build effort | Runtime cost | Latency | Determinism | Testability | Security exposure | Lock-in risk |
|---|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Conversational chatbot | Proven | Low | Low | Low | Med | High | Low | Low |
## Demo workspace

A runnable scaffold for all 8 approaches lives in [`demo/`](./demo/README.md) — Python/FastAPI (uv) + Vue/Nuxt, Docker, and CI. It wires the shared manifest → backend → frontend end-to-end, with every approach left as a clearly marked stub (the `/demo` endpoint returns `501` on purpose). It's a starting point to implement the approaches, not an implementation.

```bash
cd demo && docker compose up --build   # frontend :3000 · backend :8000/docs
```
