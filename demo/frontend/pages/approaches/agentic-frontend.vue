<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#7</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
      <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">● Live demo</span>
      <span class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">most capable</span>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <!-- accessibility: announce every agent-driven change -->
    <p class="sr-only" aria-live="polite">{{ live }}</p>

    <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
      <div class="min-w-0 space-y-4">
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          🤖 Give the agent a <strong>goal</strong>. It operates the whole app — every UI mutation is a tool
          call applied to the reactive store. The backend is stateless: it rebuilds the prompt from live
          state each turn. Booking is <strong>gated by your confirmation</strong>. State + any text you enter
          flow into the prompt, so scope tools tightly (prompt-injection surface).
        </div>

        <form class="flex gap-2" @submit.prevent="run(goal)">
          <input
            v-model="goal"
            type="text"
            placeholder="e.g. Book the cheapest morning direct flight from Graz to Hamburg for 2"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            :disabled="running"
          >
          <button
            v-if="!running"
            type="submit"
            class="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
            :disabled="!goal.trim()"
          >
            Run
          </button>
          <button v-else type="button" class="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white" @click="stop">
            Stop
          </button>
        </form>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="ex in examples"
            :key="ex"
            class="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
            :disabled="running"
            @click="run(ex)"
          >
            {{ ex }}
          </button>
          <button class="ml-auto text-xs text-slate-400 hover:text-slate-700" @click="reset">reset</button>
        </div>

        <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>

        <!-- HITL gate -->
        <div v-if="pendingBook" class="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm">
          <p class="font-medium text-amber-900">
            ⚠️ The agent wants to <strong>book {{ state.selectedFlightId }}</strong>
            for {{ state.form.passengers }} ({{ state.form.cabin }}). Confirm?
          </p>
          <div class="mt-2 flex gap-2">
            <button class="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white" @click="confirmBook(true)">Confirm booking</button>
            <button class="rounded-md bg-white px-3 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-slate-300" @click="confirmBook(false)">Cancel</button>
          </div>
        </div>

        <!-- step tabs (agent navigates via goto; user can click too) -->
        <div class="flex gap-1 text-xs">
          <button
            v-for="st in (['search', 'results', 'review'] as const)"
            :key="st"
            class="rounded-full px-3 py-1 capitalize"
            :class="state.step === st ? 'bg-ink text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            @click="state.step = st"
          >
            {{ st }}
          </button>
          <span v-if="running" class="ml-2 flex items-center gap-1 text-slate-400">
            <span class="h-2 w-2 animate-pulse rounded-full bg-amber-400" /> agent working…
          </span>
        </div>

        <AgentSearchForm v-if="state.step === 'search'" :form="state.form" :highlight="highlight" @change="onChange" />
        <AgentResults
          v-else-if="state.step === 'results'"
          :flights="visibleFlights"
          :filters="state.filters"
          :sort="state.sort"
          :selected-id="state.selectedFlightId"
          :highlight="highlight"
          @select="onSelect"
        />
        <AgentReview v-else :flight="selectedFlight" :form="state.form" :booked="state.booked" :highlight="highlight" />
      </div>

      <aside class="space-y-4">
        <AgentActionLog :log="log" />
        <div class="rounded-lg border border-slate-200 bg-white p-4 text-xs text-slate-500">
          <h2 class="font-semibold uppercase tracking-wide text-slate-500">Tools = UI mutations</h2>
          <ul class="mt-2 space-y-1">
            <li><code>update_form</code> · <code>set_filter</code> · <code>sort_flights</code></li>
            <li><code>goto</code> · <code>select_flight</code></li>
            <li><code>book</code> (HITL) · <code>finish</code></li>
          </ul>
          <p class="mt-2">Each carries a <code>next</code> directive that drives the loop.</p>
        </div>
        <div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900">
          Needs <code>OPENAI_API_KEY</code>. Cost grows per turn (full state each time) — production uses
          prompt caching + state diffing.
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { AppForm } from '~/types/agent'

const approach = useApproach('agentic-frontend')
const {
  state, flights, visibleFlights, log, running, pendingBook, error, live, highlight,
  loadData, run, stop, confirmBook, setForm, reset,
} = useAgentApp()

const goal = ref('')
const examples = [
  'Find the cheapest morning direct flight from Graz to Hamburg',
  'Book a flight from Vienna to Berlin under €120 for 2 people',
  'Show fastest Graz to London flights',
]

const selectedFlight = computed(() => flights.value.find(f => f.id === state.selectedFlightId))

function onChange(payload: { field: keyof AppForm, value: string }) {
  setForm(payload.field, payload.value)
}
function onSelect(id: string) {
  state.selectedFlightId = id
  state.step = 'review'
}

onMounted(loadData)
</script>
