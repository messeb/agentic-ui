/**
 * A single raw payload the backend sent — one SSE frame, one JSON response, or one request line.
 * Collected by each approach's composable and shown verbatim in <WireInspector> so the user can see
 * exactly what streamed/returned from the backend (nothing is fabricated client-side).
 */
export interface WireFrame {
  /** Short label, e.g. an event type ('token', 'tool_call') or a request line ('POST /api/chat'). */
  label: string
  /** The raw body as received — a JSON string or plain text, shown verbatim. */
  body: string
  /** Optional group, drives the row's accent colour. */
  kind?: 'request' | 'stream' | 'response' | 'error'
}
