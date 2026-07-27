<template>
  <div class="flex h-[70vh] flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
    <!-- header -->
    <div class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2.5">
      <div class="flex items-center gap-2">
        <span class="h-2 w-2 rounded-full bg-emerald-500" />
        <span class="text-sm font-semibold">Assistant</span>
        <span class="text-xs text-slate-400">streaming · SSE</span>
      </div>
      <button
        class="text-xs text-slate-500 hover:text-slate-900 disabled:opacity-40"
        :disabled="streaming || !messages.length"
        @click="reset"
      >
        Clear
      </button>
    </div>

    <!-- messages -->
    <div
      ref="el"
      class="flex-1 space-y-3 overflow-y-auto p-4"
      @scroll="onScroll"
    >
      <div v-if="!messages.length" class="grid h-full place-items-center text-center text-sm text-slate-400">
        <div>
          <p class="mb-3">Ask anything — answers stream in as Markdown.</p>
          <div class="flex flex-wrap justify-center gap-2">
            <button
              v-for="s in suggestions"
              :key="s"
              class="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-600 hover:border-slate-500"
              @click="submit(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>
      </div>

      <ChatMessage v-for="(m, i) in messages" :key="i" :message="m" />

      <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
        {{ error }}
      </p>
    </div>

    <!-- composer -->
    <form class="flex gap-2 border-t border-slate-200 bg-white p-3" @submit.prevent="submit(input)">
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
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const { messages, streaming, error, send, reset } = useChat()
const { el, onScroll, scrollToBottom } = useAutoScroll()

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
  await nextTick(() => scrollToBottom(true))
  await send(value, () => scrollToBottom())
}

// Keep pinned to the bottom as tokens stream in (respecting user scroll-up).
watch(messages, () => nextTick(() => scrollToBottom()), { deep: true })
</script>
