<template>
  <div class="flex h-[70vh] flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
    <div class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2.5">
      <div class="flex items-center gap-2">
        <span class="h-2 w-2 rounded-full bg-emerald-500" />
        <span class="text-sm font-semibold">Catalog assistant</span>
        <span class="text-xs text-slate-400">structured output</span>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="cart.length" class="text-xs text-slate-600">
          🛒 {{ cart.length }} · €{{ cartTotal }}
        </span>
        <button
          class="text-xs text-slate-500 hover:text-slate-900 disabled:opacity-40"
          :disabled="loading || (!items.length && !cart.length)"
          @click="clearAll"
        >
          Clear
        </button>
      </div>
    </div>

    <div ref="el" class="flex-1 space-y-3 overflow-y-auto p-4" @scroll="onScroll">
      <div v-if="!items.length" class="grid h-full place-items-center text-center text-sm text-slate-400">
        <div>
          <p class="mb-3">Ask for flights, a flight's status, or extras — the model picks the UI.</p>
          <div class="flex flex-wrap justify-center gap-2">
            <button
              v-for="s in suggestions"
              :key="s"
              class="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-600 hover:border-slate-500"
              @click="submit(s)"
            >
              {{ s }}
            </button>
          </div>
        </div>
      </div>

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

    <!-- predefined prompts, shown after every exchange -->
    <div v-if="items.length" class="flex flex-wrap gap-2 border-t border-slate-200 bg-white px-3 pt-2">
      <button
        v-for="s in suggestions"
        :key="s"
        class="rounded-full border border-slate-300 px-2.5 py-1 text-xs text-slate-600 hover:border-slate-500 disabled:opacity-40"
        :disabled="loading"
        @click="submit(s)"
      >
        {{ s }}
      </button>
    </div>

    <form class="flex gap-2 border-t border-slate-200 bg-white p-3" @submit.prevent="submit(input)">
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
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { AncillaryOption, BookingRequestProps, Flight } from '~/types/catalog'

const { items, cart, loading, error, send, addAncillary, book, note, reset } = useComponentChat()
const { el, onScroll, scrollToBottom } = useAutoScroll()

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
  await nextTick(() => scrollToBottom(true))
}
function onSelectFlight(flight: Flight) {
  // Inject a booking form (passenger name) for the selected flight.
  items.value.push({
    kind: 'doc',
    message: '',
    components: [{ component: 'booking_form', props: { flight } }],
  })
  nextTick(() => scrollToBottom(true))
}
async function onConfirmBooking(req: BookingRequestProps) {
  await book(req.flight_id, req.passenger) // real backend booking with the cart's extras
  await nextTick(() => scrollToBottom(true))
}
function onCancelBooking(req: BookingRequestProps) {
  note(`Booking of ${req.flight_id} cancelled.`)
}

async function submit(text: string) {
  const value = text.trim()
  if (!value || loading.value) return
  input.value = ''
  await nextTick(() => scrollToBottom(true))
  await send(value)
  await nextTick(() => scrollToBottom(true))
}

function clearAll() {
  reset()
}

watch(items, () => nextTick(() => scrollToBottom()), { deep: true })
</script>
