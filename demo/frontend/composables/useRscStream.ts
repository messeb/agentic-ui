import { ref } from 'vue'
import type { RscNode, RscToolInfo } from '~/types/rsc'

/**
 * Server-streamed UI client (approach #5). The server picks a component (tool call), serializes
 * it into a node tree, and streams the nodes; we append them so the UI renders progressively.
 * The tree is ephemeral — a new request resets it.
 */
export function useRscStream() {
  const apiBase = useRuntimeConfig().public.apiBase
  const nodes = ref<RscNode[]>([])
  const tools = ref<RscToolInfo[]>([])
  const streaming = ref(false)
  const done = ref(false)
  const error = ref('')

  async function stream(prompt: string) {
    const value = prompt.trim()
    if (!value || streaming.value) return
    nodes.value = []
    tools.value = []
    done.value = false
    error.value = ''
    streaming.value = true
    try {
      const res = await fetch(`${apiBase}/api/rsc/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: value }),
      })
      if (!res.ok || !res.body) {
        const detail = await res.json().then(b => b.detail).catch(() => res.statusText)
        throw new Error(detail || `HTTP ${res.status}`)
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { done: finished, value: chunk } = await reader.read()
        if (finished) break
        buffer += decoder.decode(chunk, { stream: true })
        const frames = buffer.split('\n\n')
        buffer = frames.pop() ?? ''
        for (const frame of frames) {
          const line = frame.trim()
          if (!line.startsWith('data:')) continue
          const data = line.slice(5).trim()
          if (data === '[DONE]') continue
          const ev = JSON.parse(data)
          if (ev.type === 'tool') tools.value.push({ name: ev.name, args: ev.args })
          else if (ev.type === 'node') nodes.value.push({ id: ev.id, parent: ev.parent, comp: ev.comp, props: ev.props })
          else if (ev.type === 'done') done.value = true
          else if (ev.type === 'error') error.value = ev.message
        }
      }
    }
    catch (e) {
      error.value = (e as Error).message
    }
    finally {
      streaming.value = false
    }
  }

  function reset() {
    nodes.value = []
    tools.value = []
    done.value = false
    error.value = ''
  }

  return { nodes, tools, streaming, done, error, stream, reset }
}
