import { computed, reactive, ref } from 'vue'
import type { AgentFlight, AppState, LogEntry, ToolCall } from '~/types/agent'

const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

function initialState(): AppState {
  return {
    step: 'search',
    form: { origin: '', destination: '', date: '', passengers: '1', cabin: 'economy' },
    filters: { max_price: null, morning_only: false, direct_only: false },
    sort: null,
    selectedFlightId: null,
    booked: false,
  }
}

/**
 * The agentic frontend store (approach #7). Holds reactive app state, derives the visible flight
 * list (deterministic, client-side), serializes state for the prompt, and runs the agent loop:
 * post goal+state → apply each returned tool call as a state patch → re-post until done. `book`
 * is gated by a human-in-the-loop confirmation. Every applied patch announces via aria-live.
 */
export function useAgentApp() {
  const apiBase = useRuntimeConfig().public.apiBase
  const state = reactive<AppState>(initialState())
  const flights = ref<AgentFlight[]>([])
  const log = ref<LogEntry[]>([])
  const running = ref(false)
  const pendingBook = ref(false)
  const error = ref('')
  const live = ref('') // aria-live announcement
  const highlight = ref('') // e.g. 'form.destination' | 'results' | 'review'
  const goal = ref('')

  async function loadData() {
    try {
      const res = await fetch(`${apiBase}/api/agent/data`)
      if (res.ok) flights.value = (await res.json()).flights
    }
    catch {
      // best effort
    }
  }

  const visibleFlights = computed(() => {
    let arr = flights.value.filter(f =>
      (!state.form.origin || f.origin.toLowerCase() === state.form.origin.toLowerCase())
      && (!state.form.destination || f.destination.toLowerCase() === state.form.destination.toLowerCase()),
    )
    if (state.filters.max_price != null) arr = arr.filter(f => f.price <= state.filters.max_price!)
    if (state.filters.morning_only) arr = arr.filter(f => Number(f.departure_time.slice(0, 2)) < 12)
    if (state.filters.direct_only) arr = arr.filter(f => f.stops === 0)
    if (state.sort === 'price') arr = [...arr].sort((a, b) => a.price - b.price)
    else if (state.sort === 'duration') arr = [...arr].sort((a, b) => a.duration_min - b.duration_min)
    return arr
  })

  function serialize() {
    return {
      step: state.step,
      form: { ...state.form },
      filters: { ...state.filters },
      sort: state.sort,
      selected_flight_id: state.selectedFlightId,
      booked: state.booked,
      visible_flights: visibleFlights.value.map(f => ({
        id: f.id, price: f.price, duration_min: f.duration_min,
        stops: f.stops, departure_time: f.departure_time,
      })),
    }
  }

  function announce(message: string) {
    live.value = ''
    // toggle so identical consecutive messages are still announced
    requestAnimationFrame(() => { live.value = message })
  }

  function flash(key: string | undefined) {
    if (!key) return
    highlight.value = key
    setTimeout(() => { if (highlight.value === key) highlight.value = '' }, 900)
  }

  const s = (v: unknown) => String(v ?? '')

  // Generic dispatcher: tool name → state patch. Adding a tool = one entry here.
  function apply(call: ToolCall): { desc: string, highlight?: string, finish?: boolean } | null {
    const a = call.args
    switch (call.name) {
      case 'update_form': {
        const field = s(a.field) as keyof AppState['form']
        state.form[field] = s(a.value)
        return { desc: `Set ${field} = “${s(a.value)}”`, highlight: `form.${field}` }
      }
      case 'set_filter': {
        const filter = s(a.filter)
        if (filter === 'max_price') state.filters.max_price = Number(a.value)
        else if (filter === 'morning_only') state.filters.morning_only = s(a.value) === 'true'
        else if (filter === 'direct_only') state.filters.direct_only = s(a.value) === 'true'
        return { desc: `Filter ${filter} = ${s(a.value)}`, highlight: 'results' }
      }
      case 'sort_flights':
        state.sort = s(a.by) === 'duration' ? 'duration' : 'price'
        return { desc: `Sort by ${state.sort}`, highlight: 'results' }
      case 'goto':
        state.step = s(a.step) as AppState['step']
        return { desc: `Go to ${state.step}`, highlight: state.step }
      case 'select_flight':
        state.selectedFlightId = s(a.flight_id)
        state.step = 'review'
        return { desc: `Select ${s(a.flight_id)}`, highlight: 'review' }
      case 'finish':
        return { desc: s(a.message) || 'Done.', finish: true }
      default:
        return null
    }
  }

  async function stepCall(): Promise<{ calls: ToolCall[], error?: string }> {
    try {
      const res = await fetch(`${apiBase}/api/agent/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: goal.value, state: serialize() }),
      })
      if (!res.ok) {
        const detail = await res.json().then(b => b.detail).catch(() => res.statusText)
        return { calls: [], error: detail || `HTTP ${res.status}` }
      }
      return await res.json()
    }
    catch (e) {
      return { calls: [], error: (e as Error).message }
    }
  }

  async function loop() {
    for (let i = 0; i < 8 && running.value; i++) {
      const res = await stepCall()
      if (res.error) { error.value = res.error; break }
      if (!res.calls.length) break

      let stop = false
      for (const call of res.calls) {
        if (call.name === 'book') {
          pendingBook.value = true
          announce('The agent is asking to confirm booking.')
          running.value = false
          stop = true
          break
        }
        const out = apply(call)
        if (out) {
          log.value.push({ name: call.name, desc: out.desc, next: call.next })
          announce(out.desc)
          flash(out.highlight)
          await delay(380)
          if (out.finish) { stop = true; break }
        }
        if (call.next === 'await_user' || call.next === 'done') { stop = true; break }
      }
      if (stop) break
    }
    running.value = false
  }

  async function run(userGoal: string) {
    const value = userGoal.trim()
    if (!value || running.value) return
    goal.value = value
    error.value = ''
    running.value = true
    await loop()
  }

  function stop() {
    running.value = false
  }

  async function confirmBook(ok: boolean) {
    pendingBook.value = false
    if (ok) {
      state.booked = true
      state.step = 'review'
      log.value.push({ name: 'book', desc: `Booked ${state.selectedFlightId}` })
      announce(`Booked ${state.selectedFlightId}.`)
      running.value = true
      await loop() // let the agent finish with a summary
    }
    else {
      log.value.push({ name: 'book', desc: 'Booking cancelled by user' })
      announce('Booking cancelled.')
    }
  }

  function setForm(field: keyof AppState['form'], value: string) {
    state.form[field] = value
  }

  function reset() {
    Object.assign(state, initialState())
    log.value = []
    error.value = ''
    live.value = ''
    highlight.value = ''
    running.value = false
    pendingBook.value = false
  }

  return {
    state, flights, visibleFlights, log, running, pendingBook, error, live, highlight,
    loadData, run, stop, confirmBook, setForm, reset,
  }
}
