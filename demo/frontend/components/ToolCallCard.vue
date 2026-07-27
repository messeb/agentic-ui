<template>
  <div class="rounded-lg border bg-white text-sm" :class="borderClass">
    <div class="flex items-center gap-2 px-3 py-2">
      <span>{{ icon }}</span>
      <code class="font-semibold">{{ item.name }}</code>
      <span class="text-slate-400">(</span>
      <code class="text-xs text-slate-600">{{ argsText }}</code>
      <span class="text-slate-400">)</span>
      <span
        v-if="item.sideEffect"
        class="ml-auto rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800"
      >
        side-effect
      </span>
      <span class="ml-auto text-xs" :class="statusClass">{{ statusLabel }}</span>
    </div>
    <details v-if="item.status !== 'pending'" class="border-t border-slate-100 px-3 py-2">
      <summary class="cursor-pointer text-xs text-slate-500">result</summary>
      <pre class="mt-2 overflow-x-auto rounded bg-slate-900 p-2 text-xs text-slate-100">{{ resultText }}</pre>
    </details>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ToolItem } from '~/types/tools'

const props = defineProps<{ item: ToolItem }>()

const argsText = computed(() =>
  Object.entries(props.item.args)
    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
    .join(', '),
)
const resultText = computed(() => JSON.stringify(props.item.result, null, 2))

const icon = computed(() => (props.item.status === 'denied' ? '🚫' : props.item.sideEffect ? '⚙️' : '🔧'))
const statusLabel = computed(() =>
  ({ pending: 'running…', done: 'done', denied: 'declined' })[props.item.status],
)
const statusClass = computed(() =>
  ({ pending: 'text-slate-400', done: 'text-emerald-600', denied: 'text-rose-600' })[props.item.status],
)
const borderClass = computed(() =>
  props.item.status === 'denied' ? 'border-rose-200' : 'border-slate-200',
)
</script>
