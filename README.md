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
| 5 | **Server-streamed generative UI** | User prompt + component-returning tools | A component streamed at runtime | ★★★★☆ |
| 6 | **Intent-based adaptive UI** | Implicit telemetry (no chat) | Re-ranked / re-rendered layout | ★★★☆☆ |
| 7 | **Agentic frontend ("UI as toolbox")** | User goal + live app state | Stream of state-mutating tool calls | ★★★★★ |
| 8 | **Protocol-decoupled agent (AG-UI)** | Messages + tool/component descriptions | Typed protocol message stream | orthogonal |

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

### 5. Server-streamed generative UI (RSC / v0 style)

- **Input:** A user prompt plus a server-side tool set whose tools return UI components.
- **Output:** A **rendered component streamed at runtime** — serialized on the server and progressively rendered on the client.
- **How it works:** On the server, the model picks a tool that returns a component (often built on a design system); a streaming helper (e.g. `streamUI` on the Vercel AI SDK with React Server Components) serializes it and streams it to the client just like text. The component is typically ephemeral — discarded on navigation.
- **What you need:** A server-rendering framework (Next.js / RSC or equivalent), the Vercel AI SDK, server infrastructure, and a component set the tools can return.
- **Best for:** Historically, Next.js-native teams wanting deep RSC integration.
- **⚠️ Status:** Vercel has **officially paused AI SDK RSC development** and now steers new projects toward client-rendered tool-calling + structured output (#2/#3). Treat RSC as legacy, not a default.
- **Trade-offs:** ➕ Pre-written components streamed with no code-gen/sandbox step; strong type safety; good partial-render latency. ➖ Tightly coupled to Next.js/RSC (framework lock-in); complex mental model; now deprioritized upstream.

### 6. Intent-based adaptive UI (inference layer)

- **Input:** **Implicit user telemetry** — clicks, dwell time, mouse movement, usage history — not a chat message.
- **Output:** A **re-rendered or re-ranked interface**: which components appear, in what order, with which emphasis.
- **How it works:** An inference layer sits between interaction and render, scoring signals into an intent probability. "Intent hooks" then decide what to render (e.g. surface a data grid vs. an assistant; reorder listings by predicted booking probability; hide widgets irrelevant to the time of day or role).
- **What you need:** A telemetry pipeline, an inference model or scoring service, a state store for derived preferences, and component/layout variants to switch between. No conversational surface at all.
- **Best for:** Consumer apps optimizing engagement/conversion at scale (feeds, marketplaces); inappropriate for high-stakes, compliance-sensitive UIs where predictability beats optimization.
- **Trade-offs:** ➕ Zero extra user effort; anticipatory (prefetching, zero-UI, layout morphing); a controlled study reports gains in time-on-platform, CTR, satisfaction. ➖ Opaque ("why did it move?"); hard to make reversible/testable; **PII / GDPR-class consent and data-privacy exposure**. **Least production-mature of the eight** — reviews still cite model complexity and data quality as unsolved.

### 7. Agentic frontend ("UI as toolbox")

- **Input:** A user **goal** (typed or spoken) plus the **current app state**, injected into the prompt on every turn.
- **Output:** A **stream of tool calls** — each a state patch (e.g. fill a field, filter a table, navigate) carrying a `nextStep` directive — applied to the reactive store.
- **How it works:** The key insight is that *an LLM function call and a frontend state mutation are the same thing*, so every UI mutation is exposed as a callable tool. A generic dispatcher applies each call as a patch and re-renders. The system prompt is rebuilt from live state each request ("the prompt *is* the state"), acting as a state machine — no separate client-side conversation memory. Deterministic flow stays in the frontend; only interpretive decisions go to the model.
- **What you need:** A flat tool schema covering UI actions, a generic dispatcher, a reactive state layer (signals / Redux / Zustand), a prompt builder that serializes state, **prompt caching + state diffing** to control cost, **human-in-the-loop gates** (`useHumanInTheLoop`, LangGraph interrupt/breakpoint) before destructive actions, visible feedback per action, and **`aria-live` regions** so screen readers announce agent-driven changes. Frameworks: CopilotKit's "Agentic Frontend Stack" over AG-UI.
- **Best for:** Collaborative "co-pilot" workspaces (travel planning, portfolio allocation) where the agent acts inside a stateful app; in vendor-reported production use at Docusign, Cisco, S&P Global, Deutsche Telekom, Function Health (adoption only — no published performance data).
- **Trade-offs:** ➕ Most capable; unifies data and navigation logic; transport- and voice-agnostic. ➖ Costliest (full prompt rebuilt each turn); too slow for keystroke-level interactions; unsafe for regulated/high-stakes flows without explicit human confirmation; **prompt-injection exposure** — untrusted content and live app state enter the prompt every turn; largest blast radius, so scope tools tightly; accessibility must be built in deliberately.

### 8. Protocol-decoupled agents (MCP · MCP-UI · AG-UI)

Not a rung on the ladder but an **architectural layer under approaches 1–7** — open standards that solve the "M×N" glue problem (every agent framework needing custom wiring for every frontend). They are **complementary, not competing**:

| Protocol | Connects | Role |
|---|---|---|
| **MCP** (Model Context Protocol) | agent → **tools** | JSON-RPC access to external tools/resources/prompts (Anthropic, Nov 2024) |
| **MCP Apps / MCP-UI** | agent → **generative UI** | a tool returns a `ui://` HTML resource, rendered in a sandboxed iframe, `postMessage` back to the host |
| **AG-UI** | agent → **user interface** | event stream syncing agent activity to the UI |
| *(A2A / A2UI, Open-JSON-UI — adjacent/competing)* | agent ↔ agent / UI | still-settling standards |

- **Input / Output:** Messages + tool/component descriptions in → a **stream of typed protocol events** out. AG-UI defines **16 event types** across five groups (lifecycle, text message, tool call, state, special), incl. **`STATE_DELTA` (a JSON Patch / RFC 6902 array) and `STATE_SNAPSHOT` (full state)** for efficient bidirectional sync. Everything is a "Run" (all messages answering one question) grouped into threads; content splits into deltas for streaming.
- **What you need:** The protocol SDK (TS/Python), a framework adapter, a transport (SSE/WebSockets/binary), and usually a thin framework wrapper. MCP-UI ships `@mcp-ui/client` + `@mcp-ui/server` for "write once, render everywhere."
- **Best for:** Multi-framework/multi-vendor orgs avoiding lock-in; overkill for a single app that will never swap its agent backend.
- **Trade-offs:** ➕ True frontend/backend/vendor decoupling; streaming built in; inspectable in DevTools; broad adopter momentum (Google, AWS, Microsoft, Oracle, LangChain, Mastra). ➖ Young specs (MCP Apps launched Jan 2026) with maturing tooling/security practices; short-term fragmentation across competing UI specs.

---

## Engineering comparison

Qualitative ratings to weigh the operational cost of each approach. **Lower is cheaper/safer/easier** except where noted.

| # | Approach | Maturity | Build effort | Runtime cost | Latency | Determinism | Testability | Security exposure | Lock-in risk |
|---|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Conversational chatbot | Proven | Low | Low | Low | Med | High | Low | Low |
| 2 | Function / Tool Calling | Proven | Med | Med | Med | Low | Med | Med | Low |
| 3 | Component selection | Established | Med | Med | Med | Med | High | Low | Med |
| 4 | Sandboxed generated code | Emerging | High | Med | Med | Low | Low | **High** | Med |
| 5 | Server-streamed gen UI | **Paused** | High | High | Med | Low | Med | Med | **High** |
| 6 | Intent-based adaptive UI | Least mature | High | Med | Low | Low | Low | Med | Med |
| 7 | Agentic frontend | Emerging | High | **High** | High | Low | Med | Med–High | Med |
| 8 | Protocol-decoupled (AG-UI) | Emerging | Med | — | — | — | High | Low | **Low** |

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

A runnable scaffold with **all 8 approaches fully implemented** lives in [`demo/`](./demo/README.md) — Python/FastAPI (uv) + Vue/Nuxt, Docker, and CI, wiring the shared manifest → backend → frontend end-to-end: a streaming OpenAI chatbot (SSE); a tool-calling agent loop with a human-in-the-loop permission gate; Structured-Output component selection (combined with a real booking call); generative UI where model-written JS runs in a locked-down sandboxed iframe; server-streamed UI (a framework-native take on the RSC/`streamUI` pattern); an intent-based adaptive UI driven by implicit telemetry (no chat, no API key); an agentic "UI as toolbox" frontend where a goal drives a stateless dispatcher loop with a HITL booking gate; and a protocol-decoupled layer where the UI is a pure function of a typed AG-UI event stream (with `STATE_DELTA` JSON Patch and an MCP-UI `ui://` sandboxed-iframe resource).

```bash
cd demo && docker compose up --build   # frontend :3000 · backend :8000/docs
```
