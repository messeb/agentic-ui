import { ref } from 'vue'
import type { AncillaryOption, CartSummaryProps, UiComponent, UiDocument } from '~/types/catalog'
import type { WireFrame } from '~/types/wire'

export interface UserItem {
  kind: 'user'
  content: string
}
export interface DocItem {
  kind: 'doc'
  message: string
  components: UiComponent[]
}
export interface NoteItem {
  kind: 'note'
  content: string
}
export type CatalogTimelineItem = UserItem | DocItem | NoteItem

/**
 * Component-selection client (approach #3). Sends user intent to the backend, which uses
 * Structured Output to return a UI document (message + selected components with props).
 */
export function useComponentChat() {
  const apiBase = useRuntimeConfig().public.apiBase
  const items = ref<CatalogTimelineItem[]>([])
  const messages = ref<Array<{ role: string, content: string }>>([])
  const cart = ref<AncillaryOption[]>([])
  const loading = ref(false)
  const error = ref('')
  const wire = ref<WireFrame[]>([])

  async function postDoc(path: string, body: object): Promise<UiDocument | null> {
    loading.value = true
    error.value = ''
    try {
      const res = await fetch(`${apiBase}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const detail = await res.json().then(b => b.detail).catch(() => res.statusText)
        throw new Error(detail || `HTTP ${res.status}`)
      }
      const doc = (await res.json()) as UiDocument
      wire.value.push({ label: `POST ${path}`, body: JSON.stringify(doc), kind: 'response' })
      items.value.push({ kind: 'doc', message: doc.message, components: doc.components })
      return doc
    }
    catch (e) {
      error.value = (e as Error).message
      return null
    }
    finally {
      loading.value = false
    }
  }

  async function send(text: string) {
    const content = text.trim()
    if (!content || loading.value) return
    error.value = ''
    wire.value = []
    items.value.push({ kind: 'user', content })
    messages.value.push({ role: 'user', content })
    loading.value = true
    try {
      const res = await fetch(`${apiBase}/api/components/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: messages.value }),
      })
      if (!res.ok) {
        const detail = await res.json().then(b => b.detail).catch(() => res.statusText)
        throw new Error(detail || `HTTP ${res.status}`)
      }
      const doc = (await res.json()) as UiDocument
      wire.value.push({ label: 'structured-output', body: JSON.stringify(doc), kind: 'response' })
      items.value.push({ kind: 'doc', message: doc.message, components: doc.components })
      messages.value.push({ role: 'assistant', content: doc.message })
    }
    catch (e) {
      error.value = (e as Error).message
    }
    finally {
      loading.value = false
    }
  }

  // Real backend action: add an ancillary to the shared server cart.
  async function addAncillary(option: AncillaryOption) {
    const doc = await postDoc('/api/components/ancillary', option)
    const summary = doc?.components.find(c => c.component === 'cart_summary')
    if (summary) cart.value = (summary.props as CartSummaryProps).items
  }

  // Real backend action: book a flight with the cart's ancillaries (server clears the cart).
  async function book(flightId: string, passenger: string) {
    const doc = await postDoc('/api/components/book', { flight_id: flightId, passenger })
    if (doc) cart.value = []
  }

  function note(content: string) {
    items.value.push({ kind: 'note', content })
  }

  function reset() {
    items.value = []
    messages.value = []
    cart.value = []
    error.value = ''
    wire.value = []
  }

  return { items, cart, loading, error, wire, send, addAncillary, book, note, reset }
}
