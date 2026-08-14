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

  it('renders the SQL block for assistant messages with sql_query', () => {
    render(
      <MessageItem
        message={{
          id: '3',
          role: 'assistant',
          content: 'Here are the results.',
          sql_query: 'SELECT product_name FROM sales LIMIT 3',
        }}
      />,
    )
    expect(screen.getByText('View SQL')).toBeTruthy()
    expect(screen.getByText('SELECT product_name FROM sales LIMIT 3')).toBeTruthy()
  })
})
