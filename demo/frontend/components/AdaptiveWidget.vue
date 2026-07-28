<template>
  <div
    class="rounded-lg border bg-white p-3 text-sm transition"
    :class="emphasized ? 'border-ink ring-1 ring-ink' : 'border-slate-200'"
  >
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-500">{{ widget.title }}</h3>
      <span v-if="emphasized" class="rounded-full bg-ink px-1.5 py-0.5 text-[10px] font-medium text-white">
        for you
      </span>
    </div>

    <!-- deals -->
    <ul v-if="widget.id === 'deals'" class="mt-2 space-y-1">
      <li v-for="f in cheapest" :key="f.id" class="flex justify-between text-xs">
        <span class="text-slate-600">{{ f.destination }}</span>
        <span class="font-medium">€{{ f.price }}</span>
      </li>
    </ul>

    <!-- fastest -->
    <ul v-else-if="widget.id === 'fastest'" class="mt-2 space-y-1">
      <li v-for="f in shortest" :key="f.id" class="flex justify-between text-xs">
        <span class="text-slate-600">{{ f.destination }}</span>
        <span class="font-medium">{{ dur(f.duration_min) }}</span>
      </li>
    </ul>

    <!-- popular -->
    <ul v-else-if="widget.id === 'popular'" class="mt-2 flex flex-wrap gap-1.5">
      <li v-for="p in popular" :key="p.name" class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
        {{ p.name }} · {{ p.count }}
      </li>
    </ul>

    <!-- book -->
    <div v-else-if="widget.id === 'book'" class="mt-2">
      <p class="text-xs text-slate-500">{{ focusId ? `Finish booking ${focusId}` : widget.description }}</p>
      <button class="mt-2 w-full rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:opacity-90">
        {{ focusId ? `Book ${focusId}` : 'Book' }}
      </button>
    </div>

    <!-- price_alert -->
    <div v-else-if="widget.id === 'price_alert'" class="mt-2">
      <p class="text-xs text-slate-500">{{ widget.description }}</p>
      <button class="mt-2 w-full rounded-md border border-slate-300 px-3 py-1.5 text-xs text-slate-700 hover:border-slate-500">
        Set a price alert
      </button>
    </div>

    <!-- assistant / fallback -->
    <p v-else class="mt-1 text-xs text-slate-500">{{ widget.description }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AdFlight, Widget } from '~/types/adaptive'

const props = defineProps<{
  widget: Widget
  flights: AdFlight[]
  emphasized?: boolean
  focusId?: string | null
}>()

const dur = (m: number) => `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`
const cheapest = computed(() => [...props.flights].sort((a, b) => a.price - b.price).slice(0, 3))
const shortest = computed(() => [...props.flights].sort((a, b) => a.duration_min - b.duration_min).slice(0, 3))
const popular = computed(() => {
  const counts = new Map<string, number>()
  for (const f of props.flights) counts.set(f.destination, (counts.get(f.destination) ?? 0) + 1)
  return [...counts.entries()].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count)
})
</script>
