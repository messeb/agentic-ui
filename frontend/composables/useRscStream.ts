import { ref } from 'vue'
import type { RscToolInfo } from '~/types/rsc'
import type { WireFrame } from '~/types/wire'

/**
 * Server-streamed UI client (approach #5). The server renders each component to a REAL HTML
 * fragment (flight cards are `<flight-card>` web components) and streams the fragments; we collect
 * them so the view can mount each progressively. The result is ephemeral — a new request resets it.
 */
export function useRscStream() {
  const apiBase = useRuntimeConfig().public.apiBase
  const fragments = ref<string[]>([])
  const tools = ref<RscToolInfo[]>([])
  const streaming = ref(false)
  const done = ref(false)
  const error = ref('')
  const wire = ref<WireFrame[]>([])

  async function stream(prompt: string) {
    const value = prompt.trim()
    if (!value || streaming.value) return
    fragments.value = []
    tools.value = []
    done.value = false
    error.value = ''
    wire.value = []
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
          wire.value.push({ label: String(ev.type), body: data, kind: ev.type === 'error' ? 'error' : 'stream' })
          if (ev.type === 'tool') tools.value.push({ name: ev.name, args: ev.args })
          else if (ev.type === 'html') fragments.value.push(ev.html)
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
    fragments.value = []
    tools.value = []
    done.value = false
    error.value = ''
    wire.value = []
  }

  return { fragments, tools, streaming, done, error, wire, stream, reset }
}
