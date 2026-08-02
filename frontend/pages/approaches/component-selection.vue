<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#3</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <ApproachIntro
      type="Component selection from a catalog"
      level="★★★☆☆ — the model picks UI, not prose"
      demonstrates="Structured Output constrains the model to choose pre-built components (names + prop values) from a fixed catalog; a renderer instantiates the real, hand-built Vue components — here composed with a live booking call (select a flight → enter a passenger → book, with ancillaries)."
    />

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
      <ComponentChatPanel ref="panel" class="min-w-0" />

      <aside class="min-w-0 space-y-4 text-sm">
        <WireInspector :frames="panel?.wire ?? []" />

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
          <p class="mt-1 text-xs text-slate-500">
            The model may only pick from these pre-built components — it supplies their props but can't
            invent markup. Try “flights from Graz to Hamburg”, then select one to book.
          </p>
          <ul class="mt-2 space-y-2">
            <li v-for="c in catalog" :key="c.name">
              <code class="text-xs font-semibold">{{ c.name }}</code>
              <p class="text-xs text-slate-500">{{ c.description }}</p>
            </li>
          </ul>
          <p v-if="catalogError" class="mt-2 text-xs text-rose-600">{{ catalogError }}</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ComponentChatPanel from '~/components/ComponentChatPanel.vue'
import type { CatalogEntry } from '~/types/catalog'

const approach = useApproach('component-selection')

const panel = ref<InstanceType<typeof ComponentChatPanel> | null>(null)

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
