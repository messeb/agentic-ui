<template>
  <div class="space-y-4">
    <!-- composer on top -->
    <form class="flex gap-2" @submit.prevent="submit(input)">
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

    <div class="flex flex-wrap gap-2">
      <button
        v-for="s in suggestions"
        :key="s"
        class="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
        :disabled="streaming || !!pending"
        @click="submit(s)"
      >
        {{ s }}
      </button>
      <button
        v-if="items.length"
        class="ml-auto text-xs text-slate-400 hover:text-slate-700 disabled:opacity-40"
        :disabled="streaming"
        @click="reset"
      >
        Clear
      </button>
    </div>

    <!-- the agent's work flows top-to-bottom -->
    <div v-if="items.length || pending || error" class="space-y-3">
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
            @click="decide(true)"
          >
            Approve
          </button>
          <button
            class="rounded-md bg-rose-600 px-3 py-1.5 text-xs font-medium text-white hover:opacity-90"
            :disabled="streaming"
            @click="decide(false)"
          >
            Deny
          </button>
        </div>
      </div>

      <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const { items, pending, streaming, error, wire, send, decide, reset } = useToolChat()

// Expose the raw backend frames so the page can render the <WireInspector> in its side column.
defineExpose({ wire })

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
  await send(value)
}
</script>
