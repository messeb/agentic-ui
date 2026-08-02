import { fileURLToPath } from 'node:url'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },

  modules: ['@nuxtjs/tailwindcss', '@nuxt/eslint'],

  // This demo doesn't use route rules / payload extraction; disabling the app manifest
  // avoids the dev-server "#app-manifest" resolve error and keeps the build lean.
  experimental: { appManifest: false },

  // Code-highlighting theme for streamed Markdown (approach #1).
  css: ['highlight.js/styles/github-dark.css'],

  // Vendored manifest (kept in sync with shared/approaches.json via `make sync-manifest`).
  alias: {
    '@shared': fileURLToPath(new URL('./shared', import.meta.url)),
  },

  runtimeConfig: {
    public: {
      // Base URL of the FastAPI backend. Override with NUXT_PUBLIC_API_BASE.
      apiBase: 'http://localhost:8000',
    },
  },

  app: {
    head: {
      title: 'Agentic UI Patterns',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        {
          name: 'description',
          content: 'A scaffolded demo of the 8 Agentic UI approaches. Starting point, not implementations.',
        },
      ],
    },
  },
})
