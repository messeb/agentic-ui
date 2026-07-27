<template>
  <div>
    <section class="mb-8">
      <h1 class="text-2xl font-bold text-slate-900">Eight ways to build an Agentic UI</h1>
      <p class="mt-2 max-w-2xl text-slate-600">
        A best-in-class demo scaffold. Each card is a <strong>starting point</strong> — the metadata is
        wired end-to-end (shared manifest → FastAPI → Nuxt), but no approach is implemented. Open one
        and press <em>Run demo</em> to see the stubbed <code>501</code> from the backend.
      </p>
    </section>

    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <ApproachCard v-for="a in approaches" :key="a.id" :approach="a" />
    </section>
  </div>
</template>

<script setup lang="ts">
const approaches = useApproaches()
</script>
