import { beforeEach, describe, expect, it } from 'vitest'
import { useAppStore } from './useAppStore'

const initialState = {
  sessions: [],
  currentSessionId: null,
  messages: [],
  isStreaming: false,
  chartConfig: null,
  tableData: null,
  viewMode: 'chart' as const,
}

beforeEach(() => {
  useAppStore.setState(initialState)
})

describe('session actions', () => {
  it('creates and selects a session', () => {
    const session = useAppStore.getState().createSession('Test')
    const state = useAppStore.getState()
    expect(state.sessions).toHaveLength(1)
    expect(state.currentSessionId).toBe(session.id)
  })

  it('renames a session', () => {
    const session = useAppStore.getState().createSession('Old')
    useAppStore.getState().renameSession(session.id, 'New')
    expect(useAppStore.getState().sessions[0].title).toBe('New')
  })

  it('deletes the active session and selects the next one', () => {
    const first = useAppStore.getState().createSession('First')
    const second = useAppStore.getState().createSession('Second')
    useAppStore.getState().deleteSession(first.id)
    const state = useAppStore.getState()
    expect(state.sessions).toHaveLength(1)
    expect(state.currentSessionId).toBe(second.id)
  })

  it('auto-titles from the first message', () => {
    const session = useAppStore.getState().createSession()
    useAppStore.getState().autoTitleFromMessage(session.id, 'This is a long first question')
    expect(useAppStore.getState().sessions[0].title).toBe('This is a long first question')
  })
})

describe('message actions', () => {
  it('adds a message with generated id and created_at', () => {
    useAppStore.getState().addMessage({ role: 'user', content: 'Hello' })
    const [message] = useAppStore.getState().messages
    expect(message.role).toBe('user')
    expect(message.content).toBe('Hello')
    expect(message.id).toBeTruthy()
    expect(message.created_at).toBeTruthy()
  })

  it('updates the last message content', () => {
    useAppStore.getState().addMessage({ role: 'assistant', content: '' })
    useAppStore.getState().updateLastMessageContent('Streamed text')
    expect(useAppStore.getState().messages[0].content).toBe('Streamed text')
  })
})

describe('chart actions', () => {
  it('sets chart config, table data, and view mode', () => {
    useAppStore.getState().setChartConfig({ type: 'bar', title: 'T', data: [] })
    useAppStore.getState().setTableData({ columns: ['A'], rows: [{ name: 'a', value: 1 }] })
    useAppStore.getState().setViewMode('table')
    const state = useAppStore.getState()
    expect(state.chartConfig?.type).toBe('bar')
    expect(state.tableData?.columns).toEqual(['A'])
    expect(state.viewMode).toBe('table')
  })

  it('clears chart data', () => {
    useAppStore.getState().setChartConfig({ type: 'line', title: 'T', data: [] })
    useAppStore.getState().clearChartData()
    expect(useAppStore.getState().chartConfig).toBeNull()
    expect(useAppStore.getState().tableData).toBeNull()
  })
})
