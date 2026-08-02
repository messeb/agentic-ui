import { ref } from 'vue'
import type { GenFlight, GenResult, RuntimeFunction } from '~/types/generative'
import type { WireFrame } from '~/types/wire'

/**
 * Generative-UI client (approach #4). Fetches the dataset that backs `loadFlights` and asks the
 * backend to GENERATE sandboxed code. Execution happens in the browser sandbox, not here.
 */
export function useGenerativeUi() {
  const apiBase = useRuntimeConfig().public.apiBase
  const flights = ref<GenFlight[]>([])
  const functions = ref<RuntimeFunction[]>([])
  const result = ref<GenResult | null>(null)
  const generating = ref(false)
  const error = ref('')
  const dataError = ref('')
  const wire = ref<WireFrame[]>([])

  async function loadData() {
    try {
      const res = await fetch(`${apiBase}/api/generative/data`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body = await res.json()
      flights.value = body.flights
      functions.value = body.functions
    }
    catch (e) {
      dataError.value = `Could not load data — is the backend running? (${(e as Error).message})`
    }
  }

  async function generate(prompt: string) {
    const value = prompt.trim()
    if (!value || generating.value) return
    generating.value = true
    error.value = ''
    result.value = null
    wire.value = []
    try {
      const res = await fetch(`${apiBase}/api/generative/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: value }),
      })
      if (!res.ok) {
        const detail = await res.json().then(b => b.detail).catch(() => res.statusText)
        throw new Error(detail || `HTTP ${res.status}`)
      }
      const responseObject = (await res.json()) as GenResult
      wire.value.push({ label: 'generate', body: JSON.stringify(responseObject), kind: 'response' })
      result.value = responseObject
    }
    catch (e) {
      error.value = (e as Error).message
    }
    finally {
      generating.value = false
    }
  }

  return { flights, functions, result, generating, error, dataError, wire, loadData, generate }
}
