<template>
  <header class="border-b border-slate-200 bg-white">
    <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
      <NuxtLink to="/" class="flex items-center gap-2 font-semibold">
        <span class="text-xl">🧭</span>
        <span>Agentic UI — 8 Approaches</span>
      </NuxtLink>
      <a
        href="https://github.com"
        class="text-sm text-slate-500 hover:text-slate-900"
        target="_blank"
        rel="noopener"
      >
        Demo scaffold · v{{ version }}
      </a>
    </div>
  </header>
</template>

<script setup lang="ts">
const version = useManifestVersion()
</script>
