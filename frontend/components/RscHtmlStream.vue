<template>
  <!-- The server-rendered HTML fragments are mounted here as they arrive (insertAdjacentHTML),
       so the page renders progressively. <flight-card> tags upgrade to web components. -->
  <div ref="host" class="space-y-3" />
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps<{ fragments: string[] }>()
const host = ref<HTMLElement | null>(null)
let rendered = 0

function sync() {
  const el = host.value
  if (!el) return
  if (props.fragments.length < rendered) {
    el.innerHTML = '' // a new run reset the fragments
    rendered = 0
  }
  for (let i = rendered; i < props.fragments.length; i++) {
    el.insertAdjacentHTML('beforeend', props.fragments[i])
  }
  rendered = props.fragments.length
}

watch(() => props.fragments.length, () => nextTick(sync))
onMounted(() => nextTick(sync))
</script>
