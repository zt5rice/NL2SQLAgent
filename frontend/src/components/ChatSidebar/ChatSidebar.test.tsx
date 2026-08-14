import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { vi } from 'vitest'
import { useAppStore } from '../../store/useAppStore'
import ChatSidebar from './index'

vi.mock('../../services/api', () => ({
  api: {
    session: {
      list: vi.fn(async () => []),
      create: vi.fn(async (title?: string) => ({
        id: 'backend-1',
        title: title ?? 'New Session',
        created_at: '2026-08-14T00:00:00',
        updated_at: '2026-08-14T00:00:00',
      })),
      update: vi.fn(async () => ({})),
      delete: vi.fn(async () => undefined),
      getMessages: vi.fn(async () => []),
    },
    database: {},
    chat: {},
  },
}))

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

describe('ChatSidebar', () => {
  it('creates a session with the New Session button', async () => {
    render(<ChatSidebar />)
    fireEvent.click(screen.getByText('New Session'))
    await waitFor(() => {
      expect(useAppStore.getState().sessions).toHaveLength(1)
    })
  })

  it('renames a session inline', () => {
    useAppStore.getState().createSession('Old Title')
    render(<ChatSidebar />)
    fireEvent.mouseEnter(screen.getByText('Old Title'))
    fireEvent.click(screen.getByTitle('Rename'))
    const input = screen.getByDisplayValue('Old Title') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'New Title' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(screen.getByText('New Title')).toBeTruthy()
    expect(useAppStore.getState().sessions[0].title).toBe('New Title')
  })

  it('deletes a session', async () => {
    useAppStore.getState().createSession('To Delete')
    render(<ChatSidebar />)
    fireEvent.mouseEnter(screen.getByText('To Delete'))
    fireEvent.click(screen.getByTitle('Delete'))
    await waitFor(() => {
      expect(useAppStore.getState().sessions).toHaveLength(0)
    })
  })

  it('shows the DeepSeek branding in the footer', () => {
    render(<ChatSidebar />)
    expect(screen.getByText('Powered by DeepSeek + LangChain')).toBeTruthy()
  })
})
