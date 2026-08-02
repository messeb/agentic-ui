<template>
  <div v-if="approach">
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#{{ approach.number }}</span>
      <h1 class="text-2xl font-bold">{{ approach.title }}</h1>
      <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="maturityClass(approach.maturity)">
        {{ maturityLabel(approach.maturity) }}
      </span>
    </header>
    <p class="mt-1 text-slate-600">{{ approach.tagline }}</p>

    <div class="mt-6 grid gap-4 sm:grid-cols-2">
      <div class="rounded-lg border border-slate-200 bg-white p-4">
        <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Input</h2>
        <p class="mt-1">{{ approach.input }}</p>
      </div>
      <div class="rounded-lg border border-slate-200 bg-white p-4">
        <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Output</h2>
        <p class="mt-1">{{ approach.output }}</p>
      </div>
    </div>

    <div class="mt-4 rounded-lg border border-slate-200 bg-white p-4">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">How it works</h2>
      <p class="mt-1">{{ approach.howItWorks }}</p>
    </div>

    <div class="mt-4 rounded-lg border border-slate-200 bg-white p-4">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">What you need</h2>
      <ul class="mt-2 flex flex-wrap gap-2">
        <li
          v-for="need in approach.whatYouNeed"
          :key="need"
          class="rounded bg-slate-100 px-2 py-1 text-sm text-slate-700"
        >
          {{ need }}
        </li>
      </ul>
    </div>

    <section class="mt-6 rounded-lg border border-dashed border-slate-300 bg-white p-4">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold">Live demo</h2>
        <button
          class="rounded-md bg-ink px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          :disabled="loading"
          @click="runDemo"
        >
          {{ loading ? 'Calling backend…' : 'Run demo' }}
        </button>
      </div>
      <p class="mt-2 text-sm text-slate-500">
        This calls <code>{{ apiBase }}/api/approaches/{{ approach.id }}/demo</code>. The backend returns
        <code>501 Not Implemented</code> on purpose — implement it in
        <code>backend/…/routers/approaches.py</code> and this page.
      </p>
      <pre
        v-if="result"
        class="mt-3 overflow-x-auto rounded bg-slate-900 p-3 text-xs text-slate-100"
      >{{ result }}</pre>
    </section>
  </div>

  <div v-else class="text-slate-600">
    Unknown approach. <NuxtLink to="/" class="underline">Back to the list.</NuxtLink>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const approach = useApproach(route.params.id as string)

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const loading = ref(false)
const result = ref<string>('')

async function runDemo() {
  if (!approach) return
  loading.value = true
  result.value = ''
  try {
    const res = await fetch(`${apiBase}/api/approaches/${approach.id}/demo`)
    const body = await res.json()
    result.value = `HTTP ${res.status}\n\n${JSON.stringify(body, null, 2)}`
  } catch (err) {
    result.value = `Request failed: ${(err as Error).message}\n\nIs the backend running on ${apiBase}?`
  } finally {
    loading.value = false
  }
}
</script>
