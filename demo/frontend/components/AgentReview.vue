<template>
  <div class="rounded-xl border bg-white p-4 transition" :class="highlight === 'review' ? 'border-ink ring-1 ring-ink' : 'border-slate-200'">
    <div class="flex items-center justify-between">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Review</h2>
      <span v-if="booked" class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
        ✅ Booked
      </span>
    </div>

    <div v-if="flight" class="mt-3">
      <div class="flex items-center gap-2">
        <code class="text-sm font-semibold">{{ flight.id }}</code>
        <span class="text-xs text-slate-500">{{ flight.origin }} → {{ flight.destination }} · {{ flight.date }}</span>
      </div>
      <dl class="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <div><dt class="text-xs text-slate-400">Departs</dt><dd class="font-medium">{{ flight.departure_time }}</dd></div>
        <div><dt class="text-xs text-slate-400">Duration</dt><dd class="font-medium">{{ dur(flight.duration_min) }}</dd></div>
        <div><dt class="text-xs text-slate-400">Passengers</dt><dd class="font-medium">{{ form.passengers }} · {{ form.cabin }}</dd></div>
        <div><dt class="text-xs text-slate-400">Price</dt><dd class="font-semibold">€{{ flight.price }}</dd></div>
      </dl>
    </div>
    <p v-else class="mt-3 text-sm text-slate-400">No flight selected yet.</p>
  </div>
</template>

<script setup lang="ts">
import type { AgentFlight, AppForm } from '~/types/agent'

defineProps<{ flight: AgentFlight | undefined, form: AppForm, booked: boolean, highlight: string }>()

const dur = (m: number) => `${Math.floor(m / 60)}h ${String(m % 60).padStart(2, '0')}m`
</script>
