<template>
  <div class="space-y-10">
    <!-- hero + evolution axis -->
    <section>
      <h1 class="text-2xl font-bold text-slate-900">Agentic UI Patterns</h1>
      <p class="mt-2 max-w-2xl text-slate-600">
        How AI drives a user interface, told as an <strong>evolution</strong>. Each stage hands the AI more
        authority over the interface — from merely <em>talking about</em> the app, to acting on it, to
        <em>generating and operating</em> it outright. The stages aren't exclusive: they compose, and real
        products stack several.
      </p>

      <div class="mt-6 rounded-xl border border-slate-200 bg-white p-4">
        <div class="flex items-stretch gap-1 overflow-x-auto pb-1 text-center">
          <template v-for="(p, i) in forwardPhases" :key="p.key">
            <div class="flex min-w-0 flex-1 flex-col items-center px-1">
              <span class="flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">{{ i + 1 }}</span>
              <span class="mt-1 text-sm font-semibold text-slate-800">{{ p.name }}</span>
              <span class="text-[11px] leading-tight text-slate-400">{{ p.tag }}</span>
            </div>
            <span v-if="i < forwardPhases.length - 1" class="self-center text-slate-300">→</span>
          </template>
        </div>
        <div class="mt-3 h-1.5 rounded-full bg-gradient-to-r from-emerald-300 via-amber-300 to-rose-400" />
        <div class="mt-1 flex justify-between text-[10px] text-slate-400">
          <span>AI suggests · low authority · deterministic</span>
          <span>AI operates · high authority · autonomous</span>
        </div>
      </div>
    </section>

    <!-- one section per evolutionary stage -->
    <section v-for="p in phases" :key="p.key">
      <div class="flex items-baseline gap-3">
        <span class="font-mono text-3xl font-bold" :class="p.orthogonal ? 'text-indigo-200' : 'text-slate-200'">{{ p.label }}</span>
        <div>
          <h2 class="text-lg font-bold text-slate-900">
            {{ p.name }}
            <span class="text-sm font-normal text-slate-400">— {{ p.tag }}</span>
          </h2>
          <p class="mt-0.5 max-w-2xl text-sm text-slate-600">{{ p.blurb }}</p>
        </div>
      </div>

      <div class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ApproachCard v-for="a in p.items" :key="a.id" :approach="a" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Approach } from '~/types/approach'

const approaches = useApproaches()
const byNumber = new Map(approaches.map(a => [a.number, a]))

interface PhaseDef {
  key: string
  label: string
  name: string
  tag: string
  blurb: string
  numbers: number[]
  orthogonal?: boolean
}

const PHASES: PhaseDef[] = [
  {
    key: 'talk',
    label: '01',
    name: 'Talk',
    tag: 'the AI answers',
    blurb: 'The assistant sits beside the app and answers in text. It can explain and draft, but the user still does all the work — nothing in the app changes.',
    numbers: [1],
  },
  {
    key: 'act',
    label: '02',
    name: 'Act',
    tag: 'the AI calls tools',
    blurb: 'Function calling connects the model to real data and actions. It decides to call a tool, the result comes back into the loop, and that drives what is shown.',
    numbers: [2],
  },
  {
    key: 'render',
    label: '03',
    name: 'Render',
    tag: 'the AI builds the UI',
    blurb: 'Beyond text, the model produces the interface itself — choosing components from a catalog, generating sandboxed code, or streaming server-rendered fragments.',
    numbers: [3, 4, 5],
  },
  {
    key: 'adapt',
    label: '04',
    name: 'Adapt',
    tag: 'no prompt at all',
    blurb: 'The conversation disappears. An inference layer reads live context and intent and rearranges the UI on its own — surfacing what matters, hiding what does not.',
    numbers: [6],
  },
  {
    key: 'operate',
    label: '05',
    name: 'Operate',
    tag: 'the AI runs the app',
    blurb: 'Full autonomy: a goal goes in and the agent operates the whole app — every UI mutation is a tool. Humans set the intent and approve consequential actions.',
    numbers: [7],
  },
  {
    key: 'foundation',
    label: '∞',
    name: 'Foundation',
    tag: 'the wiring underneath',
    blurb: 'Not a rung on the ladder — open protocols (MCP · MCP-UI · AG-UI) that decouple UI, agent, and vendor. Any pattern above can ride on them.',
    numbers: [8],
    orthogonal: true,
  },
]

function itemsFor(numbers: number[]): Approach[] {
  return numbers.flatMap((n) => {
    const a = byNumber.get(n)
    return a ? [a] : []
  })
}

const phases = computed(() => PHASES.map(p => ({ ...p, items: itemsFor(p.numbers) })))
const forwardPhases = computed(() => phases.value.filter(p => !p.orthogonal))
</script>
