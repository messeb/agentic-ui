<template>
  <div class="rounded-lg border border-slate-200 bg-white">
    <div class="border-b border-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
      ✈️ {{ data.origin }} → {{ data.destination }}
      <span class="font-normal text-slate-400">· {{ data.flights.length }} flights</span>
    </div>
    <ul class="divide-y divide-slate-100">
      <li v-for="f in data.flights" :key="f.id" class="flex items-center gap-3 px-4 py-3">
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <code class="text-sm font-semibold">{{ f.id }}</code>
            <span class="text-xs text-slate-400">{{ f.date }}</span>
          </div>
          <div class="text-xs text-slate-500">
            {{ f.seats > 0 ? `${f.seats} seats left` : 'sold out' }}
          </div>
        </div>
        <div class="text-right">
          <div class="font-semibold text-slate-900">€{{ f.price }}</div>
        </div>
        <button
          class="rounded-md bg-ink px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:opacity-40"
          :disabled="f.seats <= 0"
          @click="emit('select', f)"
        >
          Select
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import type { Flight, FlightResultsProps } from '~/types/catalog'

defineProps<{ data: FlightResultsProps }>()
const emit = defineEmits<{ select: [flight: Flight] }>()
</script>
