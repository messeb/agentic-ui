export interface GenFlight {
  id: string
  origin: string
  destination: string
  date: string
  price: number
  delay_minutes: number
}

export interface RuntimeFunction {
  name: string
  kind: string
  signature: string
  description: string
}

export interface GenResult {
  status: 'success' | 'error'
  message: string
  code: string
}

export interface ChartPoint {
  name: string
  value: number
}

export type ChartType = 'bar' | 'pie'

export interface ChartData {
  title: string
  type: ChartType
  data: ChartPoint[]
}
