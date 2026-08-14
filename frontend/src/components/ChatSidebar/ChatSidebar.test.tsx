import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { useAppStore } from '../../store/useAppStore'
import ChatSidebar from './index'

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
  it('creates a session with the New Session button', () => {
    render(<ChatSidebar />)
    fireEvent.click(screen.getByText('New Session'))
    expect(useAppStore.getState().sessions).toHaveLength(1)
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

  it('deletes a session', () => {
    useAppStore.getState().createSession('To Delete')
    render(<ChatSidebar />)
    fireEvent.mouseEnter(screen.getByText('To Delete'))
    fireEvent.click(screen.getByTitle('Delete'))
    expect(useAppStore.getState().sessions).toHaveLength(0)
  })
})
