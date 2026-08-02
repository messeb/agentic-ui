export type Maturity = 'proven' | 'established' | 'emerging' | 'paused' | 'least-mature'
export type ApproachStatus = 'not-implemented' | 'in-progress' | 'implemented'

export interface Approach {
  id: string
  number: number
  title: string
  tagline: string
  input: string
  output: string
  howItWorks: string
  whatYouNeed: string[]
  agenticLevel: number
  maturity: Maturity
  status: ApproachStatus
}

export interface Manifest {
  version: string
  description: string
  approaches: Approach[]
}
