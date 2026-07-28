export interface AdFlight {
  id: string
  origin: string
  destination: string
  date: string
  price: number
  delay_minutes: number
  duration_min: number
  stops: number
  airline: string
}

export interface Widget {
  id: string
  title: string
  description: string
}

export interface Intents {
  price: number
  time: number
  urgency: number
  explore: number
}

export type PrimaryIntent = 'price' | 'time' | 'urgency' | 'explore'

export interface LayoutPlan {
  intents: Intents
  primary: PrimaryIntent
  sort: 'price' | 'duration' | 'relevance'
  emphasize: string[]
  hide: string[]
  cta: string
  focus_flight_id: string | null
  rationale: string
}

export interface TEvent {
  kind: 'view' | 'click' | 'sort'
  flight_id?: string
  dwell_ms?: number
  sort?: 'price' | 'duration'
}
