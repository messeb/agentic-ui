import { ref, toRaw } from 'vue'
import type { PatchOp, ProtoEvent, ProtocolInfo, ToolCallView, UiResource } from '~/types/protocol'

/** Apply an RFC-6902 JSON Patch (add/replace/remove subset) — used by STATE_DELTA. */
function applyPatch(target: Record<string, unknown>, ops: PatchOp[]) {
  for (const op of ops) {
    const keys = op.path.split('/').slice(1).map(k => k.replace(/~1/g, '/').replace(/~0/g, '~'))
    const last = keys.pop()
    if (last === undefined) continue
    let node: Record<string, unknown> = target
    for (const k of keys) node = node[k] as Record<string, unknown>
    if (op.op === 'remove') {
      if (Array.isArray(node)) node.splice(Number(last), 1)
      else Reflect.deleteProperty(node, last)
    }
    else {
      if (Array.isArray(node) && last === '-') node.push(op.value)
      else node[last] = op.value
    }
  }
}

/**
 * AG-UI client (approach #8). The UI is a pure function of the typed event stream: this consumes
 * lifecycle / text / tool-call / state events, assembles message text, tool calls, and app state
 * (STATE_SNAPSHOT + STATE_DELTA via JSON Patch), and collects MCP-UI ui:// resources to render.
 * Swap the backend — as long as it speaks AG-UI, this client is unchanged.
 */
export function useProtocol() {
  const apiBase = useRuntimeConfig().public.apiBase
  const info = ref<ProtocolInfo | null>(null)
  const events = ref<ProtoEvent[]>([])
  const text = ref('')
  const toolCalls = ref<ToolCallView[]>([])
  const state = ref<Record<string, unknown> | null>(null)
  const resources = ref<UiResource[]>([])
  const runId = ref('')
  const threadId = ref('')
  const running = ref(false)
  const error = ref('')

  async function loadInfo() {
    try {
      const res = await fetch(`${apiBase}/api/protocol/info`)
      if (res.ok) info.value = await res.json()
    }
    catch { /* legend is optional */ }
  }

  function handle(ev: ProtoEvent) {
    events.value.push(ev)
    switch (ev.type) {
      case 'RUN_STARTED':
        runId.value = String(ev.runId ?? '')
        threadId.value = String(ev.threadId ?? '')
        break
      case 'TEXT_MESSAGE_CONTENT':
        text.value += String(ev.delta ?? '')
        break
      case 'TOOL_CALL_START':
        toolCalls.value.push({ id: String(ev.toolCallId), name: String(ev.toolCallName), args: '', result: null })
        break
      case 'TOOL_CALL_ARGS': {
        const tc = toolCalls.value.find(t => t.id === ev.toolCallId)
        if (tc) tc.args += String(ev.delta ?? '')
        break
      }
      case 'TOOL_CALL_RESULT': {
        const tc = toolCalls.value.find(t => t.id === ev.toolCallId)
        if (tc) tc.result = ev.content
        const content = ev.content as { type?: string, resource?: UiResource } | undefined
        if (content?.type === 'resource' && content.resource) resources.value.push(content.resource)
        break
      }
      case 'STATE_SNAPSHOT':
        state.value = structuredClone(ev.snapshot as Record<string, unknown>)
        break
      case 'STATE_DELTA': {
        // state.value is a Vue reactive Proxy (Vue wraps object ref values); structuredClone can't
        // clone a Proxy → DataCloneError. Clone the raw target instead.
        const next = structuredClone(toRaw(state.value) ?? {})
        applyPatch(next, ev.delta as PatchOp[])
        state.value = next
        break
      }
    }
  }

  async function run(prompt: string) {
    const value = prompt.trim()
    if (!value || running.value) return
    events.value = []
    text.value = ''
    toolCalls.value = []
    state.value = null
    resources.value = []
    error.value = ''
    running.value = true
    try {
      const res = await fetch(`${apiBase}/api/protocol/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: value, thread_id: threadId.value || undefined }),
      })
      if (!res.ok || !res.body) {
        const detail = await res.json().then(b => b.detail).catch(() => res.statusText)
        throw new Error(detail || `HTTP ${res.status}`)
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { done, value: chunk } = await reader.read()
        if (done) break
        buffer += decoder.decode(chunk, { stream: true })
        const frames = buffer.split('\n\n')
        buffer = frames.pop() ?? ''
        for (const frame of frames) {
          const line = frame.trim()
          if (!line.startsWith('data:')) continue
          const data = line.slice(5).trim()
          if (data === '[DONE]') continue
          handle(JSON.parse(data) as ProtoEvent)
        }
      }
    }
    catch (e) {
      error.value = (e as Error).message
    }
    finally {
      running.value = false
    }
  }

  return { info, events, text, toolCalls, state, resources, runId, threadId, running, error, loadInfo, run }
}
