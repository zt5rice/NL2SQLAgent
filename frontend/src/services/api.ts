import type {
  ChartType,
  DatabaseSchema,
  DatabaseTable,
  Message,
  Session,
} from '../types'

const API_BASE = 'http://localhost:8000/api'

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Request failed')
  }

  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

// Session API (backed by the FastAPI backend, available from Phase 3)
export const sessionApi = {
  list: async () => {
    const payload = await request<{ sessions: Session[] }>('/sessions')
    return payload.sessions
  },
  create: (title?: string) =>
    request<Session>('/sessions', { method: 'POST', body: JSON.stringify({ title }) }),
  update: (id: string, data: { title?: string }) =>
    request<Session>(`/sessions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => request<void>(`/sessions/${id}`, { method: 'DELETE' }),
  getMessages: (id: string) => request<Message[]>(`/sessions/${id}/messages`),
}

// Database introspection API (matches the backend /api/database endpoints)
export const databaseApi = {
  tables: () => request<{ tables: string[] }>('/database/tables'),
  schema: () => request<DatabaseSchema>('/database/schema'),
  table: (name: string) => request<DatabaseTable>(`/database/tables/${name}`),
}

export interface ChatRequest {
  session_id: string
  message: string
}

export interface SSEDataPayload {
  columns: string[]
  rows: Array<Array<string | number>>
  raw: string
}

export interface SSEChartPayload {
  type: ChartType
  title: string
  data: Array<{ name: string; value: number | string }>
  xField?: string
  yField?: string
}

export interface SSEHandlers {
  onThinking?: (text: string) => void
  onText?: (text: string) => void
  onSql?: (sql: string) => void
  onData?: (data: SSEDataPayload) => void
  onChart?: (config: SSEChartPayload) => void
  onError?: (message: string) => void
  onDone?: () => void
}

/**
 * SSE chat client.
 *
 * POSTs the chat request and parses the text/event-stream response with
 * fetch + ReadableStream (EventSource cannot send a POST body).
 */
export function createChatSSE(request: ChatRequest) {
  const controller = new AbortController()

  return {
    async start(handlers: SSEHandlers) {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = ''
      const dataLines: string[] = []
      let watchdog: ReturnType<typeof setTimeout> | null = null

      const flush = () => {
        if (!currentEvent || dataLines.length === 0) return
        processEvent(currentEvent, dataLines.join('\n'), handlers)
        currentEvent = ''
        dataLines.length = 0
      }

      // The backend pings every 15s, so a live stream always produces bytes.
      // If nothing arrives for 60s, the connection is dead: abort and let the
      // finally block finalize the stream (onDone) instead of hanging forever.
      const armWatchdog = () => {
        if (watchdog) clearTimeout(watchdog)
        watchdog = setTimeout(() => controller.abort(), 60_000)
      }

      armWatchdog()
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          armWatchdog()

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              flush()
              currentEvent = line.slice(7).trim()
            } else if (line.startsWith('data: ')) {
              dataLines.push(line.slice(6))
            } else if (line === '') {
              flush()
            }
          }
        }
        flush()
      } finally {
        if (watchdog) clearTimeout(watchdog)
        // Guaranteed finalization: fires even if the read loop throws or the
        // watchdog aborts, so isStreaming can never stay stuck.
        handlers.onDone?.()
      }
    },

    abort: () => controller.abort(),
  }
}

function processEvent(event: string, data: string, handlers: SSEHandlers) {
  try {
    switch (event) {
      case 'thinking':
        handlers.onThinking?.(data)
        break
      case 'text':
        handlers.onText?.(data)
        break
      case 'sql':
        handlers.onSql?.(data)
        break
      case 'data':
        handlers.onData?.(JSON.parse(data) as SSEDataPayload)
        break
      case 'chart':
        handlers.onChart?.(JSON.parse(data) as SSEChartPayload)
        break
      case 'error':
        handlers.onError?.(data)
        break
      default:
        break
    }
  } catch (e) {
    console.error('Failed to process SSE event', e)
  }
}

export const api = {
  session: sessionApi,
  database: databaseApi,
  chat: createChatSSE,
}
