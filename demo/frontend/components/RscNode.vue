<template>
  <!-- stack -->
  <div v-if="node.comp === 'stack'" class="space-y-3">
    <RscNode v-for="c in children" :key="c.id" :node="c" :children-map="childrenMap" />
  </div>

  <!-- statRow -->
  <div
    v-else-if="node.comp === 'statRow'"
    class="flex flex-wrap gap-6 rounded-lg border border-slate-200 bg-white p-3"
  >
    <RscNode v-for="c in children" :key="c.id" :node="c" :children-map="childrenMap" />
  </div>

  <!-- heading -->
  <component :is="headingTag" v-else-if="node.comp === 'heading'" class="text-base font-semibold text-slate-800">
    {{ str('text') }}
  </component>

  <!-- text -->
  <p v-else-if="node.comp === 'text'" class="text-sm" :class="muted ? 'text-slate-400' : 'text-slate-600'">
    {{ str('text') }}
  </p>

  <!-- stat -->
  <div v-else-if="node.comp === 'stat'">
    <div class="text-xs text-slate-400">{{ str('label') }}</div>
    <div class="font-medium text-slate-800">{{ str('value') }}</div>
  </div>

  <!-- badge -->
  <span v-else-if="node.comp === 'badge'" class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
    {{ str('text') }}
  </span>

  <!-- divider -->
  <hr v-else-if="node.comp === 'divider'" class="border-slate-200">

  <!-- flightCard -->
  <div
    v-else-if="node.comp === 'flightCard'"
    class="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3"
  >
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2">
        <code class="text-sm font-semibold">{{ str('id') }}</code>
        <span class="text-xs text-slate-400">{{ str('date') }}</span>
      </div>
      <div class="truncate text-xs text-slate-500">{{ str('origin') }} → {{ str('destination') }}</div>
    </div>
    <span
      class="rounded-full px-2 py-0.5 text-xs font-medium"
      :class="delay > 0 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'"
    >
      {{ delay > 0 ? `${delay}m late` : 'on time' }}
    </span>
    <div class="font-semibold text-slate-900">€{{ str('price') }}</div>
  </div>

  <!-- table -->
  <div v-else-if="node.comp === 'table'" class="overflow-x-auto rounded-lg border border-slate-200">
    <table class="w-full text-sm">
      <thead class="bg-slate-50 text-left">
        <tr>
          <th v-for="col in columns" :key="col" class="px-3 py-2 font-semibold text-slate-700">{{ col }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in rows" :key="i" class="border-t border-slate-100">
          <td v-for="(cell, j) in row" :key="j" class="px-3 py-2 text-slate-700">{{ cell }}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div v-else class="text-xs text-rose-500">unknown component: {{ node.comp }}</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RscNode as RscNodeT } from '~/types/rsc'

const props = defineProps<{ node: RscNodeT, childrenMap: Map<string, RscNodeT[]> }>()

const children = computed(() => props.childrenMap.get(props.node.id) ?? [])
const str = (key: string) => String(props.node.props[key] ?? '')
const muted = computed(() => props.node.props.muted === true)
const headingTag = computed(() => `h${Number(props.node.props.level ?? 2)}`)
const delay = computed(() => Number(props.node.props.delay ?? 0))
const columns = computed(() => (props.node.props.columns as string[] | undefined) ?? [])
const rows = computed(() => (props.node.props.rows as string[][] | undefined) ?? [])
</script>
