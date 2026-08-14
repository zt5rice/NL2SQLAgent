import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAppStore } from '../store/useAppStore'
import { useSession } from './useSession'

const session = {
  id: 's1',
  title: 'Backend Session',
  created_at: '2026-08-14T00:00:00',
  updated_at: '2026-08-14T00:00:00',
}

const persistedMessages = [
  {
    id: 1,
    session_id: 's1',
    role: 'user',
    content: 'hi',
    sql_query: null,
    data_json: null,
    chart_json: null,
    created_at: '2026-08-14T00:00:00',
  },
  {
    id: 2,
    session_id: 's1',
    role: 'assistant',
    content: 'answer',
    sql_query: 'SELECT 1',
    data_json: JSON.stringify({ columns: ['a'], rows: [['x', 1]], raw: '[]' }),
    chart_json: JSON.stringify({ type: 'bar', title: 'T', data: [{ name: 'x', value: 1 }] }),
    created_at: '2026-08-14T00:00:00',
  },
]

vi.mock('../services/api', () => ({
  api: {
    session: {
      list: vi.fn(async () => [session]),
      create: vi.fn(async () => session),
      update: vi.fn(async () => session),
      delete: vi.fn(async () => undefined),
      getMessages: vi.fn(async () => persistedMessages),
    },
    database: {},
    chat: {},
  },
}))

import { api } from '../services/api'

const mockedSessionApi = api.session as {
  list: ReturnType<typeof vi.fn>
  create: ReturnType<typeof vi.fn>
  update: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
  getMessages: ReturnType<typeof vi.fn>
}

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
  vi.clearAllMocks()
})

describe('useSession', () => {
  it('loads sessions and the first session messages on mount', async () => {
    renderHook(() => useSession())
    await waitFor(() => {
      expect(useAppStore.getState().sessions).toHaveLength(1)
    })
    expect(useAppStore.getState().currentSessionId).toBe('s1')
    await waitFor(() => {
      expect(useAppStore.getState().messages).toHaveLength(2)
    })
    expect(mockedSessionApi.getMessages).toHaveBeenCalledWith('s1')
    // Chart/table data is restored from the last assistant message.
    expect(useAppStore.getState().chartConfig?.type).toBe('bar')
    expect(useAppStore.getState().tableData?.columns).toEqual(['a'])
    expect(useAppStore.getState().viewMode).toBe('chart')
  })

  it('creates a session through the backend', async () => {
    const { result } = renderHook(() => useSession())
    await act(async () => {
      await result.current.createSession('New')
    })
    expect(mockedSessionApi.create).toHaveBeenCalledWith('New')
    expect(useAppStore.getState().sessions[0].title).toBe('Backend Session')
  })

  it('selects a session and loads its messages', async () => {
    useAppStore.setState({ sessions: [session] })
    const { result } = renderHook(() => useSession())
    await act(async () => {
      result.current.selectSession('s1')
    })
    expect(useAppStore.getState().currentSessionId).toBe('s1')
    await waitFor(() => {
      expect(useAppStore.getState().messages[0].content).toBe('hi')
    })
    expect(useAppStore.getState().chartConfig?.type).toBe('bar')
  })

  it('renames a session locally and on the backend', async () => {
    useAppStore.setState({ sessions: [session] })
    const { result } = renderHook(() => useSession())
    act(() => {
      result.current.renameSession('s1', 'Renamed')
    })
    expect(useAppStore.getState().sessions[0].title).toBe('Renamed')
    expect(mockedSessionApi.update).toHaveBeenCalledWith('s1', { title: 'Renamed' })
  })

  it('deletes a session on the backend and locally', async () => {
    useAppStore.setState({ sessions: [session], currentSessionId: 's1' })
    const { result } = renderHook(() => useSession())
    await act(async () => {
      await result.current.deleteSession('s1')
    })
    expect(mockedSessionApi.delete).toHaveBeenCalledWith('s1')
    expect(useAppStore.getState().sessions).toHaveLength(0)
  })
})
