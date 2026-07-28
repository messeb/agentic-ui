<template>
  <div class="rounded-lg border border-slate-200 bg-white p-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Inference layer</h2>
      <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="badgeClass">{{ primaryLabel }}</span>
    </div>

    <div class="mt-3 space-y-2">
      <div v-for="row in bars" :key="row.key">
        <div class="flex justify-between text-xs">
          <span class="text-slate-600">{{ row.label }}</span>
          <span class="text-slate-400">{{ Math.round(row.value * 100) }}%</span>
        </div>
        <div class="mt-0.5 h-1.5 overflow-hidden rounded bg-slate-100">
          <div class="h-full rounded transition-all" :class="row.key === primary ? 'bg-ink' : 'bg-slate-300'" :style="{ width: `${Math.round(row.value * 100)}%` }" />
        </div>
      </div>
    </div>

    <p class="mt-3 border-t border-slate-100 pt-2 text-xs text-slate-500">
      💡 {{ rationale }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { LayoutPlan } from '~/types/adaptive'

const props = defineProps<{ plan: LayoutPlan | null }>()

const LABELS = { price: 'Price-sensitive', time: 'Time-sensitive', urgency: 'Ready to book', explore: 'Exploring' }

const primary = computed(() => props.plan?.primary ?? 'explore')
const primaryLabel = computed(() => LABELS[primary.value])
const rationale = computed(() => props.plan?.rationale ?? 'Browse around — the UI will adapt to you.')
const bars = computed(() => {
  const i = props.plan?.intents ?? { price: 0, time: 0, urgency: 0, explore: 0.5 }
  return [
    { key: 'price', label: LABELS.price, value: i.price },
    { key: 'time', label: LABELS.time, value: i.time },
    { key: 'urgency', label: LABELS.urgency, value: i.urgency },
    { key: 'explore', label: LABELS.explore, value: i.explore },
  ]
})
const badgeClass = computed(() =>
  ({
    price: 'bg-emerald-100 text-emerald-800',
    time: 'bg-sky-100 text-sky-800',
    urgency: 'bg-amber-100 text-amber-800',
    explore: 'bg-slate-200 text-slate-700',
  }[primary.value]),
)
</script>
