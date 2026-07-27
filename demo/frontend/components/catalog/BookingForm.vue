<template>
  <div class="rounded-lg border border-slate-300 bg-white p-4">
    <p class="text-sm font-medium text-slate-800">
      Book <code>{{ data.flight.id }}</code>
      <span class="text-slate-500">· {{ data.flight.origin }} → {{ data.flight.destination }} · €{{ data.flight.price }}</span>
    </p>
    <div v-if="!done" class="mt-3 flex flex-wrap gap-2">
      <input
        v-model="passenger"
        type="text"
        placeholder="Passenger name"
        class="flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-slate-500 focus:outline-none"
        @keyup.enter="confirm"
      >
      <button
        class="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:opacity-40"
        :disabled="!passenger.trim()"
        @click="confirm"
      >
        Book
      </button>
      <button
        class="rounded-md bg-white px-3 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-slate-300 hover:bg-slate-50"
        @click="cancel"
      >
        Cancel
      </button>
    </div>
    <p v-else class="mt-2 text-xs text-slate-500">{{ outcome }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { BookingFormProps, BookingRequestProps } from '~/types/catalog'

const props = defineProps<{ data: BookingFormProps }>()
const emit = defineEmits<{ confirm: [req: BookingRequestProps], cancel: [req: BookingRequestProps] }>()

const passenger = ref('')
const done = ref(false)
const outcome = ref('')

function confirm() {
  const name = passenger.value.trim()
  if (!name) return
  done.value = true
  outcome.value = `Booking ${props.data.flight.id} for ${name}…`
  emit('confirm', { flight_id: props.data.flight.id, passenger: name })
}
function cancel() {
  done.value = true
  outcome.value = 'Cancelled.'
  emit('cancel', { flight_id: props.data.flight.id, passenger: '' })
}
</script>
