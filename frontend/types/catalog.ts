export interface Flight {
  id: string
  origin: string
  destination: string
  date: string
  price: number
  seats: number
}

export interface FlightResultsProps {
  origin: string
  destination: string
  flights: Flight[]
}

export type FlightStatusValue = 'on-time' | 'delayed' | 'boarding' | 'cancelled'

export interface FlightStatusProps {
  flight_id: string
  status: FlightStatusValue
  departure_time: string
  gate: string | null
  delay_minutes: number | null
}

export type AncillaryKind = 'seat' | 'baggage' | 'meal' | 'lounge' | 'priority' | 'insurance'

export interface AncillaryOption {
  id: string
  label: string
  description: string
  price: number
  kind: AncillaryKind
}

export interface AncillaryOfferProps {
  title: string
  options: AncillaryOption[]
}

export interface BookingRequestProps {
  flight_id: string
  passenger: string
}

export interface ExtraLine {
  label: string
  price: number
}

export interface BookingConfirmationProps {
  booking_id: string
  flight_id: string
  passenger: string
  base_price: number
  extras: ExtraLine[]
  total: number
}

export interface CartSummaryProps {
  items: AncillaryOption[]
  subtotal: number
}

export interface BookingFormProps {
  flight: Flight
}

export type UiComponent =
  | { component: 'flight_results', props: FlightResultsProps }
  | { component: 'flight_status', props: FlightStatusProps }
  | { component: 'ancillary_offer', props: AncillaryOfferProps }
  | { component: 'booking_request', props: BookingRequestProps }
  | { component: 'booking_confirmation', props: BookingConfirmationProps }
  | { component: 'cart_summary', props: CartSummaryProps }
  | { component: 'booking_form', props: BookingFormProps }

export interface UiDocument {
  message: string
  components: UiComponent[]
}

export interface CatalogEntry {
  name: string
  description: string
  props: Record<string, unknown>
}
