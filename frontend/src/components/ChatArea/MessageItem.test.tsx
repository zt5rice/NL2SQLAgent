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

  it('renders markdown headings as real heading elements', () => {
    const { container } = render(
      <MessageItem
        message={{
          id: '5',
          role: 'assistant',
          content: '## 1. Plan\n\nThe question asks about revenue.',
        }}
      />,
    )
    const heading = container.querySelector('h2')
    expect(heading).toBeTruthy()
    expect(heading?.textContent).toBe('1. Plan')
    expect(screen.getByText('The question asks about revenue.')).toBeTruthy()
  })

  it('renders error messages with an error style', () => {
    const { container } = render(
      <MessageItem
        message={{ id: '4', role: 'assistant', content: '⚠️ boom', isError: true }}
      />,
    )
    expect(screen.getByText('⚠️ boom')).toBeTruthy()
    expect(container.querySelector('.bg-red-950\\/60')).toBeTruthy()
  })

  it('renders GFM pipe tables as real table elements', () => {
    const { container } = render(
      <MessageItem
        message={{
          id: '6',
          role: 'assistant',
          content:
            '| Category | Revenue |\n|---|---|\n| Electronics | 575,396.77 |\n| Books | 52,719.46 |',
        }}
      />,
    )
    const table = container.querySelector('table')
    expect(table).toBeTruthy()
    expect(table?.querySelectorAll('tr')).toHaveLength(3)
    expect(screen.getByText('Electronics')).toBeTruthy()
    expect(screen.getByText('575,396.77')).toBeTruthy()
  })
})
