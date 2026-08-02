<template>
  <div
    class="rounded-xl border bg-white p-4 transition-all"
    :class="[toneClass, emphasized ? 'ring-2 ring-offset-2 shadow-md ' + ringClass : 'opacity-95']"
  >
    <div class="flex items-center gap-2">
      <span class="text-lg">{{ icon }}</span>
      <h3 class="font-semibold text-slate-800">{{ title }}</h3>
      <span
        v-if="emphasized"
        class="ml-auto rounded-full bg-ink px-2 py-0.5 text-[10px] font-semibold text-white"
      >★ surfaced now</span>
    </div>

    <!-- overview -->
    <div v-if="card.id === 'overview'" class="mt-3 space-y-2">
      <div class="flex items-baseline gap-2">
        <span class="text-xl font-bold">{{ trip.origin }}</span>
        <span class="text-slate-400">→</span>
        <span class="text-xl font-bold">{{ trip.destination }}</span>
        <span class="ml-auto text-sm text-slate-500">{{ trip.flight_no }} · {{ trip.airline }}</span>
      </div>
      <div class="grid grid-cols-3 gap-2 text-sm">
        <div><div class="text-xs text-slate-400">Departs</div>{{ departureLabel }}</div>
        <div><div class="text-xs text-slate-400">Terminal / Gate</div>{{ trip.terminal }} · {{ effectiveGate }}</div>
        <div><div class="text-xs text-slate-400">Seat</div>{{ trip.seat }}</div>
      </div>
      <p class="text-xs" :class="statusClass">{{ statusLine }}</p>
    </div>

    <!-- check-in -->
    <div v-else-if="card.id === 'checkin'" class="mt-3 space-y-2 text-sm">
      <template v-if="plan.checked_in">
        <p class="text-slate-600">Seat <strong>{{ trip.seat }}</strong> · boarding group {{ trip.boarding_group }}.</p>
        <span class="inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">✓ Boarding pass ready</span>
      </template>
      <template v-else>
        <p class="text-slate-600">Check in online to get your boarding pass and keep your seat.</p>
        <button
          class="rounded-lg bg-ink px-3 py-1.5 text-sm font-medium text-white hover:opacity-90"
          @click="$emit('checkin')"
        >
          Check in online
        </button>
      </template>
    </div>

    <!-- leave for the airport -->
    <div v-else-if="card.id === 'leave'" class="mt-3 space-y-1 text-sm text-slate-600">
      <p>Security at {{ trip.origin_city }} ({{ trip.origin }}) can take 30–45 min at peak.</p>
      <p class="text-slate-500">Aim to be at the gate by <strong>{{ gateBy }}</strong>.</p>
    </div>

    <!-- boarding -->
    <div v-else-if="card.id === 'boarding'" class="mt-3 grid grid-cols-3 gap-2 text-sm">
      <div><div class="text-xs text-slate-400">Gate</div><span class="text-lg font-bold">{{ effectiveGate }}</span></div>
      <div><div class="text-xs text-slate-400">Group</div><span class="text-lg font-bold">{{ trip.boarding_group }}</span></div>
      <div><div class="text-xs text-slate-400">Seat</div><span class="text-lg font-bold">{{ trip.seat }}</span></div>
      <p class="col-span-3 text-xs text-slate-500">The gate closes 15 minutes before departure.</p>
    </div>

    <!-- disruption -->
    <div v-else-if="card.id === 'disruption'" class="mt-3 space-y-2 text-sm">
      <template v-if="detail.type === 'delayed'">
        <p>New departure <strong>{{ detail.new_departure }}</strong>
          <span class="text-slate-400 line-through">{{ trip.scheduled_departure }}</span>
          <span class="text-rose-700"> (+{{ detail.delay_min }} min)</span>
        </p>
        <p class="text-slate-500">We'll keep this updated — no action needed right now.</p>
      </template>
      <template v-else-if="detail.type === 'gate_change'">
        <p>New gate <strong>{{ detail.new_gate }}</strong>
          <span class="text-slate-400 line-through">{{ detail.old_gate }}</span>
        </p>
        <p class="text-slate-500">Allow a few extra minutes to reach the new gate.</p>
      </template>
      <template v-else-if="detail.type === 'cancelled'">
        <p>Your flight was cancelled. We can rebook you on the next available service.</p>
        <button class="rounded-lg bg-rose-600 px-3 py-1.5 text-sm font-medium text-white hover:opacity-90">
          See rebooking options
        </button>
      </template>
    </div>

    <p class="mt-3 border-t border-slate-100 pt-2 text-xs text-slate-400">{{ card.reason }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CardScore, InferResult, Trip } from '~/types/adaptive'

const props = defineProps<{
  card: CardScore
  trip: Trip
  plan: InferResult
  emphasized: boolean
}>()

defineEmits<{ checkin: [] }>()

const detail = computed(() => props.plan.disruption_detail)

const META: Record<string, { icon: string, title: string }> = {
  overview: { icon: '✈️', title: 'Your flight' },
  checkin: { icon: '🎫', title: 'Check-in' },
  leave: { icon: '🚕', title: 'Head to the airport' },
  boarding: { icon: '🛫', title: 'Boarding' },
  disruption: { icon: '⚠️', title: 'Flight update' },
}
const icon = computed(() => META[props.card.id]!.icon)
const title = computed(() => META[props.card.id]!.title)

const isDisruption = computed(() => props.card.id === 'disruption')
const toneClass = computed(() =>
  isDisruption.value ? 'border-rose-200 bg-rose-50' : 'border-slate-200',
)
const ringClass = computed(() =>
  isDisruption.value ? 'ring-rose-400' : 'ring-ink',
)

const effectiveGate = computed(() =>
  props.plan.disruption === 'gate_change' ? props.plan.disruption_detail.new_gate : props.trip.gate,
)

// Minutes → "in 3h 05m" / "20 min ago".
const departureLabel = computed(() => {
  const dep = props.plan.disruption === 'delayed'
    ? props.plan.disruption_detail.new_departure
    : props.trip.scheduled_departure
  return `${dep} · ${props.trip.date}`
})

function addMinutes(hhmm: string, minutes: number): string {
  const [h = 0, m = 0] = hhmm.split(':').map(Number)
  const total = (h * 60 + m + minutes + 24 * 60) % (24 * 60)
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}
// Be at the gate ~40 min before departure.
const gateBy = computed(() => addMinutes(props.trip.scheduled_departure, -40))

const statusLine = computed(() => {
  if (props.plan.disruption === 'delayed') return `Delayed +${detail.value.delay_min} min`
  if (props.plan.disruption === 'gate_change') return `Gate changed to ${detail.value.new_gate}`
  if (props.plan.disruption === 'cancelled') return 'Cancelled'
  if (props.plan.minutes_to_departure < 0) return 'Departed'
  return 'On time'
})
const statusClass = computed(() =>
  props.plan.disruption === 'none' && props.plan.minutes_to_departure >= 0
    ? 'text-emerald-600'
    : 'text-rose-600',
)
</script>
