<template>
  <div>
    <NuxtLink to="/" class="text-sm text-slate-500 hover:text-slate-900">← All approaches</NuxtLink>

    <header class="mt-4 flex flex-wrap items-center gap-3">
      <span class="text-sm font-mono text-slate-400">#4</span>
      <h1 class="text-2xl font-bold">{{ approach?.title }}</h1>
    </header>
    <p class="mt-1 text-slate-600">{{ approach?.tagline }}</p>

    <ApproachIntro
      type="Generative UI via sandboxed code"
      level="★★★★☆ — the model writes the UI"
      demonstrates="The model generates JavaScript that renders arbitrary UI (table, chart, cards…), executed in a locked-down iframe — sandbox='allow-scripts' with no same-origin, and a CSP that blocks all network. Data reaches it only through a postMessage→loadFlights bridge; the backend never runs the code."
    />

    <div class="mt-6 grid gap-6 lg:grid-cols-2">
      <div class="min-w-0 space-y-4">
        <!-- prompt -->
        <form class="flex gap-2" @submit.prevent="submit(prompt)">
          <input
            v-model="prompt"
            type="text"
            placeholder="e.g. Average price per destination"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            :disabled="generating"
          >
          <button
            type="submit"
            class="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
            :disabled="generating || !prompt.trim()"
          >
            {{ generating ? 'Generating…' : 'Generate' }}
          </button>
        </form>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="s in suggestions"
            :key="s"
            class="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
            :disabled="generating"
            @click="submit(s)"
          >
            {{ s }}
          </button>
        </div>

        <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
        <p v-if="dataError" class="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">{{ dataError }}</p>

        <!-- generated code -->
        <div v-if="result" class="space-y-3">
          <p class="text-sm text-slate-600">
            <span class="font-medium">{{ result.status === 'success' ? '✅' : '⚠️' }} {{ result.message }}</span>
          </p>
          <div class="min-w-0">
            <h2 class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Generated code</h2>
            <!-- eslint-disable-next-line vue/no-v-html -- highlight.js output of model code shown read-only -->
            <div class="code-block text-sm" v-html="renderedCode" />
          </div>

          <div v-if="result.status === 'success'">
            <h2 class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Sandbox output</h2>
            <SandboxRunner :code="result.code" :flights="flights" />
          </div>
        </div>
      </div>

      <aside class="min-w-0 space-y-4 text-sm">
        <WireInspector :frames="wire" />

        <div class="rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-900">
          <h2 class="text-xs font-semibold uppercase tracking-wide">Sandbox contract</h2>
          <ul class="mt-2 space-y-1 text-xs">
            <li>🔒 <code>iframe sandbox="allow-scripts"</code> — <strong>no</strong> <code>allow-same-origin</code> → opaque origin, no host DOM/cookies.</li>
            <li>🚫 CSP <code>connect-src 'none'</code> — no fetch/XHR/WebSocket; no external URLs.</li>
            <li>🧭 no top-navigation, forms, or popups.</li>
            <li>🎨 the code renders <strong>any</strong> UI into its own DOM (table, chart, cards…) — isolation makes that safe.</li>
            <li>📨 gets data only via <code>postMessage</code> → <code>loadFlights</code>.</li>
          </ul>
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <h2 class="text-xs font-semibold uppercase tracking-wide text-slate-500">Runtime functions</h2>
          <p class="mt-1 text-xs text-slate-500">
            The generated code runs in the sandbox and may only call these whitelisted functions —
            everything else (network, imports) is blocked. Try “flights per destination as a pie chart”.
          </p>
          <ul class="mt-2 space-y-2">
            <li v-for="f in functions" :key="f.name">
              <code class="text-xs font-semibold">{{ f.name }}</code>
              <span class="text-[10px] text-slate-400"> · {{ f.kind }}</span>
              <p class="text-xs text-slate-500">{{ f.description }}</p>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const approach = useApproach('sandboxed-code')
const { flights, functions, result, generating, error, dataError, wire, loadData, generate } = useGenerativeUi()

const prompt = ref('')
const suggestions = [
  'Flights per destination as a pie chart',
  'A table of flights sorted by price',
  'Average price per destination as a bar chart',
  'Cards for each delayed flight',
]

const renderedCode = computed(() =>
  result.value ? renderMarkdown(`\`\`\`js\n${result.value.code}\n\`\`\``) : '',
)

async function submit(text: string) {
  const value = text.trim()
  if (!value || generating.value) return
  prompt.value = value
  await generate(value)
}

onMounted(loadData)
</script>

<style scoped>
/* Fixed-width code block: never let long lines widen the column — scroll instead. */
.code-block :deep(pre) {
  margin: 0;
  max-width: 100%;
  max-height: 340px;
  overflow: auto;
  padding: 0.75rem;
  border-radius: 0.5rem;
}
.code-block :deep(code) {
  white-space: pre;
  font-size: 0.8rem;
}
</style>
