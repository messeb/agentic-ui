<template>
  <div class="rounded-lg border border-slate-200 bg-white p-4">
    <h3 class="text-sm font-semibold text-slate-700">{{ data.title }}</h3>
    <div class="mt-3 grid gap-2 sm:grid-cols-2">
      <div
        v-for="o in data.options"
        :key="o.id"
        class="flex flex-col rounded-lg border border-slate-200 p-3"
      >
        <div class="flex items-center gap-2">
          <span>{{ icon(o.kind) }}</span>
          <span class="text-sm font-medium">{{ o.label }}</span>
        </div>
        <p class="mt-1 flex-1 text-xs text-slate-500">{{ o.description }}</p>
        <button
          class="mt-2 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50"
          :disabled="added.has(o.id)"
          @click="add(o)"
        >
          {{ added.has(o.id) ? 'Added ✓' : `Add · €${o.price}` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import type { AncillaryKind, AncillaryOption, AncillaryOfferProps } from '~/types/catalog'

defineProps<{ data: AncillaryOfferProps }>()
const emit = defineEmits<{ add: [option: AncillaryOption] }>()

const added = reactive(new Set<string>())

const ICONS: Record<AncillaryKind, string> = {
  seat: '💺',
  baggage: '🧳',
  meal: '🍽️',
  lounge: '🛋️',
  priority: '⚡',
  insurance: '🛡️',
}
const icon = (kind: AncillaryKind) => ICONS[kind] ?? '➕'

function add(option: AncillaryOption) {
  added.add(option.id)
  emit('add', option)
}
</script>
