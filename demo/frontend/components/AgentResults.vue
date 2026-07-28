<template>
  <div class="rounded-xl border bg-white p-4 transition" :class="highlight === 'results' ? 'border-ink ring-1 ring-ink' : 'border-slate-200'">
    <div class="flex flex-wrap items-center gap-2">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Results</h2>
      <span class="text-xs text-slate-400">{{ flights.length }} flights</span>
      <span v-for="chip in chips" :key="chip" class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
        {{ chip }}
      </span>
    </div>

    <div class="mt-3 overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-left text-xs text-slate-400">
          <tr>
            <th class="py-1 pr-2">Flight</th>
            <th class="py-1 pr-2">Dep</th>
            <th class="py-1 pr-2">Duration</th>
            <th class="py-1 pr-2">Stops</th>
            <th class="py-1 pr-2">Price</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-if="!flights.length"><td colspan="6" class="py-3 text-xs text-slate-400">No flights match the current form/filters.</td></tr>
          <tr
            v-for="f in flights"
            :key="f.id"
            class="border-t border-slate-100"
            :class="f.id === selectedId ? 'bg-slate-50' : ''"
          >
            <td class="py-2 pr-2"><code class="font-semibold">{{ f.id }}</code></td>
            <td class="py-2 pr-2">{{ f.departure_time }}</td>
            <td class="py-2 pr-2">{{ dur(f.duration_min) }}</td>
            <td class="py-2 pr-2">{{ f.stops === 0 ? 'direct' : f.stops }}</td>
            <td class="py-2 pr-2 font-medium">€{{ f.price }}</td>
            <td class="py-2 text-right">
              <button
                class="rounded-md border border-slate-300 px-2 py-1 text-xs hover:border-slate-500"
                :class="f.id === selectedId ? 'bg-ink text-white' : 'text-slate-600'"
                @click="emit('select', f.id)"
              >
                {{ f.id === selectedId ? 'selected' : 'select' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AgentFlight, AppFilters } from '~/types/agent'

const props = defineProps<{
  flights: AgentFlight[]
  filters: AppFilters
  sort: 'price' | 'duration' | null
  selectedId: string | null
  highlight: string
}>()
const emit = defineEmits<{ select: [id: string] }>()

const dur = (m: number) => `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`
const chips = computed(() => {
  const out: string[] = []
  if (props.sort) out.push(`sorted: ${props.sort}`)
  if (props.filters.max_price != null) out.push(`≤ €${props.filters.max_price}`)
  if (props.filters.morning_only) out.push('morning only')
  if (props.filters.direct_only) out.push('direct only')
  return out
})
</script>
