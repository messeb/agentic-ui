export interface Trip {
  id: string
  flight_no: string
  airline: string
  origin: string
  origin_city: string
  destination: string
  dest_city: string
  date: string
  scheduled_departure: string
  terminal: string
  gate: string
  seat: string
  boarding_group: string
  duration_min: number
}

export type Disruption = 'none' | 'delayed' | 'gate_change' | 'cancelled'

export interface DisruptionDetail {
  type: Disruption
  delay_min?: number
  new_departure?: string
  new_gate?: string
  old_gate?: string
}

export type CardId = 'overview' | 'checkin' | 'leave' | 'boarding' | 'disruption'

export interface CardScore {
  id: CardId
  score: number
  visible: boolean
  reason: string
}

export interface InferResult {
  minutes_to_departure: number
  checked_in: boolean
  disruption: Disruption
  disruption_detail: DisruptionDetail
  primary: CardId
  rationale: string
  cards: CardScore[]
}
