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

vi.mock('../services/api', () => ({
  api: {
    session: {
      list: vi.fn(async () => [session]),
      create: vi.fn(async () => session),
      update: vi.fn(async () => session),
      delete: vi.fn(async () => undefined),
      getMessages: vi.fn(async () => [
        { id: 1, session_id: 's1', role: 'user', content: 'hi', sql_query: null, created_at: '2026-08-14T00:00:00' },
      ]),
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
      expect(useAppStore.getState().messages).toHaveLength(1)
    })
    expect(mockedSessionApi.getMessages).toHaveBeenCalledWith('s1')
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
