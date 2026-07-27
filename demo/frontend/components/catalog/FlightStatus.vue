<template>
  <div class="rounded-lg border border-slate-200 bg-white p-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span>🛫</span>
        <code class="text-sm font-semibold">{{ data.flight_id }}</code>
      </div>
      <span class="rounded-full px-2.5 py-0.5 text-xs font-medium" :class="pillClass">
        {{ label }}
      </span>
    </div>
    <dl class="mt-3 grid grid-cols-3 gap-2 text-sm">
      <div>
        <dt class="text-xs text-slate-400">Departure</dt>
        <dd class="font-medium">{{ data.departure_time }}</dd>
      </div>
      <div>
        <dt class="text-xs text-slate-400">Gate</dt>
        <dd class="font-medium">{{ data.gate ?? '—' }}</dd>
      </div>
      <div>
        <dt class="text-xs text-slate-400">Delay</dt>
        <dd class="font-medium">{{ data.delay_minutes ? `${data.delay_minutes} min` : '—' }}</dd>
      </div>
    </dl>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FlightStatusProps } from '~/types/catalog'

const props = defineProps<{ data: FlightStatusProps }>()

const LABELS = {
  'on-time': 'On time',
  'delayed': 'Delayed',
  'boarding': 'Boarding',
  'cancelled': 'Cancelled',
}
const CLASSES = {
  'on-time': 'bg-emerald-100 text-emerald-800',
  'delayed': 'bg-amber-100 text-amber-800',
  'boarding': 'bg-sky-100 text-sky-800',
  'cancelled': 'bg-rose-100 text-rose-800',
}
const label = computed(() => LABELS[props.data.status])
const pillClass = computed(() => CLASSES[props.data.status])
</script>
