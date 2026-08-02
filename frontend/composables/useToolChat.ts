import { ref } from 'vue'
import type { OpenAiMessage, PendingCall, TimelineItem, ToolItem } from '~/types/tools'
import type { WireFrame } from '~/types/wire'

/**
 * Drives the tool-calling agent loop (approach #2). It POSTs the chat-format message
 * list to the backend, consumes the streamed events, and builds a UI timeline. Side-effect
 * tools pause the loop with an `awaiting_permission` event; calling `decide()` resumes it.
 */
export function useToolChat() {
  const apiBase = useRuntimeConfig().public.apiBase
  const items = ref<TimelineItem[]>([])
  const messages = ref<OpenAiMessage[]>([])
  const pending = ref<PendingCall[] | null>(null)
  const streaming = ref(false)
  const error = ref('')
  const wire = ref<WireFrame[]>([])

  interface StreamEvent {
    type: string
    content?: string
    id?: string
    name?: string
    args?: Record<string, unknown>
    side_effect?: boolean
    result?: unknown
    denied?: boolean
    calls?: PendingCall[]
    messages?: OpenAiMessage[]
    message?: string
  }

  function handle(ev: StreamEvent, onUpdate?: () => void) {
    wire.value.push({
      label: String(ev.type),
      body: JSON.stringify(ev),
      kind: ev.type === 'error' ? 'error' : 'stream',
    })
    switch (ev.type) {
      case 'assistant_text':
        items.value.push({ kind: 'assistant_text', content: ev.content ?? '' })
        break
      case 'tool_call':
        items.value.push({
          kind: 'tool',
          id: ev.id!,
          name: ev.name!,
          args: ev.args ?? {},
          sideEffect: !!ev.side_effect,
          status: 'pending',
          result: null,
        })
        break
      case 'tool_result': {
        const item = items.value.find(
          (i): i is ToolItem => i.kind === 'tool' && i.id === ev.id,
        )
        if (item) {
          item.result = ev.result
          item.status = ev.denied ? 'denied' : 'done'
        }
        break
      }
      case 'awaiting_permission':
        pending.value = ev.calls ?? []
        break
      case 'final':
        items.value.push({ kind: 'final', content: ev.content ?? '' })
        break
      case 'state':
        messages.value = ev.messages ?? []
        break
      case 'error':
        error.value = ev.message ?? 'Unknown error'
        break
    }
    onUpdate?.()
  }

  async function run(body: object, onUpdate?: () => void) {
    streaming.value = true
    error.value = ''
    try {
      const res = await fetch(`${apiBase}/api/tools/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
          if (data === '[DONE]') continue
          handle(JSON.parse(data) as StreamEvent, onUpdate)
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

  async function send(text: string, onUpdate?: () => void) {
    const content = text.trim()
    if (!content || streaming.value) return
    pending.value = null
    wire.value = []
    items.value.push({ kind: 'user', content })
    messages.value.push({ role: 'user', content })
    await run({ messages: messages.value }, onUpdate)
  }

  async function decide(approve: boolean, onUpdate?: () => void) {
    if (!pending.value || streaming.value) return
    const approvals: Record<string, boolean> = {}
    for (const call of pending.value) approvals[call.id] = approve
    pending.value = null
    await run({ messages: messages.value, approvals }, onUpdate)
  }

  function reset() {
    items.value = []
    messages.value = []
    pending.value = null
    error.value = ''
    wire.value = []
  }

  return { items, messages, pending, streaming, error, wire, send, decide, reset }
}
