<template>
  <FlightResults
    v-if="item.component === 'flight_results'"
    :data="item.props"
    @select="emit('select-flight', $event)"
  />
  <FlightStatus
    v-else-if="item.component === 'flight_status'"
    :data="item.props"
  />
  <AncillaryOffer
    v-else-if="item.component === 'ancillary_offer'"
    :data="item.props"
    @add="emit('add-ancillary', $event)"
  />
  <BookingRequest
    v-else-if="item.component === 'booking_request'"
    :data="item.props"
    @confirm="emit('confirm-booking', $event)"
    @cancel="emit('cancel-booking', $event)"
  />
  <BookingConfirmation
    v-else-if="item.component === 'booking_confirmation'"
    :data="item.props"
  />
  <CartSummary
    v-else-if="item.component === 'cart_summary'"
    :data="item.props"
  />
  <BookingForm
    v-else-if="item.component === 'booking_form'"
    :data="item.props"
    @confirm="emit('confirm-booking', $event)"
    @cancel="emit('cancel-booking', $event)"
  />
  <div v-else class="rounded bg-rose-50 px-3 py-2 text-xs text-rose-700">
    Unknown component
  </div>
</template>

<script setup lang="ts">
import AncillaryOffer from './catalog/AncillaryOffer.vue'
import BookingConfirmation from './catalog/BookingConfirmation.vue'
import BookingForm from './catalog/BookingForm.vue'
import BookingRequest from './catalog/BookingRequest.vue'
import CartSummary from './catalog/CartSummary.vue'
import FlightResults from './catalog/FlightResults.vue'
import FlightStatus from './catalog/FlightStatus.vue'
import type { AncillaryOption, BookingRequestProps, Flight, UiComponent } from '~/types/catalog'

defineProps<{ item: UiComponent }>()
const emit = defineEmits<{
  'select-flight': [flight: Flight]
  'add-ancillary': [option: AncillaryOption]
  'confirm-booking': [req: BookingRequestProps]
  'cancel-booking': [req: BookingRequestProps]
}>()
</script>
