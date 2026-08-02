<template>
  <div class="rounded-lg border border-slate-200 bg-white p-4">
    <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Agent actions</h2>
    <ol v-if="log.length" class="mt-2 space-y-1.5">
      <li v-for="(entry, i) in log" :key="i" class="flex items-start gap-2 text-xs">
        <span>{{ icon(entry.name) }}</span>
        <span class="flex-1 text-slate-600">{{ entry.desc }}</span>
        <span v-if="entry.next" class="rounded bg-slate-100 px-1 py-0.5 text-[10px] text-slate-400">{{ entry.next }}</span>
      </li>
    </ol>
    <p v-else class="mt-2 text-xs text-slate-400">Give the agent a goal — its actions appear here.</p>
  </div>
</template>

<script setup lang="ts">
import type { LogEntry } from '~/types/agent'

defineProps<{ log: LogEntry[] }>()

const ICONS: Record<string, string> = {
  update_form: '✏️',
  set_filter: '🔎',
  sort_flights: '↕️',
  goto: '🧭',
  select_flight: '✔️',
  book: '🧾',
  finish: '🏁',
}
const icon = (name: string) => ICONS[name] ?? '•'
</script>
