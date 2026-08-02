export type ToolStatus = 'pending' | 'done' | 'denied'

export interface UserItem {
  kind: 'user'
  content: string
}

export interface AssistantTextItem {
  kind: 'assistant_text'
  content: string
}

export interface ToolItem {
  kind: 'tool'
  id: string
  name: string
  args: Record<string, unknown>
  sideEffect: boolean
  status: ToolStatus
  result: unknown
}

export interface FinalItem {
  kind: 'final'
  content: string
}

export type TimelineItem = UserItem | AssistantTextItem | ToolItem | FinalItem

export interface PendingCall {
  id: string
  name: string
  args: Record<string, unknown>
}

/** OpenAI-format message the client stores and resends verbatim. */
export type OpenAiMessage = Record<string, unknown>

export interface ToolCatalogEntry {
  name: string
  description: string
  side_effect: boolean
  parameters: Record<string, unknown>
}
