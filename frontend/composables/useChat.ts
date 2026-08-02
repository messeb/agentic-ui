import { ref } from 'vue'
import type { ChatMessage } from '~/types/chat'
import type { WireFrame } from '~/types/wire'

/**
 * Streaming chat client for approach #1. POSTs the conversation to the backend proxy
 * and consumes the Server-Sent Events stream, appending token deltas to the last message.
 */
export function useChat() {
  const apiBase = useRuntimeConfig().public.apiBase
  const messages = ref<ChatMessage[]>([])
  const streaming = ref(false)
  const error = ref('')
  const wire = ref<WireFrame[]>([])

  async function send(text: string, onToken?: () => void) {
    const content = text.trim()
    if (!content || streaming.value) return

    error.value = ''
    wire.value = []
    messages.value.push({ role: 'user', content })
    const payload = messages.value.map(m => ({ role: m.role, content: m.content }))
    messages.value.push({ role: 'assistant', content: '' })
    const index = messages.value.length - 1
    streaming.value = true

    try {
      const res = await fetch(`${apiBase}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: payload }),
      })

      if (!res.ok || !res.body) {
        const detail = await res.json().then(b => b.detail).catch(() => res.statusText)
        throw new Error(detail || `HTTP ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const frames = buffer.split('\n\n')
        buffer = frames.pop() ?? ''
        for (const frame of frames) {
          const line = frame.trim()
          if (!line.startsWith('data:')) continue
          const data = line.slice(5).trim()
          if (data === '[DONE]') {
            wire.value.push({ label: 'done', body: '[DONE]', kind: 'stream' })
            continue
          }
          const json = JSON.parse(data) as { type?: string, delta?: string, error?: string }
          wire.value.push({ label: json.type ?? 'data', body: data, kind: 'stream' })
          if (json.error) error.value = json.error
          if (json.delta) {
            messages.value[index].content += json.delta
            onToken?.()
          }
        }
      }
    }
    catch (e) {
      error.value = (e as Error).message
    }
    finally {
      streaming.value = false
      // Drop the empty assistant bubble if nothing came back (e.g. error).
      if (!messages.value[index]?.content) messages.value.splice(index, 1)
    }
  }

  function reset() {
    messages.value = []
    error.value = ''
  }

  return { messages, streaming, error, wire, send, reset }
}
