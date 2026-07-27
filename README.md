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
| 1 | **Conversational chatbot / sidebar** | User text | Streamed text (Markdown) | ★☆☆☆☆ |
| 2 | **Function / Tool Calling** | User text + tool schemas | Structured function call(s) → executed | ★★☆☆☆ |
| 3 | **Component selection from a catalog** | User text + component catalog | JSON choosing component(s) + their data | ★★★☆☆ |
| 4 | **Generative UI via sandboxed code** | User request + runtime function list | Generated code (run in a sandbox) | ★★★★☆ |
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

### 2. Function / Tool Calling

- **Input:** User intent in natural language plus a set of **tool definitions** (name, description, and a JSON-Schema for arguments).
- **Output:** A structured **tool call** — the function name and validated arguments — which your code executes; the result is fed back to the model, which then answers.
- **How it works:** The model decides a tool is needed and emits a call instead of prose. A dispatcher runs the matching handler, appends the result to the context window, and the loop repeats (the ReAct pattern: reason → act → observe → repeat) until the model produces a final answer. Tools can run **server-side** (privileged, DB/API) or **frontend** (in the browser — read component state, call browser APIs, mutate the UI directly).
- **What you need:** Tool schemas (OpenAI function calling / Anthropic tool-use / AI SDK `tool()`), a dispatcher (name → handler map), an **agent-loop runner** that re-invokes the model with each tool result until it returns a final answer, a backend for privileged actions and key hiding, and access to the data/state the tools touch. Optionally an orchestration framework (LangChain/LangGraph) and persistent memory. A **permission layer** before side effects run — never blindly execute a model-chosen action. This is the **foundational primitive nearly every richer approach builds on.**
- **Best for:** Fetching real-time data, calling APIs, performing discrete actions ("book this", "search flights").
- **Trade-offs:** ➕ Connects the LLM to real data and actions; supports multi-step reasoning; framework-agnostic. ➖ Non-deterministic; the right tool granularity is hard (too fine = many chained calls, too coarse = inflexible); cost and latency per round-trip.

### 3. Component selection from a catalog

- **Input:** User intent plus a **catalog of pre-built UI components**, each described with a name, a purpose, and an input schema.
- **Output:** A **Structured Output** JSON document naming one or more components and supplying their prop values (e.g. under a `$props` key).
- **How it works:** Structured Output constrains the model to emit JSON that matches your schema. A renderer reads that JSON and instantiates the real, hand-built components with the model-supplied data. A "smart wrapper" around each "dumb" presentational component handles events, state, and navigation.
- **What you need:** A component library, schema descriptions per component, a model that supports Structured Output (`generateObject`/`streamObject`, CopilotKit `useCopilotAction` + `render`), and a dynamic renderer. Weaker models need few-shot examples to infer inputs correctly; some models can't combine Structured Output with Tool Calling (needs an emulation workaround).
- **Best for:** Rich, interactive answers — cards, forms, charts, product tiles — instead of plain prose.
- **Trade-offs:** ➕ Interactive and on-brand; components stay hand-built and testable in isolation. ➖ Limited to a fixed catalog; input inference is unreliable on cheap models.

### 4. Generative UI via sandboxed code

- **Input:** A user request plus a list of **runtime functions** the generated code may call (each a data source or a sink, with described argument/return schemas).
- **Output:** **Generated code** (typically JavaScript) plus a status and a user-facing message, returned as a structured object.
- **How it works:** Because models compute unreliably but *describe* computation well, the model emits code (or full React/HTML/JS) rather than doing the math. It runs in an **isolated runtime with no access to the app** — an iframe sandbox, WebContainer, or cloud VM (E2B, ~400–600ms cold start) — calling only whitelisted functions (e.g. `loadFlights`, `generateChart`). Products: **v0** (React + Tailwind + shadcn/ui), **Claude Artifacts / MCP Apps** (server HTML in a sandboxed iframe, `postMessage` back to host).
- **What you need:** A sandboxed runtime, a whitelist of callable functions with schemas plus a **host↔sandbox `postMessage` bridge** so sandboxed code can invoke them, a build/transpile step (JSX/TS → runnable), and a **strict security contract** — CSP, `allow-scripts` *without* `allow-same-origin`, no top-navigation; treat all generated code as an active attack vector. Guardrail prompting ("never use external resources", "always return via the runtime").
- **Best for:** No/low-code builders, rapid prototyping, and open-ended charts no fixed component covers.
- **Trade-offs:** ➕ Maximum flexibility — genuinely novel UI for unanticipated problems. ➖ Highest latency (generate + build/execute) and largest security surface; non-deterministic; hardest to test.


## Engineering comparison

Qualitative ratings to weigh the operational cost of each approach. **Lower is cheaper/safer/easier** except where noted.

