import { computed, ref } from 'vue'
import type { AdFlight, LayoutPlan, TEvent, Widget } from '~/types/adaptive'

/**
 * Intent-based adaptive UI (approach #6). No chat. It buffers implicit telemetry (hovers with
 * dwell, clicks, sort taps), debounces a call to the inference layer, and applies the returned
 * layout plan (re-rank flights, emphasize/hide widgets). Telemetry stays in this session.
 */
export function useAdaptive() {
  const apiBase = useRuntimeConfig().public.apiBase
  const flights = ref<AdFlight[]>([])
  const widgets = ref<Widget[]>([])
  const plan = ref<LayoutPlan | null>(null)
  const events = ref<TEvent[]>([])
  const dataError = ref('')
  let timer: ReturnType<typeof setTimeout> | null = null

  async function loadData() {
    try {
      const res = await fetch(`${apiBase}/api/adaptive`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body = await res.json()
      flights.value = body.flights
      widgets.value = body.widgets
      await infer()
    }
    catch (e) {
      dataError.value = `Could not load — is the backend running? (${(e as Error).message})`
    }
  }

  async function infer() {
    try {
      const res = await fetch(`${apiBase}/api/adaptive/infer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: events.value }),
      })
      if (res.ok) plan.value = await res.json()
    }
    catch {
      // inference is best-effort; keep the last plan
    }
  }

  function record(ev: TEvent) {
    events.value.push(ev)
    if (events.value.length > 40) events.value.shift() // rolling window: recent behaviour wins
    if (timer) clearTimeout(timer)
    timer = setTimeout(infer, 450)
  }

  function reset() {
    events.value = []
    infer()
  }

  const sortedFlights = computed(() => {
    const arr = [...flights.value]
    const sort = plan.value?.sort
    if (sort === 'price') arr.sort((a, b) => a.price - b.price)
    else if (sort === 'duration') arr.sort((a, b) => a.duration_min - b.duration_min)
    else if (plan.value?.focus_flight_id) {
      const fid = plan.value.focus_flight_id
      arr.sort((a, b) => (a.id === fid ? -1 : 0) - (b.id === fid ? -1 : 0))
    }
    return arr
  })

  const orderedWidgets = computed(() => {
    if (!plan.value) return widgets.value
    const hide = new Set(plan.value.hide)
    const emph = plan.value.emphasize
    const rank = (id: string) => (emph.includes(id) ? emph.indexOf(id) : 99)
    return widgets.value.filter(w => !hide.has(w.id)).sort((a, b) => rank(a.id) - rank(b.id))
  })

  return { flights, widgets, plan, dataError, loadData, record, reset, sortedFlights, orderedWidgets }
}
