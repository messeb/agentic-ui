<template>
  <div class="rounded-lg border border-slate-200 bg-white p-4">
    <div class="flex items-center gap-2 text-sm font-semibold text-slate-700">
      🛒 Cart <span class="font-normal text-slate-400">· {{ data.items.length }} item(s)</span>
    </div>
    <ul class="mt-2 space-y-1 text-sm">
      <li v-for="o in data.items" :key="o.id" class="flex justify-between text-slate-600">
        <span>{{ o.label }}</span>
        <span>€{{ o.price }}</span>
      </li>
    </ul>
    <div class="mt-2 flex justify-between border-t border-slate-100 pt-1 text-sm font-semibold">
      <span>Subtotal</span>
      <span>€{{ data.subtotal }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CartSummaryProps } from '~/types/catalog'

defineProps<{ data: CartSummaryProps }>()
</script>
