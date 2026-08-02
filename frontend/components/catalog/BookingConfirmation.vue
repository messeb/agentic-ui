<template>
  <div class="rounded-lg border border-emerald-300 bg-emerald-50 p-4">
    <div class="flex items-center gap-2">
      <span>✅</span>
      <span class="text-sm font-semibold text-emerald-900">Booking confirmed</span>
      <code class="ml-auto text-xs text-emerald-800">{{ data.booking_id }}</code>
    </div>
    <p class="mt-1 text-sm text-emerald-900">
      <code>{{ data.flight_id }}</code> for <strong>{{ data.passenger }}</strong>
    </p>
    <dl class="mt-3 space-y-1 text-sm">
      <div class="flex justify-between text-slate-600">
        <dt>Flight</dt>
        <dd>€{{ data.base_price }}</dd>
      </div>
      <div v-for="e in data.extras" :key="e.label" class="flex justify-between text-slate-600">
        <dt>{{ e.label }}</dt>
        <dd>€{{ e.price }}</dd>
      </div>
      <div class="flex justify-between border-t border-emerald-200 pt-1 font-semibold text-emerald-900">
        <dt>Total</dt>
        <dd>€{{ data.total }}</dd>
      </div>
    </dl>
  </div>
</template>

<script setup lang="ts">
import type { BookingConfirmationProps } from '~/types/catalog'

defineProps<{ data: BookingConfirmationProps }>()
</script>
