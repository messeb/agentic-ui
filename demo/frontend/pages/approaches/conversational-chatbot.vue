<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#1</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
      <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
        ● Live demo
      </span>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
      <ChatPanel class="min-w-0" />

      <aside class="space-y-4 text-sm">
        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">How this demo works</h2>
          <ol class="mt-2 list-decimal space-y-1 pl-4 text-slate-600">
            <li>The browser POSTs the conversation to the backend proxy.</li>
            <li>The proxy calls OpenAI with your key (never exposed here).</li>
            <li>Tokens stream back over <strong>SSE</strong> and render as Markdown live.</li>
          </ol>
        </div>

        <div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900">
          <h2 class="text-xs font-semibold uppercase tracking-wide">Setup</h2>
          <p class="mt-2">Export your key and start the backend:</p>
          <pre class="mt-2 overflow-x-auto rounded bg-amber-100 p-2 text-xs">export OPENAI_API_KEY=sk-...
make dev-backend</pre>
          <p class="mt-2 text-xs">Without a key the backend returns <code>503</code> and the panel shows it.</p>
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Implemented in</h2>
          <ul class="mt-2 space-y-1 text-slate-600">
            <li><code>backend/…/routers/chat.py</code></li>
            <li><code>frontend/composables/useChat.ts</code></li>
            <li><code>frontend/components/ChatPanel.vue</code></li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
const approach = useApproach('conversational-chatbot')
</script>
