export interface RscNode {
  id: string
  parent: string | null
  comp: string
  props: Record<string, unknown>
}

export interface RscToolInfo {
  name: string
  args: Record<string, unknown>
}
