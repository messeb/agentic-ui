export type ProtoEvent = { type: string } & Record<string, unknown>

export interface ToolCallView {
  id: string
  name: string
  args: string
  result: unknown
}

export interface UiResource {
  uri: string
  text: string
}

export interface McpUiIntent {
  tool: string
  args: Record<string, unknown>
}

export interface ProtocolInfo {
  protocols: { name: string, connects: string, role: string }[]
  event_types: Record<string, string[]>
}

export interface PatchOp {
  op: 'add' | 'replace' | 'remove'
  path: string
  value?: unknown
}
