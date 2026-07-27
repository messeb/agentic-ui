<template>
  <div class="flex h-[70vh] flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
    <div class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2.5">
      <div class="flex items-center gap-2">
        <span class="h-2 w-2 rounded-full bg-emerald-500" />
        <span class="text-sm font-semibold">Flight agent</span>
        <span class="text-xs text-slate-400">tool calling · ReAct loop</span>
      </div>
      <button
        class="text-xs text-slate-500 hover:text-slate-900 disabled:opacity-40"
        :disabled="streaming || !items.length"
        @click="reset"
      >
        Clear
      </button>
    </div>

    <div ref="el" class="flex-1 space-y-3 overflow-y-auto p-4" @scroll="onScroll">
      <div v-if="!items.length" class="grid h-full place-items-center text-center text-sm text-slate-400">
        <div>
          <p class="mb-3">Ask the agent to search or book flights. It will call tools and show its work.</p>
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

      <template v-for="(item, i) in items" :key="i">
        <div v-if="item.kind === 'user'" class="flex justify-end">
          <div class="max-w-[85%] rounded-2xl bg-ink px-4 py-2.5 text-sm text-white">{{ item.content }}</div>
        </div>
        <!-- eslint-disable-next-line vue/no-v-html -- markdown-it html:false escapes model input -->
        <div v-else-if="item.kind === 'assistant_text'" class="markdown max-w-[85%] text-sm text-slate-500 italic" v-html="md(item.content)" />
        <ToolCallCard v-else-if="item.kind === 'tool'" :item="item" />
        <!-- eslint-disable-next-line vue/no-v-html -- markdown-it html:false escapes model input -->
        <div v-else-if="item.kind === 'final'" class="markdown max-w-[85%] rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-800" v-html="md(item.content)" />
      </template>

      <!-- permission gate -->
      <div v-if="pending" class="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm">
        <p class="font-medium text-amber-900">⚠️ The agent wants to run a side-effect action:</p>
        <ul class="mt-1 space-y-1">
          <li v-for="c in pending" :key="c.id">
            <code class="text-amber-900">{{ c.name }}({{ argsText(c.args) }})</code>
          </li>
        </ul>
        <div class="mt-3 flex gap-2">
          <button
            class="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:opacity-90"
            :disabled="streaming"
            @click="decide(true, () => scrollToBottom())"
          >
            Approve
          </button>
          <button
            class="rounded-md bg-rose-600 px-3 py-1.5 text-xs font-medium text-white hover:opacity-90"
            :disabled="streaming"
            @click="decide(false, () => scrollToBottom())"
          >
            Deny
          </button>
        </div>
      </div>

      <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
    </div>

    <!-- predefined prompts, shown after every exchange -->
    <div v-if="items.length" class="flex flex-wrap gap-2 border-t border-slate-200 bg-white px-3 pt-2">
      <button
        v-for="s in suggestions"
        :key="s"
        class="rounded-full border border-slate-300 px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
        :disabled="streaming || !!pending"
        @click="submit(s)"
      >
        {{ s }}
      </button>
    </div>

    <form class="flex gap-2 border-t border-slate-200 bg-white p-3" @submit.prevent="submit(input)">
      <input
        v-model="input"
        type="text"
        placeholder="e.g. Find flights from Graz to Hamburg"
        class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
        :disabled="streaming || !!pending"
      >
      <button
        type="submit"
        class="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
        :disabled="streaming || !!pending || !input.trim()"
      >
        {{ streaming ? '…' : 'Send' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const { items, pending, streaming, error, send, decide, reset } = useToolChat()
const { el, onScroll, scrollToBottom } = useAutoScroll()

const input = ref('')
const suggestions = [
  'Find flights from Graz to Hamburg',
  'Book the cheapest Graz→Hamburg flight for Alice',
  'Show my bookings',
]

const md = (s: string) => renderMarkdown(s)
const argsText = (args: Record<string, unknown>) =>
  Object.entries(args).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(', ')

async function submit(text: string) {
  const value = text.trim()
  if (!value || streaming.value || pending.value) return
  input.value = ''
  await nextTick(() => scrollToBottom(true))
  await send(value, () => scrollToBottom())
}

watch(items, () => nextTick(() => scrollToBottom()), { deep: true })
</script>
