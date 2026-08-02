<template>
  <!-- Always shown (like #8's event inspector), including an empty state. Shows the raw payloads the
       backend sent (SSE frames / JSON responses) verbatim; click a row to expand its full body. -->
  <div class="rounded-lg border border-slate-200 bg-slate-950 p-3 font-mono text-xs text-slate-200">
    <div class="mb-2 flex items-center justify-between text-slate-400">
      <span>{{ title }}</span>
      <span>{{ frames.length }} {{ frames.length === 1 ? 'frame' : 'frames' }}</span>
    </div>
    <ol class="max-h-[420px] space-y-1 overflow-y-auto">
      <li v-for="(f, i) in frames" :key="i">
        <button type="button" class="flex w-full items-start gap-2 text-left" @click="toggle(i)">
          <span class="rounded px-1.5 py-0.5 text-[10px] font-semibold" :class="kindClass(f.kind)">{{ f.label }}</span>
          <span
            class="min-w-0 flex-1 text-slate-400"
            :class="expanded.has(i) ? 'whitespace-pre-wrap break-all' : 'truncate'"
          >{{ expanded.has(i) ? f.body : oneLine(f.body) }}</span>
        </button>
      </li>
      <li v-if="!frames.length" class="text-slate-500">Run something — the backend frames stream here.</li>
    </ol>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { WireFrame } from '~/types/wire'

withDefaults(defineProps<{ frames: WireFrame[], title?: string }>(), {
  title: 'Backend stream',
})

const expanded = ref<Set<number>>(new Set())

function toggle(i: number) {
  // Reassign so Vue tracks the Set mutation.
  const next = new Set(expanded.value)
  if (next.has(i)) next.delete(i)
  else next.add(i)
  expanded.value = next
}

const CLASS: Record<string, string> = {
  request: 'bg-sky-900 text-sky-200',
  stream: 'bg-amber-900 text-amber-200',
  response: 'bg-emerald-900 text-emerald-200',
  error: 'bg-rose-900 text-rose-200',
}
const kindClass = (kind?: string) => CLASS[kind ?? 'stream'] ?? CLASS.stream

const oneLine = (body: string) => {
  const s = body.replace(/\s+/g, ' ').trim()
  return s.length > 120 ? `${s.slice(0, 120)}…` : s
}
</script>