| # | Approach | Maturity | Build effort | Runtime cost | Latency | Determinism | Testability | Security exposure | Lock-in risk |
|---|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Conversational chatbot | Proven | Low | Low | Low | Med | High | Low | Low |
| 2 | Function / Tool Calling | Proven | Med | Med | Med | Low | Med | Med | Low |
| 3 | Component selection | Established | Med | Med | Med | Med | High | Low | Med |
| 4 | Sandboxed generated code | Emerging | High | Med | Med | Low | Low | **High** | Med |
> **Maturity** signals build risk: *Proven* = widely in production; *Established* = solid tooling, growing adoption; *Emerging* = promising but young, expect churn; *Paused* = upstream has deprioritized it (RSC); *Least mature* = active research, thin production track record. **Determinism** = *output-UI* determinism ("High" is good): tool calling can be schema-valid yet still pick different tools/args, so it rates Low. **Lock-in, runtime cost, and security** columns are author synthesis (not in the source) — treat as directional. Row 8 inherits the runtime characteristics of whichever approach it wraps.

**Build vs. buy & team readiness.** Most approaches are buy-first — adopt CopilotKit / Vercel AI SDK / an AG-UI SDK rather than hand-rolling the loop and protocol. Skill demands differ sharply: #4 needs security engineering (sandboxing), #5 deep Next.js/RSC, #6 ML/data engineering, #7 disciplined prompt/state engineering. Staff to the approach, not to the demo.

## Cross-cutting concerns

These apply to every approach beyond a plain chatbot and should be designed in from the start:

- **Transparency** — show what the agent did and why (surface tool calls in plain language, not raw function names).
- **Reversibility & control** — undo, human confirmation for consequential actions, and a kill switch; keep humans accountable for outcomes.
- **Governance** — define what the agent may do autonomously vs. what needs approval; log model/prompt/tool versions, decisions, and cost budgets for audit; protocols like MCP Apps force explicit capability declaration (`ui.components`, `ui.hooks`).
- **Security** — treat model output and any injected content as untrusted: gate tool execution behind a permission layer, sandbox generated code, and defend against **prompt injection** (untrusted text or app state steering the model). Human-in-the-loop (HITL) approval before consequential side effects.
- **Accessibility** — dynamic, AI-driven changes are silent to assistive tech unless announced via `aria-live`; this is a hard requirement, not a nicety.
- **Cost & latency** — token generation costs more than rendering markup and adds delay; mitigate with cheap-model proxies, streaming/optimistic UI, and prompt caching.

## Production signals & 2026 outlook

- **Proven in production:** tool calling + component rendering. Shopify **Sidekick** (Claude) chains many tool calls per turn with an **LLM-as-judge** eval harness to fight "tool confusion" as the catalog grows. *Separately*, Shopify **Flow**'s fine-tuned Qwen3-32B tool-calling agent hit **2.2× faster / 68% cheaper** — a different product, not Sidekick.
- **Standards still settling:** MCP (tools) + AG-UI (UI) + MCP Apps/MCP-UI (portable sandboxed UI) are converging into a layered stack, but competing UI specs (A2UI, Open-JSON-UI) mean short-term churn. Open questions: reusable non-re-rendering views, letting a model "fill a UI like a human," and whether HTML suffices for mobile-native.

## Choosing an approach

1. **Start at the top of the list and stop as soon as the value is delivered.** Move down only when the added capability justifies the extra cost, latency, non-determinism, and governance burden.
2. **Keep deterministic flow in the frontend.** Hand the AI only decisions that genuinely require interpreting user intent; hard rules belong in code, not in a prompt.
3. **Match the approach to the interaction.** Q&A → #1; live data/actions → #2; rich answers → #3; open-ended computation → #4; adaptive personalization → #6; full task automation → #7.
4. **Treat protocols (#8) as orthogonal** — layer MCP/AG-UI/MCP-UI under any approach when independence from a specific backend or model matters.
5. **Never put autonomy on high-stakes or latency-critical paths** (payments, medical, legal, keystroke-level editing) without explicit human confirmation.

## Demo workspace

A runnable scaffold for all 8 approaches lives in [`demo/`](./demo/README.md) — Python/FastAPI (uv) + Vue/Nuxt, Docker, and CI. It wires the shared manifest → backend → frontend end-to-end. **Approaches #1–#4 are fully implemented** as references — a streaming OpenAI chatbot (SSE), a tool-calling agent loop with a human-in-the-loop permission gate, Structured-Output component selection (combined with a real booking call), and generative UI where model-written JS runs in a locked-down sandboxed iframe; the other four are clearly marked stubs (their `/demo` endpoint returns `501` on purpose).

```bash
cd demo && docker compose up --build   # frontend :3000 · backend :8000/docs
```
