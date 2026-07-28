<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#6</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
      <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">● Live demo</span>
      <span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-700">no chat</span>
      <span class="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-800">least mature</span>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
      <div class="min-w-0 space-y-4">
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          👀 <strong>No chat.</strong> Just browse — hover cards (dwell counts), tap a sort, click a flight.
          An inference layer scores your behaviour into intent and re-ranks the UI. Watch the
          <strong>Inference layer</strong> panel update. Telemetry stays in this session (a real one would
          need consent / GDPR handling).
        </div>

        <!-- sort taps are telemetry, not a chat -->
        <div class="flex items-center gap-2 text-xs">
          <span class="text-slate-500">Sort:</span>
          <button
            v-for="s in (['price', 'duration'] as const)"
            :key="s"
            class="rounded-full border px-2.5 py-1 capitalize"
            :class="plan?.sort === s ? 'border-ink bg-ink text-white' : 'border-slate-300 text-slate-600 hover:border-slate-500'"
            @click="onSort(s)"
          >
            {{ s }}
          </button>
          <button class="ml-auto text-slate-400 hover:text-slate-700" @click="reset">reset session</button>
        </div>

        <p v-if="dataError" class="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">{{ dataError }}</p>

        <div class="space-y-2">
          <AdaptiveFlightCard
            v-for="f in sortedFlights"
            :key="f.id"
            :flight="f"
            :focused="f.id === plan?.focus_flight_id"
            :emphasis="cardEmphasis"
            @view="onView(f.id, $event)"
            @click="onClick(f.id)"
          />
        </div>
      </div>

      <aside class="space-y-4">
        <IntentPanel :plan="plan" />

        <div class="space-y-2">
          <AdaptiveWidget
            v-for="(w, i) in orderedWidgets"
            :key="w.id"
            :widget="w"
            :flights="flights"
            :emphasized="i === 0 && !!plan && plan.emphasize.includes(w.id)"
            :focus-id="plan?.focus_flight_id"
          />
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-4 text-xs text-slate-500">
          <h2 class="font-semibold uppercase tracking-wide text-slate-500">Signals captured</h2>
          <ul class="mt-2 list-disc space-y-1 pl-4">
            <li>hover dwell time per card</li>
            <li>clicks (Details / Select)</li>
            <li>sort taps (price / duration)</li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const approach = useApproach('intent-adaptive')
const { flights, plan, dataError, loadData, record, reset, sortedFlights, orderedWidgets } = useAdaptive()

const cardEmphasis = computed<'price' | 'time' | null>(() => {
  if (plan.value?.primary === 'price') return 'price'
  if (plan.value?.primary === 'time') return 'time'
  return null
})

function onView(id: string, dwellMs: number) {
  record({ kind: 'view', flight_id: id, dwell_ms: dwellMs })
}
function onClick(id: string) {
  record({ kind: 'click', flight_id: id })
}
function onSort(sort: 'price' | 'duration') {
  record({ kind: 'sort', sort })
}

onMounted(loadData)
</script>
