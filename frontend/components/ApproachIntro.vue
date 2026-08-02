<template>
  <!-- Front-matter explanation shown before the example (full width, not in the aside). -->
  <div class="mt-4 rounded-xl border border-slate-200 border-l-4 border-l-ink bg-slate-50 p-4">
    <div class="flex flex-wrap items-baseline gap-x-2 gap-y-1">
      <h2 class="text-sm font-semibold text-slate-800">{{ type }}</h2>
      <span v-if="level" class="text-xs text-slate-400">{{ level }}</span>
    </div>
    <p class="mt-1.5 text-sm text-slate-600">
      <span class="font-medium text-slate-700">Demonstrates:</span> {{ demonstrates }}
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ type: string, demonstrates: string, level?: string }>()
</script>
