<template>
  <div class="space-y-4">
    <!-- composer on top -->
    <form class="flex gap-2" @submit.prevent="submit(input)">
      <input
        v-model="input"
        type="text"
        placeholder="Type a message…"
        class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
        :disabled="streaming"
      >
      <button
        type="submit"
        class="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
        :disabled="streaming || !input.trim()"
      >
        {{ streaming ? '…' : 'Send' }}
      </button>
    </form>

    <div class="flex flex-wrap gap-2">
      <button
        v-for="s in suggestions"
        :key="s"
        class="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
        :disabled="streaming"
        @click="submit(s)"
      >
        {{ s }}
      </button>
      <button
        v-if="messages.length"
        class="ml-auto text-xs text-slate-400 hover:text-slate-700 disabled:opacity-40"
        :disabled="streaming"
        @click="reset"
      >
        Clear
      </button>
    </div>

    <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>

    <!-- conversation flows top-to-bottom -->
    <div v-if="messages.length" class="space-y-3">
      <ChatMessage v-for="(m, i) in messages" :key="i" :message="m" />
      <p v-if="streaming" class="flex items-center gap-1 text-xs text-slate-400">
        <span class="h-2 w-2 animate-pulse rounded-full bg-amber-400" /> streaming…
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const { messages, streaming, error, wire, send, reset } = useChat()

// Expose the raw backend frames so the page can render the <WireInspector> in its side column.
defineExpose({ wire })

const input = ref('')
const suggestions = [
  'Explain SSE vs WebSockets',
  'Write a Python hello world',
  'Give me 3 Markdown tips',
]

async function submit(text: string) {
  const value = text.trim()
  if (!value || streaming.value) return
  input.value = ''
  await send(value)
}
</script>
