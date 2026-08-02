<template>
  <div class="rounded-lg border border-slate-200 bg-white p-4">
    <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Inference layer</h2>

    <p v-if="plan" class="mt-2 rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-900">
      {{ plan.rationale }}
    </p>

    <ul v-if="plan" class="mt-3 space-y-2">
      <li v-for="c in plan.cards" :key="c.id" class="text-xs">
        <div class="flex items-center gap-2">
          <span class="w-20 shrink-0 capitalize" :class="c.id === plan.primary ? 'font-semibold text-slate-800' : 'text-slate-500'">
            {{ c.id }}
          </span>
          <div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div class="h-full rounded-full" :class="c.id === plan.primary ? 'bg-ink' : 'bg-slate-300'" :style="{ width: c.score + '%' }" />
          </div>
          <span class="w-8 shrink-0 text-right tabular-nums text-slate-400">{{ c.score }}</span>
          <span class="w-10 shrink-0 text-right" :class="c.visible ? 'text-emerald-600' : 'text-slate-300'">
            {{ c.visible ? 'shown' : 'hidden' }}
          </span>
        </div>
      </li>
    </ul>

    <p class="mt-3 text-[11px] leading-snug text-slate-400">
      Scores come from the trip context (time to departure, check-in window, disruption) — not from
      clicks. The highest-scoring visible card is surfaced to the top.
    </p>
  </div>
</template>

<script setup lang="ts">
import type { InferResult } from '~/types/adaptive'

defineProps<{ plan: InferResult | null }>()
</script>
