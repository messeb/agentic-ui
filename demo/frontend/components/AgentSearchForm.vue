<template>
  <div class="rounded-xl border border-slate-200 bg-white p-4">
    <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Search</h2>
    <div class="mt-3 grid gap-3 sm:grid-cols-2">
      <label v-for="f in fields" :key="f.key" class="block">
        <span class="text-xs text-slate-500">{{ f.label }}</span>
        <select
          v-if="f.options"
          :value="form[f.key]"
          class="mt-1 w-full rounded-md border px-2 py-1.5 text-sm transition"
          :class="ring(f.key)"
          @change="emit('change', { field: f.key, value: ($event.target as HTMLSelectElement).value })"
        >
          <option v-for="o in f.options" :key="o" :value="o">{{ o }}</option>
        </select>
        <input
          v-else
          :value="form[f.key]"
          type="text"
          :placeholder="f.placeholder"
          class="mt-1 w-full rounded-md border px-2 py-1.5 text-sm transition"
          :class="ring(f.key)"
          @input="emit('change', { field: f.key, value: ($event.target as HTMLInputElement).value })"
        >
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AppForm } from '~/types/agent'

const props = defineProps<{ form: AppForm, highlight: string }>()
const emit = defineEmits<{ change: [payload: { field: keyof AppForm, value: string }] }>()

const fields = [
  { key: 'origin' as const, label: 'Origin', placeholder: 'e.g. Graz' },
  { key: 'destination' as const, label: 'Destination', placeholder: 'e.g. Hamburg' },
  { key: 'date' as const, label: 'Date', placeholder: 'YYYY-MM-DD' },
  { key: 'passengers' as const, label: 'Passengers', placeholder: '1' },
  { key: 'cabin' as const, label: 'Cabin', options: ['economy', 'premium', 'business'] },
]

function ring(key: string) {
  return props.highlight === `form.${key}`
    ? 'border-ink ring-2 ring-ink'
    : 'border-slate-300 focus:border-slate-500 focus:outline-none'
}
</script>
