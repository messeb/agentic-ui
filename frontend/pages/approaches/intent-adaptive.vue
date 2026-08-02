<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#6</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <ApproachIntro
      type="Intent-based adaptive UI (inference layer)"
      level="★★★☆☆ — no chat, context-driven"
      demonstrates="No prompt at all. An inference layer reads the trip's live context — time to departure, whether you've checked in, and any disruption — and scores each card by relevance, surfacing the most useful one to the top and hiding the rest (layout morphing). Scrub time toward departure and the top card changes: overview → check-in → boarding; trigger a disruption and its alert jumps to the top. Deterministic; needs no API key. Each score has a rationale to counter the 'why did it change?' opacity."
    />

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
      <div class="min-w-0 space-y-4">
        <!-- context controls (this is the 'input' — no chat) -->
        <div class="rounded-xl border border-slate-200 bg-white p-4">
          <div class="flex items-baseline justify-between">
            <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Trip context</h2>
            <span class="font-mono text-sm font-semibold text-slate-800">{{ tMinus(minutesToDeparture) }}</span>
          </div>

          <input
            v-model.number="scrub"
            type="range"
            min="0"
            max="2940"
            step="5"
            class="mt-3 w-full accent-ink"
            aria-label="Time until departure"
          >
          <div class="flex justify-between text-[10px] text-slate-400">
            <span>48h before</span>
            <span>departure →</span>
          </div>

          <div class="mt-2 flex flex-wrap gap-1.5">
            <button
              v-for="j in jumps"
              :key="j.label"
              class="rounded-full border border-slate-300 bg-white px-2 py-0.5 text-xs text-slate-600 hover:border-slate-500"
              @click="minutesToDeparture = j.m"
            >
              {{ j.label }}
            </button>
          </div>

          <div class="mt-3 flex flex-wrap items-center gap-1.5">
            <span class="text-xs text-slate-500">Disruption:</span>
            <button
              v-for="d in disruptions"
              :key="d.value"
              class="rounded-full px-2.5 py-1 text-xs"
              :class="disruption === d.value
                ? 'bg-ink text-white'
                : 'border border-slate-300 text-slate-600 hover:border-slate-500'"
              @click="disruption = d.value"
            >
              {{ d.label }}
            </button>
          </div>

          <div class="mt-3 flex items-center gap-3 text-xs">
            <span :class="checkedIn ? 'text-emerald-600' : 'text-slate-400'">
              {{ checkedIn ? '✓ Checked in' : 'Not checked in' }}
            </span>
            <button class="ml-auto text-slate-400 hover:text-slate-700" @click="reset">reset</button>
          </div>
        </div>

        <p v-if="dataError" class="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">{{ dataError }}</p>

        <!-- the adaptive card stack — ordered & filtered by the inference layer -->
        <div v-if="trip && plan" class="space-y-3">
          <AdaptiveCard
            v-for="(c, i) in orderedCards"
            :key="c.id"
            :card="c"
            :trip="trip"
            :plan="plan"
            :emphasized="i === 0"
            @checkin="checkIn"
          />
        </div>
      </div>

      <aside class="min-w-0 space-y-4">
        <InferencePanel :plan="plan" />

        <WireInspector :frames="wire" title="Inference layer (backend)" />

        <div class="rounded-lg border border-slate-200 bg-white p-4 text-xs text-slate-500">
          <h2 class="font-semibold uppercase tracking-wide text-slate-500">Signals read</h2>
          <ul class="mt-2 list-disc space-y-1 pl-4">
            <li>time to departure (the scrubber)</li>
            <li>check-in window open / already checked in</li>
            <li>operational status (delay · gate change · cancellation)</li>
          </ul>
          <p class="mt-2">No chat, no clicks-as-intent — the trip's own context drives the layout.</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Disruption } from '~/types/adaptive'

const approach = useApproach('intent-adaptive')
const {
  trip, plan, dataError, wire,
  minutesToDeparture, checkedIn, disruption,
  orderedCards, loadData, checkIn, reset,
} = useAdaptive()

// The slider runs left→right as 48h-before → departure, so invert onto minutes-to-departure.
const scrub = computed({
  get: () => 2880 - minutesToDeparture.value,
  set: (v: number) => { minutesToDeparture.value = 2880 - Number(v) },
})

const jumps = [
  { m: 28 * 60, label: 'T-28h' },
  { m: 20 * 60, label: 'Check-in' },
  { m: 120, label: 'T-2h' },
  { m: 30, label: 'Boarding' },
]

const disruptions: { value: Disruption, label: string }[] = [
  { value: 'none', label: 'On time' },
  { value: 'delayed', label: 'Delay' },
  { value: 'gate_change', label: 'Gate change' },
  { value: 'cancelled', label: 'Cancelled' },
]

function tMinus(m: number): string {
  const abs = Math.abs(m)
  const h = Math.floor(abs / 60)
  const min = abs % 60
  return `${m < 0 ? 'T+' : 'T−'}${h}h ${String(min).padStart(2, '0')}m`
}

onMounted(loadData)
</script>
