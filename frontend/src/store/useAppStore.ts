import { create } from 'zustand'
import type {
  ChartConfig,
  Message,
  Session,
  TableData,
  ViewMode,
} from '../types'

const generateId = () => Math.random().toString(36).substring(2, 15)

const now = () => new Date().toISOString()

interface AppState {
  sessions: Session[]
  currentSessionId: string | null
  messages: Message[]
  isStreaming: boolean
  chartConfig: ChartConfig | null
  tableData: TableData | null
  viewMode: ViewMode

  createSession: (title?: string) => Session
  addSession: (session: Session) => void
  selectSession: (id: string) => void
  renameSession: (id: string, title: string) => void
  deleteSession: (id: string) => void
  autoTitleFromMessage: (id: string, content: string) => void

  addMessage: (message: Omit<Message, 'id' | 'created_at'>) => void
  updateLastMessageContent: (content: string) => void
  updateLastMessageSql: (sql: string) => void
  setStreaming: (streaming: boolean) => void
  setMessages: (messages: Message[]) => void
  setSessions: (sessions: Session[]) => void
  clearMessages: () => void

  setChartConfig: (config: ChartConfig | null) => void
  setTableData: (data: TableData | null) => void
  setViewMode: (mode: ViewMode) => void
  clearChartData: () => void
}

export const useAppStore = create<AppState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  isStreaming: false,
  chartConfig: null,
  tableData: null,
  viewMode: 'chart',

  createSession: (title) => {
    const session: Session = {
      id: generateId(),
      title: title?.trim() || 'New Session',
      created_at: now(),
      updated_at: now(),
    }
    set((state) => ({
      sessions: [session, ...state.sessions],
      currentSessionId: session.id,
    }))
    return session
  },

  addSession: (session) => {
    set((state) => ({
      sessions: [session, ...state.sessions.filter((s) => s.id !== session.id)],
      currentSessionId: session.id,
    }))
  },

  selectSession: (id) => {
    set({ currentSessionId: id })
  },

  renameSession: (id, title) => {
    const trimmed = title.trim()
    if (!trimmed) return
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === id ? { ...s, title: trimmed, updated_at: now() } : s,
      ),
    }))
  },

  deleteSession: (id) => {
    const remaining = get().sessions.filter((s) => s.id !== id)
    set({
      sessions: remaining,
      currentSessionId:
        get().currentSessionId === id ? (remaining[0]?.id ?? null) : get().currentSessionId,
    })
  },

  autoTitleFromMessage: (id, content) => {
    const title = content.slice(0, 30) + (content.length > 30 ? '...' : '')
    get().renameSession(id, title)
  },

  addMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, { ...message, id: generateId(), created_at: now() }],
    }))
  },

  updateLastMessageContent: (content) => {
    set((state) => {
      const messages = [...state.messages]
      const last = messages[messages.length - 1]
      if (last) {
        messages[messages.length - 1] = { ...last, content }
      }
      return { messages }
    })
  },

  updateLastMessageSql: (sql) => {
    set((state) => {
      const messages = [...state.messages]
      const last = messages[messages.length - 1]
      if (last) {
        messages[messages.length - 1] = { ...last, sql_query: sql }
      }
      return { messages }
    })
  },

  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setMessages: (messages) => set({ messages }),
  setSessions: (sessions) => set({ sessions }),
  clearMessages: () => set({ messages: [] }),

  setChartConfig: (config) => set({ chartConfig: config }),
  setTableData: (data) => set({ tableData: data }),
  setViewMode: (mode) => set({ viewMode: mode }),
  clearChartData: () => set({ chartConfig: null, tableData: null }),
}))
