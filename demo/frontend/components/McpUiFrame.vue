<template>
  <div>
    <div class="mb-1 flex items-center gap-2 text-xs text-slate-400">
      <span>🪟 MCP-UI resource</span>
      <code class="rounded bg-slate-100 px-1 py-0.5 text-slate-500">{{ resource.uri }}</code>
    </div>
    <iframe
      ref="frame"
      sandbox="allow-scripts"
      :srcdoc="resource.text"
      title="mcp-ui resource"
      class="block w-full rounded-lg border border-slate-200 bg-white"
      style="height: 132px"
    />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { McpUiIntent, UiResource } from '~/types/protocol'

defineProps<{ resource: UiResource }>()
const emit = defineEmits<{ intent: [intent: McpUiIntent] }>()

const frame = ref<HTMLIFrameElement | null>(null)

// The ui:// resource runs in a sandboxed iframe (opaque origin, CSP) and talks back only via
// postMessage — exactly the MCP-UI contract.
function onMessage(e: MessageEvent) {
  if (!frame.value || e.source !== frame.value.contentWindow) return
  const msg = e.data || {}
  if (msg.type === 'mcp-ui:intent') emit('intent', { tool: String(msg.tool), args: msg.args ?? {} })
}

onMounted(() => window.addEventListener('message', onMessage))
onBeforeUnmount(() => window.removeEventListener('message', onMessage))
</script>
