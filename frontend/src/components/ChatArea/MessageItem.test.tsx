import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import MessageItem from './MessageItem'

describe('MessageItem', () => {
  it('renders user message as plain text', () => {
    render(<MessageItem message={{ id: '1', role: 'user', content: 'Hello there' }} />)
    expect(screen.getByText('Hello there')).toBeTruthy()
  })

  it('renders assistant markdown', () => {
    render(
      <MessageItem
        message={{ id: '2', role: 'assistant', content: 'Result is **bold** and `code`.' }}
      />,
    )
    expect(screen.getByText('bold')).toBeTruthy()
    expect(screen.getByText('code')).toBeTruthy()
  })
})
