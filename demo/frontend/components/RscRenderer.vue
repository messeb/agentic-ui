<template>
  <div class="space-y-3">
    <RscNode v-for="root in roots" :key="root.id" :node="root" :children-map="childrenMap" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RscNode as RscNodeT } from '~/types/rsc'

const props = defineProps<{ nodes: RscNodeT[] }>()

// Group nodes by parent so the tree can render (and grow) as nodes stream in.
const childrenMap = computed(() => {
  const map = new Map<string, RscNodeT[]>()
  for (const n of props.nodes) {
    const key = n.parent ?? '__root__'
    const arr = map.get(key)
    if (arr) arr.push(n)
    else map.set(key, [n])
  }
  return map
})

const roots = computed(() => childrenMap.value.get('__root__') ?? [])
</script>
