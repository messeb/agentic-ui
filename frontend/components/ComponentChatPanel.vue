<template>
  <div class="space-y-4">
    <!-- composer on top -->
    <form class="flex gap-2" @submit.prevent="submit(input)">
      <input
        v-model="input"
        type="text"
        placeholder="e.g. Show flights from Graz to Hamburg"
        class="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
        :disabled="loading"
      >
      <button
        type="submit"
        class="rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
        :disabled="loading || !input.trim()"
      >
        {{ loading ? '…' : 'Send' }}
      </button>
    </form>

    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="s in suggestions"
        :key="s"
        class="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
        :disabled="loading"
        @click="submit(s)"
      >
        {{ s }}
      </button>
      <span v-if="cart.length" class="ml-auto text-xs text-slate-600">🛒 {{ cart.length }} · €{{ cartTotal }}</span>
      <button
        v-if="items.length || cart.length"
        class="text-xs text-slate-400 hover:text-slate-700 disabled:opacity-40"
        :class="{ 'ml-auto': !cart.length }"
        :disabled="loading"
        @click="clearAll"
      >
        Clear
      </button>
    </div>

    <!-- selected components flow top-to-bottom -->
    <div v-if="items.length || error" class="space-y-3">
      <template v-for="(item, i) in items" :key="i">
        <div v-if="item.kind === 'user'" class="flex justify-end">
          <div class="max-w-[85%] rounded-2xl bg-ink px-4 py-2.5 text-sm text-white">{{ item.content }}</div>
        </div>
        <div v-else-if="item.kind === 'note'" class="text-center text-xs text-slate-400">{{ item.content }}</div>
        <div v-else class="space-y-2">
          <p v-if="item.message" class="text-sm text-slate-600">{{ item.message }}</p>
          <CatalogRenderer
            v-for="(c, j) in item.components"
            :key="j"
            :item="c"
            @select-flight="onSelectFlight"
            @add-ancillary="onAddAncillary"
            @confirm-booking="onConfirmBooking"
            @cancel-booking="onCancelBooking"
          />
        </div>
      </template>

      <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { AncillaryOption, BookingRequestProps, Flight } from '~/types/catalog'

const { items, cart, loading, error, wire, send, addAncillary, book, note, reset } = useComponentChat()

// Expose the raw backend frames so the page can surface them in <WireInspector>.
defineExpose({ wire })

const input = ref('')
const cartTotal = computed(() => cart.value.reduce((sum, o) => sum + o.price, 0))

const suggestions = [
  'Flights from Graz to Hamburg',
  'What is the status of AB123?',
  'I want a better seat and extra baggage',
  'Book AB123 for Alice',
]

// Smart-wrapper event handlers (state + navigation live here, not in the dumb components).
async function onAddAncillary(option: AncillaryOption) {
  await addAncillary(option) // real backend call → updates the shared cart
}
function onSelectFlight(flight: Flight) {
  // Inject a booking form (passenger name) for the selected flight.
  items.value.push({
    kind: 'doc',
    message: '',
    components: [{ component: 'booking_form', props: { flight } }],
  })
}
async function onConfirmBooking(req: BookingRequestProps) {
  await book(req.flight_id, req.passenger) // real backend booking with the cart's extras
}
function onCancelBooking(req: BookingRequestProps) {
  note(`Booking of ${req.flight_id} cancelled.`)
}

async function submit(text: string) {
  const value = text.trim()
  if (!value || loading.value) return
  input.value = ''
  await send(value)
}

function clearAll() {
  reset()
}
</script>
