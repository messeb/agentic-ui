export interface AgentFlight {
  id: string
  origin: string
  destination: string
  date: string
  price: number
  duration_min: number
  stops: number
  departure_time: string
}

export type Step = 'search' | 'results' | 'review'

export interface AppForm {
  origin: string
  destination: string
  date: string
  passengers: string
  cabin: string
}

export interface AppFilters {
  max_price: number | null
  morning_only: boolean
  direct_only: boolean
}

export interface AppState {
  step: Step
  form: AppForm
  filters: AppFilters
  sort: 'price' | 'duration' | null
  selectedFlightId: string | null
  booked: boolean
}

export interface ToolCall {
  name: string
  args: Record<string, unknown>
  next: string
}

export interface LogEntry {
  name: string
  desc: string
  next?: string
}
