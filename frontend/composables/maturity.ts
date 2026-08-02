import type { Maturity } from '~/types/approach'

const LABELS: Record<Maturity, string> = {
  'proven': 'Proven',
  'established': 'Established',
  'emerging': 'Emerging',
  'paused': 'Paused',
  'least-mature': 'Least mature',
}

const CLASSES: Record<Maturity, string> = {
  'proven': 'bg-emerald-100 text-emerald-800',
  'established': 'bg-sky-100 text-sky-800',
  'emerging': 'bg-amber-100 text-amber-800',
  'paused': 'bg-rose-100 text-rose-800',
  'least-mature': 'bg-zinc-200 text-zinc-700',
}

export function maturityLabel(m: Maturity): string {
  return LABELS[m]
}

export function maturityClass(m: Maturity): string {
  return CLASSES[m]
}
