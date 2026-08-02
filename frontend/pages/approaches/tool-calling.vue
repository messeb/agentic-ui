<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#2</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <ApproachIntro
      type="Function / Tool calling"
      level="★★☆☆☆ — the model acts through tools"
      demonstrates="A function-calling loop over the chat-completions API, in the reason → act → observe → repeat shape the ReAct pattern popularized: the model calls a tool instead of answering, a dispatcher runs it, and the result is fed back until a final answer — with a human-in-the-loop gate before any side-effecting tool. How it shapes the UI: each call and its result is surfaced in a step-by-step timeline, and the tool results decide what's shown — the returned data is rendered directly and the model's answer is composed from it (the model doesn't pick UI components — that's #3)."
    />

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
      <ToolChatPanel ref="panel" class="min-w-0" />

      <aside class="min-w-0 space-y-4 text-sm">
        <WireInspector :frames="panel?.wire ?? []" />

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">The agent loop</h2>
          <ol class="mt-2 list-decimal space-y-1 pl-4 text-slate-600">
            <li>Model decides a <strong>tool call</strong> instead of prose.</li>
            <li>A dispatcher runs the handler; the result is fed back.</li>
            <li>The loop repeats (reason → act → observe) until a final answer.</li>
            <li><strong>Side-effect</strong> tools pause for your approval first.</li>
          </ol>
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Available tools</h2>
          <p class="mt-1 text-xs text-slate-500">
            The agent can only call these — <span class="text-amber-700">side-effect</span> ones need your
            approval before they run. Try “find flights…” then “book the cheapest for Alice”.
          </p>
          <ul class="mt-2 space-y-2">
            <li v-for="t in tools" :key="t.name">
              <div class="flex items-center gap-1.5">
                <code class="text-xs font-semibold">{{ t.name }}</code>
                <span
                  v-if="t.side_effect"
                  class="rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-800"
                >
                  side-effect
                </span>
              </div>
              <p class="text-xs text-slate-500">{{ t.description }}</p>
            </li>
          </ul>
          <p v-if="toolsError" class="mt-2 text-xs text-rose-600">{{ toolsError }}</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ToolChatPanel from '~/components/ToolChatPanel.vue'
import type { ToolCatalogEntry } from '~/types/tools'

const approach = useApproach('tool-calling')
const panel = ref<InstanceType<typeof ToolChatPanel> | null>(null)

const apiBase = useRuntimeConfig().public.apiBase
const tools = ref<ToolCatalogEntry[]>([])
const toolsError = ref('')

onMounted(async () => {
  try {
    const res = await fetch(`${apiBase}/api/tools`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    tools.value = (await res.json()).tools
  }
  catch (e) {
    toolsError.value = `Could not load tools — is the backend running? (${(e as Error).message})`
  }
})
</script>
