<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#8</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <ApproachIntro
      type="Protocol-decoupled agents (MCP · MCP-UI · AG-UI)"
      level="orthogonal — an architecture layer under approaches 1–7"
      demonstrates="The UI is a pure function of a typed AG-UI event stream — swap the backend and it wouldn't change. State syncs via STATE_SNAPSHOT + STATE_DELTA (RFC-6902 JSON Patch); a tool result can carry an MCP-UI ui:// HTML resource rendered in a sandboxed iframe that posts intents back."
    />

    <div class="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
      The UI below is a <strong>pure function of the AG-UI event stream</strong> — swap the backend and it
      wouldn't change. A tool result can carry an <strong>MCP-UI</strong> <code>ui://</code> resource rendered
      in a sandboxed iframe that posts intents back. State syncs via <code>STATE_SNAPSHOT</code> +
      <code>STATE_DELTA</code> (JSON Patch). Watch the inspector on the right.
    </div>

    <div class="mt-4 grid gap-6 lg:grid-cols-2">
      <!-- rendered from the protocol -->
      <div class="min-w-0 space-y-4">
        <form class="flex gap-2" @submit.prevent="submit(prompt)">
          <input
            v-model="prompt"
            type="text"
            placeholder="e.g. Show flight AB123"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            :disabled="running"
          >
          <button
            type="submit"
            class="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
            :disabled="running || !prompt.trim()"
          >
            {{ running ? 'Streaming…' : 'Run' }}
          </button>
        </form>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="ex in examples"
            :key="ex"
            class="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
            :disabled="running"
            @click="submit(ex)"
          >
            {{ ex }}
          </button>
        </div>

        <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
        <p v-if="intentNote" class="rounded-lg bg-sky-50 px-3 py-2 text-xs text-sky-800">{{ intentNote }}</p>

        <div v-if="events.length" class="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
          <div v-if="text" class="text-sm text-slate-700">{{ text }}</div>

          <div v-if="toolCalls.length" class="flex flex-wrap gap-1.5">
            <span v-for="tc in toolCalls" :key="tc.id" class="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
              🔧 {{ tc.name }}
            </span>
          </div>

          <!-- MCP-UI resources -->
          <McpUiFrame v-for="(r, i) in resources" :key="i" :resource="r" @intent="onIntent" />

          <!-- state (from snapshot + deltas) -->
          <div v-if="stateFlights.length" class="rounded-lg border border-slate-100">
            <table class="w-full text-sm">
              <tbody>
                <tr v-for="f in stateFlights" :key="f.id" class="border-b border-slate-100 last:border-0">
                  <td class="px-3 py-1.5"><code class="font-semibold">{{ f.id }}</code></td>
                  <td class="px-3 py-1.5 text-slate-500">{{ f.origin }} → {{ f.destination }}</td>
                  <td class="px-3 py-1.5 text-right font-medium">€{{ f.price }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="booking" class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
            ✅ Booked <code>{{ booking.flight_id }}</code> · ref {{ booking.ref }}
          </div>
        </div>
      </div>

      <!-- the protocol itself -->
      <div class="min-w-0 space-y-4">
        <ProtocolInspector :events="events" />
        <p v-if="runId" class="text-xs text-slate-400">run <code>{{ runId }}</code> · thread <code>{{ threadId }}</code></p>

        <div class="rounded-lg border border-slate-200 bg-white p-4 text-xs">
          <h2 class="font-semibold uppercase tracking-wide text-slate-500">Complementary protocols</h2>
          <ul class="mt-2 space-y-1.5">
            <li v-for="p in info?.protocols" :key="p.name">
              <code class="font-semibold text-slate-700">{{ p.name }}</code>
              <span class="text-slate-400"> · {{ p.connects }}</span>
              <p class="text-slate-500">{{ p.role }}</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { McpUiIntent } from '~/types/protocol'

const approach = useApproach('protocol-decoupled')
const { info, events, text, toolCalls, state, resources, runId, threadId, running, error, loadInfo, run } = useProtocol()

const prompt = ref('')
const intentNote = ref('')
const examples = [
  'Show flight AB123',
  'Search flights from Graz to Hamburg',
  'Book flight CD200',
]

interface StateFlight { id: string, origin: string, destination: string, price: number }
const stateFlights = computed(() => (state.value?.flights as StateFlight[] | undefined) ?? [])
const booking = computed(() => state.value?.booking as { flight_id: string, ref: string } | null)

async function submit(text: string) {
  const value = text.trim()
  if (!value || running.value) return
  prompt.value = value
  intentNote.value = ''
  await run(value)
}

// MCP-UI resource posted an intent back → drive a new AG-UI run (the decoupled loop).
async function onIntent(intent: McpUiIntent) {
  intentNote.value = `MCP-UI intent received: ${intent.tool}(${JSON.stringify(intent.args)}) → running…`
  await run(`Book flight ${intent.args.flight_id}`)
}

onMounted(loadInfo)
</script>
