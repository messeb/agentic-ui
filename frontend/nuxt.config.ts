import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },

  modules: ['@nuxt/eslint'],

  // Tailwind CSS v4 via its official Vite plugin (the @nuxtjs/tailwindcss module is v3-only).
  vite: { plugins: [tailwindcss()] },

  // This demo doesn't use route rules / payload extraction; disabling the app manifest
  // avoids the dev-server "#app-manifest" resolve error and keeps the build lean.
  experimental: { appManifest: false },

  // Tailwind entry (defines the `ink` theme color) + code-highlighting theme for streamed Markdown (#1).
  css: ['~/assets/css/tailwind.css', 'highlight.js/styles/github-dark.css'],

  // Approaches manifest (frontend/shared/approaches.json), imported via the @shared alias.
  alias: {
    '@shared': fileURLToPath(new URL('./shared', import.meta.url)),
  },

  runtimeConfig: {
    public: {
      // Base URL of the FastAPI backend. Override with NUXT_PUBLIC_API_BASE.
      // In single-port mode set it to '' so the browser calls same-origin /api (see routeRules).
      apiBase: 'http://localhost:8000',
    },
  },

  // Single-port mode: when the app is served on one port (the all-in-one container), the browser
  // hits same-origin /api and the Nuxt server proxies it to the co-located backend. Harmless in
  // dev/compose (the frontend calls the backend directly via apiBase there, not same-origin /api).
  routeRules: {
    '/api/**': { proxy: 'http://127.0.0.1:8000/api/**' },
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
