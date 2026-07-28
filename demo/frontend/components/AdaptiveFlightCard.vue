<template>
  <div
    class="rounded-lg border bg-white p-3 transition"
    :class="focused ? 'border-ink ring-1 ring-ink' : 'border-slate-200 hover:border-slate-400'"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
  >
    <div class="flex items-center gap-3">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <code class="text-sm font-semibold">{{ flight.id }}</code>
          <span class="text-xs text-slate-400">{{ flight.airline }}</span>
        </div>
        <div class="truncate text-xs text-slate-500">
          {{ flight.origin }} → {{ flight.destination }} · {{ flight.date }}
        </div>
        <div class="mt-1 flex items-center gap-2 text-xs">
          <span :class="emphasis === 'time' ? 'font-semibold text-slate-800' : 'text-slate-500'">
            🕒 {{ duration }}
          </span>
          <span class="text-slate-400">· {{ flight.stops === 0 ? 'direct' : `${flight.stops} stop` }}</span>
          <span v-if="flight.delay_minutes" class="rounded-full bg-amber-100 px-1.5 py-0.5 text-amber-800">
            {{ flight.delay_minutes }}m late
          </span>
        </div>
      </div>
      <div class="text-right">
        <div :class="emphasis === 'price' ? 'text-lg font-bold text-ink' : 'font-semibold text-slate-900'">
          €{{ flight.price }}
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <button
          class="rounded-md border border-slate-300 px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500"
          @click="emit('click', 'view')"
        >
          Details
        </button>
        <button
          class="rounded-md bg-ink px-2.5 py-1 text-xs font-medium text-white hover:opacity-90"
          @click="emit('click', 'select')"
        >
          Select
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AdFlight } from '~/types/adaptive'

const props = defineProps<{ flight: AdFlight, focused?: boolean, emphasis?: 'price' | 'time' | null }>()
const emit = defineEmits<{ view: [dwellMs: number], click: [source: string] }>()

const duration = computed(() => {
  const m = props.flight.duration_min
  return `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`
})

let enteredAt = 0
function onEnter() {
  enteredAt = performance.now()
}
function onLeave() {
  const dwell = Math.round(performance.now() - enteredAt)
  if (enteredAt && dwell > 300) emit('view', dwell) // ignore accidental fly-overs
  enteredAt = 0
}
</script>
