import manifest from '@shared/approaches.json'
import type { Approach, Manifest } from '~/types/approach'

const data = manifest as unknown as Manifest

/**
 * The 8 approaches, read from the shared manifest at build time.
 * This is the single source of truth shared with the backend — no network call
 * needed to render the catalog.
 */
export function useApproaches(): Approach[] {
  return data.approaches
}

export function useApproach(id: string): Approach | undefined {
  return data.approaches.find((a) => a.id === id)
}

export function useManifestVersion(): string {
  return data.version
}
