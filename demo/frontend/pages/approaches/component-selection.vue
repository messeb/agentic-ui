<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#3</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
      <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
        ● Live demo
      </span>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <div class="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
      <ComponentChatPanel class="min-w-0" />

      <aside class="space-y-4 text-sm">
        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">How this works</h2>
          <ol class="mt-2 list-decimal space-y-1 pl-4 text-slate-600">
            <li><strong>Structured Output</strong> constrains the model to your JSON schema.</li>
            <li>It returns component names + <code>props</code> — never markup.</li>
            <li>A renderer maps each to a real, hand-built Vue component.</li>
            <li>The panel (smart wrapper) handles events: cart, selection.</li>
          </ol>
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Component catalog</h2>
          <ul class="mt-2 space-y-2">
            <li v-for="c in catalog" :key="c.name">
              <code class="text-xs font-semibold">{{ c.name }}</code>
              <p class="text-xs text-slate-500">{{ c.description }}</p>
            </li>
          </ul>
          <p v-if="catalogError" class="mt-2 text-xs text-rose-600">{{ catalogError }}</p>
        </div>

        <div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900">
          <h2 class="text-xs font-semibold uppercase tracking-wide">Setup</h2>
          <pre class="mt-2 overflow-x-auto rounded bg-amber-100 p-2 text-xs">export OPENAI_API_KEY=sk-...
make dev-backend</pre>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { CatalogEntry } from '~/types/catalog'

const approach = useApproach('component-selection')

const apiBase = useRuntimeConfig().public.apiBase
const catalog = ref<CatalogEntry[]>([])
const catalogError = ref('')

onMounted(async () => {
  try {
    const res = await fetch(`${apiBase}/api/components`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    catalog.value = (await res.json()).components
  }
  catch (e) {
    catalogError.value = `Could not load the catalog — is the backend running? (${(e as Error).message})`
  }
})
</script>
