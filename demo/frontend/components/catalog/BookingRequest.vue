<template>
  <div class="rounded-lg border border-amber-300 bg-amber-50 p-4">
    <p class="text-sm font-medium text-amber-900">
      ⚠️ Confirm booking of <code>{{ data.flight_id }}</code> for <strong>{{ data.passenger }}</strong>?
    </p>
    <p class="mt-1 text-xs text-amber-800">This charges the customer and any added extras.</p>
    <div v-if="!done" class="mt-3 flex gap-2">
      <button
        class="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:opacity-90"
        @click="confirm"
      >
        Confirm booking
      </button>
      <button
        class="rounded-md bg-white px-3 py-1.5 text-xs font-medium text-slate-600 ring-1 ring-slate-300 hover:bg-slate-50"
        @click="cancel"
      >
        Cancel
      </button>
    </div>
    <p v-else class="mt-3 text-xs text-slate-500">{{ outcome }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { BookingRequestProps } from '~/types/catalog'

const props = defineProps<{ data: BookingRequestProps }>()
const emit = defineEmits<{ confirm: [req: BookingRequestProps], cancel: [req: BookingRequestProps] }>()

const done = ref(false)
const outcome = ref('')

function confirm() {
  done.value = true
  outcome.value = 'Confirmed — booking…'
  emit('confirm', props.data)
}
function cancel() {
  done.value = true
  outcome.value = 'Cancelled.'
  emit('cancel', props.data)
}
</script>
