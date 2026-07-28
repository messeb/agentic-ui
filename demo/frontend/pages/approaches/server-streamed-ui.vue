<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#5</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
      <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
        ● Live demo
      </span>
      <span class="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-800">
        paused upstream
      </span>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
      <div class="min-w-0 space-y-4">
        <div class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-900">
          ⚠️ Vercel has <strong>paused AI SDK RSC</strong> development. The real pattern needs
          Next.js + React Server Components + <code>streamUI</code>. This is a
          <strong>framework-native equivalent</strong>: the server picks a component (tool call),
          serializes it, and streams it node-by-node; the client renders each node progressively.
        </div>

        <form class="flex gap-2" @submit.prevent="submit(prompt)">
          <input
            v-model="prompt"
            type="text"
            placeholder="e.g. Flights from Graz to Hamburg"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            :disabled="streaming"
          >
          <button
            type="submit"
            class="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
            :disabled="streaming || !prompt.trim()"
          >
            {{ streaming ? 'Streaming…' : 'Render' }}
          </button>
        </form>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="s in suggestions"
            :key="s"
            class="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
            :disabled="streaming"
            @click="submit(s)"
          >
            {{ s }}
          </button>
        </div>

        <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>

        <div v-if="tools.length" class="flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
          <span>Server composed via</span>
          <code
            v-for="(t, i) in tools"
            :key="i"
            class="rounded bg-slate-100 px-1.5 py-0.5 font-semibold text-slate-700"
          >{{ t.name }}<span v-if="argsText(t)" class="font-normal text-slate-500">({{ argsText(t) }})</span></code>
        </div>

        <div v-if="nodes.length || streaming" class="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <RscRenderer :nodes="nodes" />
          <p v-if="streaming" class="mt-2 flex items-center gap-1 text-xs text-slate-400">
            <span class="h-2 w-2 animate-pulse rounded-full bg-amber-400" /> streaming from server…
          </p>
        </div>
      </div>

      <aside class="space-y-4 text-sm">
        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">How this works</h2>
          <ol class="mt-2 list-decimal space-y-1 pl-4 text-slate-600">
            <li>The model <strong>composes</strong> a page by calling one or more render tools.</li>
            <li>Each tool builds a <strong>serialized section</strong> (whitelisted nodes).</li>
            <li>Sections <strong>stream</strong> over SSE; the client paints them progressively.</li>
            <li>No code-gen, no sandbox — only pre-written components render.</li>
          </ol>
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Server tools</h2>
          <ul class="mt-2 space-y-1 text-xs text-slate-600">
            <li><code>render_flight_list</code> — search / browse (+ only delayed)</li>
            <li><code>render_flight_detail</code> — one flight</li>
            <li><code>render_delays_overview</code> — delay table</li>
            <li><code>render_summary</code> — stats panel</li>
            <li><code>render_note</code> — explanatory line</li>
          </ul>
        </div>

        <div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900">
          <h2 class="text-xs font-semibold uppercase tracking-wide">Setup</h2>
          <pre class="mt-2 overflow-x-auto rounded bg-amber-100 p-2 text-xs">export OPENAI_API_KEY=sk-...
make dev-backend</pre>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { RscToolInfo } from '~/types/rsc'

const approach = useApproach('server-streamed-ui')
const { nodes, tools, streaming, error, stream } = useRscStream()

const prompt = ref('')
const suggestions = [
  'Flights from Graz to Hamburg',
  'Overview of delays, then the delayed flights',
  'Details for AB123',
  'Summarize everything and show flights to Berlin',
]

const argsText = (t: RscToolInfo) =>
  Object.entries(t.args).map(([k, v]) => `${k}: ${v}`).join(', ')

async function submit(text: string) {
  const value = text.trim()
  if (!value || streaming.value) return
  prompt.value = value
  await stream(value)
}
</script>
