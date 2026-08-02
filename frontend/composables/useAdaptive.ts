import { computed, ref, watch } from 'vue'
import type { CardScore, Disruption, InferResult, Trip } from '~/types/adaptive'
import type { WireFrame } from '~/types/wire'

/**
 * Context-driven adaptive UI (approach #6). No chat. One upcoming trip; the client sends the live
 * context — minutes to departure (a scrubber), whether the traveller checked in, and any
 * disruption — to the inference layer, which returns an ordered layout. The most relevant card is
 * surfaced to the top; irrelevant ones are hidden. Deterministic; needs no API key.
 */
const START = 28 * 60 // ~28h out → the overview leads

export function useAdaptive() {
  const apiBase = useRuntimeConfig().public.apiBase
  const trip = ref<Trip | null>(null)
  const plan = ref<InferResult | null>(null)
  const dataError = ref('')
  const wire = ref<WireFrame[]>([])

  // The three context inputs the inference layer reads.
  const minutesToDeparture = ref(START)
  const checkedIn = ref(false)
  const disruption = ref<Disruption>('none')

  let timer: ReturnType<typeof setTimeout> | null = null

  async function loadData() {
    try {
      const res = await fetch(`${apiBase}/api/adaptive`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const body = await res.json()
      trip.value = body.trip
      wire.value.push({ label: 'GET /api/adaptive', body: JSON.stringify(body), kind: 'response' })
      await infer()
    }
    catch (e) {
      dataError.value = `Could not load — is the backend running? (${(e as Error).message})`
    }
  }

  async function infer() {
    try {
      const payload = {
        minutes_to_departure: minutesToDeparture.value,
        checked_in: checkedIn.value,
        disruption: disruption.value,
      }
      const res = await fetch(`${apiBase}/api/adaptive/infer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) return
      plan.value = await res.json()
      // The scrubber fires this repeatedly — keep a rolling log so the WireInspector shows the
      // stream of inference decisions.
      wire.value.push({
        label: 'POST /api/adaptive/infer',
        body: JSON.stringify(plan.value),
        kind: 'response',
      })
      if (wire.value.length > 20) wire.value.shift()
    }
    catch {
      // best-effort; keep the last plan
    }
  }

  // Re-infer (debounced) whenever the context changes — e.g. while dragging the scrubber.
  watch([minutesToDeparture, checkedIn, disruption], () => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(infer, 120)
  })

  function checkIn() {
    checkedIn.value = true
  }

  function reset() {
    minutesToDeparture.value = START
    checkedIn.value = false
    disruption.value = 'none'
    wire.value = []
    infer()
  }

  // Only the cards the inference layer marked visible, already ordered by score.
  const orderedCards = computed<CardScore[]>(() => (plan.value?.cards ?? []).filter(c => c.visible))

  return {
    trip,
    plan,
    dataError,
    wire,
    minutesToDeparture,
    checkedIn,
    disruption,
    orderedCards,
    loadData,
    infer,
    checkIn,
    reset,
  }
}
