<template>
  <NuxtLink
    :to="`/approaches/${approach.id}`"
    class="group flex flex-col rounded-xl border border-slate-200 bg-white p-5 transition hover:border-slate-400 hover:shadow-md"
  >
    <div class="mb-2 flex items-center justify-between">
      <span class="text-xs font-mono text-slate-400">#{{ approach.number }}</span>
      <div class="flex items-center gap-1.5">
        <span
          v-if="approach.status === 'implemented'"
          class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800"
        >
          ● Live
        </span>
        <span
          class="rounded-full px-2 py-0.5 text-xs font-medium"
          :class="maturityClass(approach.maturity)"
        >
          {{ maturityLabel(approach.maturity) }}
        </span>
      </div>
    </div>
    <h3 class="font-semibold text-slate-900 group-hover:text-ink">{{ approach.title }}</h3>
    <p class="mt-1 text-sm text-slate-600">{{ approach.tagline }}</p>
    <dl class="mt-4 space-y-1 text-xs text-slate-500">
      <div class="flex gap-1">
        <dt class="font-semibold text-slate-700">In:</dt>
        <dd>{{ approach.input }}</dd>
      </div>
      <div class="flex gap-1">
        <dt class="font-semibold text-slate-700">Out:</dt>
        <dd>{{ approach.output }}</dd>
      </div>
    </dl>
    <div class="mt-4 flex items-center gap-1 text-amber-500" :aria-label="`Agentic level ${approach.agenticLevel} of 5`">
      <span v-for="n in 5" :key="n">{{ n <= approach.agenticLevel ? '★' : '☆' }}</span>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import type { Approach } from '~/types/approach'

defineProps<{ approach: Approach }>()
</script>
