import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAppStore } from '../store/useAppStore'
import { useChat } from './useChat'

const chartConfig = {
  type: 'pie' as const,
  title: 'Top Products',
  data: [{ name: 'Pen', value: 500 }],
  xField: 'product_name',
  yField: 'total_quantity',
}

const startMock = vi.fn()

vi.mock('../services/api', () => ({
  api: {
    session: {},
    database: {},
    chat: (..._args: unknown[]) => ({
      start: (...handlerArgs: unknown[]) => startMock(...handlerArgs),
    }),
  },
}))

const initialState = {
  sessions: [],
  currentSessionId: 's1',
  messages: [],
  isStreaming: false,
  chartConfig: null,
  tableData: null,
  viewMode: 'table' as const,
}

beforeEach(() => {
  useAppStore.setState(initialState)
  startMock.mockReset()
})

describe('useChat SSE binding', () => {
  it('streams text into the last assistant message', async () => {
    startMock.mockImplementation(async ({ onText }: { onText: (t: string) => void }) => {
      onText('Top ')
      onText('products')
    })
    const { result } = renderHook(() => useChat())
    await act(async () => {
      result.current.sendMessage('What are the top products?')
    })
    const last = useAppStore.getState().messages[useAppStore.getState().messages.length - 1]
    expect(last.role).toBe('assistant')
    expect(last.content).toBe('Top products')
  })

  it('stores sql_query from the sql event', async () => {
    startMock.mockImplementation(async ({ onSql }: { onSql: (s: string) => void }) => {
      onSql('SELECT product_name FROM sales LIMIT 5')
    })
    const { result } = renderHook(() => useChat())
    await act(async () => {
      result.current.sendMessage('hi')
    })
    const last = useAppStore.getState().messages[useAppStore.getState().messages.length - 1]
    expect(last.sql_query).toBe('SELECT product_name FROM sales LIMIT 5')
  })

  it('binds the chart event and switches to the chart view', async () => {
    startMock.mockImplementation(async ({ onChart }: { onChart: (c: typeof chartConfig) => void }) => {
      onChart(chartConfig)
    })
    const { result } = renderHook(() => useChat())
    await act(async () => {
      result.current.sendMessage('hi')
    })
    const state = useAppStore.getState()
    expect(state.chartConfig?.type).toBe('pie')
    expect(state.chartConfig?.data[0].name).toBe('Pen')
    expect(state.viewMode).toBe('chart')
  })

  it('binds the data event to the table store', async () => {
    startMock.mockImplementation(async ({ onData }: { onData: (d: unknown) => void }) => {
      onData({ columns: ['product_name', 'total'], rows: [['Pen', 500]], raw: "[]" })
    })
    const { result } = renderHook(() => useChat())
    await act(async () => {
      result.current.sendMessage('hi')
    })
    const state = useAppStore.getState()
    expect(state.tableData?.columns).toEqual(['product_name', 'total'])
    expect(state.tableData?.rows[0]).toEqual(['Pen', 500])
  })
})
