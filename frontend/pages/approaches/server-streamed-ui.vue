<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#5</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <ApproachIntro
      type="Server-streamed generative UI (RSC / streamUI style)"
      level="★★★★☆ — the server renders the UI"
      demonstrates="The model composes a page by calling server render tools; the server renders each component to a real HTML fragment and streams the fragments over SSE, which the client mounts progressively. The reusable pieces are framework-agnostic web components (&lt;flight-card&gt;) — unlike #3's client-owned Vue components."
    />

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
      <div class="min-w-0 space-y-4">
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

        <div v-if="fragments.length || streaming" class="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <RscHtmlStream :fragments="fragments" />
          <p v-if="streaming" class="mt-2 flex items-center gap-1 text-xs text-slate-400">
            <span class="h-2 w-2 animate-pulse rounded-full bg-amber-400" /> streaming from server…
          </p>
        </div>
      </div>

      <aside class="min-w-0 space-y-4 text-sm">
        <WireInspector :frames="wire" />

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">How this works</h2>
          <ol class="mt-2 list-decimal space-y-1 pl-4 text-slate-600">
            <li>The model <strong>composes</strong> a page by calling one or more render tools.</li>
            <li>The <strong>server renders</strong> each component to a <strong>real HTML fragment</strong>.</li>
            <li>Fragments <strong>stream</strong> over SSE; the client mounts each progressively.</li>
            <li>Flight cards are <code>&lt;flight-card&gt;</code> <strong>web components</strong> — framework-agnostic, unlike #3's Vue-only components.</li>
          </ol>
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Server tools</h2>
          <p class="mt-1 text-xs text-slate-500">
            The model composes the page by calling these server-side render tools; the server renders each
            to HTML and streams it. Try “overview of delays, then the delayed flights”.
          </p>
          <ul class="mt-2 space-y-1 text-xs text-slate-600">
            <li><code>render_flight_list</code> — search / browse (+ only delayed)</li>
            <li><code>render_flight_detail</code> — one flight</li>
            <li><code>render_delays_overview</code> — delay table</li>
            <li><code>render_summary</code> — stats panel</li>
            <li><code>render_note</code> — explanatory line</li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { RscToolInfo } from '~/types/rsc'

const approach = useApproach('server-streamed-ui')
const { fragments, tools, streaming, error, wire, stream } = useRscStream()

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
