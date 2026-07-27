<template>
  <div class="flex" :class="isUser ? 'justify-end' : 'justify-start'">
    <div
      class="max-w-[85%] rounded-2xl px-4 py-2.5 text-sm"
      :class="isUser ? 'bg-ink text-white' : 'bg-white border border-slate-200 text-slate-800'"
    >
      <p v-if="isUser" class="whitespace-pre-wrap">{{ message.content }}</p>
      <!-- eslint-disable-next-line vue/no-v-html -- safe: markdown-it runs with html:false so model input is escaped -->
      <div v-else-if="message.content" class="markdown" v-html="rendered" />
      <span v-else class="inline-flex gap-1 py-1" aria-label="Assistant is typing">
        <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400" style="animation-delay:0ms" />
        <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400" style="animation-delay:150ms" />
        <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400" style="animation-delay:300ms" />
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage } from '~/types/chat'

const props = defineProps<{ message: ChatMessage }>()

const isUser = computed(() => props.message.role === 'user')
const rendered = computed(() => renderMarkdown(props.message.content))
</script>

<style scoped>
.markdown :deep(p) { margin: 0.25rem 0; }
.markdown :deep(pre) { margin: 0.5rem 0; padding: 0.75rem; border-radius: 0.5rem; overflow-x: auto; }
.markdown :deep(code) { font-size: 0.85em; }
.markdown :deep(:not(pre) > code) { background: rgba(0,0,0,0.06); padding: 0.1em 0.3em; border-radius: 0.25rem; }
.markdown :deep(ul), .markdown :deep(ol) { margin: 0.25rem 0 0.25rem 1.25rem; list-style: revert; }
.markdown :deep(a) { color: #2563eb; text-decoration: underline; }
</style>
