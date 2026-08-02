<template>
  <div class="rounded-lg border border-slate-200 bg-slate-950 p-3 font-mono text-xs text-slate-200">
    <div class="mb-2 flex items-center justify-between text-slate-400">
      <span>AG-UI event stream</span>
      <span>{{ events.length }} events</span>
    </div>
    <ol class="max-h-[420px] space-y-1 overflow-y-auto">
      <li v-for="(ev, i) in events" :key="i" class="flex items-start gap-2">
        <span class="rounded px-1.5 py-0.5 text-[10px] font-semibold" :class="groupClass(ev.type)">{{ ev.type }}</span>
        <span class="min-w-0 flex-1 truncate text-slate-400">{{ preview(ev) }}</span>
      </li>
      <li v-if="!events.length" class="text-slate-500">Run something — the typed events stream here.</li>
    </ol>
  </div>
</template>

<script setup lang="ts">
import type { ProtoEvent } from '~/types/protocol'

defineProps<{ events: ProtoEvent[] }>()

const GROUP: Record<string, string> = {
  RUN_STARTED: 'life', RUN_FINISHED: 'life', RUN_ERROR: 'life', STEP_STARTED: 'life', STEP_FINISHED: 'life',
  TEXT_MESSAGE_START: 'text', TEXT_MESSAGE_CONTENT: 'text', TEXT_MESSAGE_END: 'text',
  TOOL_CALL_START: 'tool', TOOL_CALL_ARGS: 'tool', TOOL_CALL_END: 'tool', TOOL_CALL_RESULT: 'tool',
  STATE_SNAPSHOT: 'state', STATE_DELTA: 'state',
  RAW: 'special', CUSTOM: 'special',
}
const CLASS: Record<string, string> = {
  life: 'bg-sky-900 text-sky-200',
  text: 'bg-emerald-900 text-emerald-200',
  tool: 'bg-amber-900 text-amber-200',
  state: 'bg-fuchsia-900 text-fuchsia-200',
  special: 'bg-slate-700 text-slate-200',
}
const groupClass = (type: string) => CLASS[GROUP[type] ?? 'special']

function preview(ev: ProtoEvent) {
  const rest: Record<string, unknown> = { ...ev }
  delete rest.type
  const json = JSON.stringify(rest)
  return json.length > 90 ? `${json.slice(0, 90)}…` : json
}
</script>
