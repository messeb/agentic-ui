<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#1</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <ApproachIntro
      type="Conversational chatbot / sidebar"
      level="★☆☆☆☆ — least agentic: the model only talks"
      demonstrates="Token-by-token SSE streaming of a Markdown answer through a key-hiding proxy backend. The AI produces text only — no app state and no actions; the user still does all the work."
    />

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
      <ChatPanel ref="panel" class="min-w-0" />

      <aside class="min-w-0 space-y-4 text-sm">
        <WireInspector :frames="panel?.wire ?? []" />

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">How this demo works</h2>
          <ol class="mt-2 list-decimal space-y-1 pl-4 text-slate-600">
            <li>The browser POSTs the conversation to the backend proxy.</li>
            <li>The proxy calls the model's chat API with the server-side key (never exposed here).</li>
            <li>Tokens stream back over <strong>SSE</strong> and render as Markdown live.</li>
          </ol>
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">What to expect</h2>
          <p class="mt-2 text-slate-600">
            Ask anything (try the suggested prompts). The answer streams in token-by-token as Markdown
            with syntax-highlighted code. This pattern only <strong>talks</strong> — it can't touch app
            state or take actions.
          </p>
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
import { ref } from 'vue'
import ChatPanel from '~/components/ChatPanel.vue'

const approach = useApproach('conversational-chatbot')
const panel = ref<InstanceType<typeof ChatPanel> | null>(null)
</script>
