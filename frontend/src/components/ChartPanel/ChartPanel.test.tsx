import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAppStore } from '../../store/useAppStore'
import ChartPanel from './index'

// ECharts needs a canvas; stub it so tests focus on panel behavior.
vi.mock('./Chart', () => ({
  default: () => <div data-testid="mock-chart">Chart</div>,
}))

const chartConfig = {
  type: 'bar' as const,
  title: 'Sales by Category',
  data: [
    { name: 'A', value: 10 },
    { name: 'B', value: 20 },
  ],
  xField: 'category',
  yField: 'total',
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
})

describe('ChartPanel', () => {
  it('renders the chart when chart data is available', () => {
    useAppStore.setState({ chartConfig })
    render(<ChartPanel />)
    expect(screen.getByTestId('mock-chart')).toBeTruthy()
  })

  it('switches chart types by updating the store config', () => {
    useAppStore.setState({ chartConfig })
    render(<ChartPanel />)
    fireEvent.click(screen.getByText('Pie'))
    expect(useAppStore.getState().chartConfig?.type).toBe('pie')
    fireEvent.click(screen.getByText('Line'))
    expect(useAppStore.getState().chartConfig?.type).toBe('line')
  })

  it('toggles between chart and table views', () => {
    useAppStore.setState({
      chartConfig,
      tableData: { columns: ['category', 'total'], rows: [['A', 10]] },
    })
    render(<ChartPanel />)
    expect(screen.getByTestId('mock-chart')).toBeTruthy()

    fireEvent.click(screen.getByText('Table'))
    expect(screen.getByText('A')).toBeTruthy()
    expect(useAppStore.getState().viewMode).toBe('table')

    fireEvent.click(screen.getByText('Chart'))
    expect(screen.getByTestId('mock-chart')).toBeTruthy()
  })

  it('shows empty state when no data exists', () => {
    render(<ChartPanel />)
    expect(screen.getByText('No data yet')).toBeTruthy()
  })

  it('shows a generating placeholder while streaming with no data', () => {
    useAppStore.setState({ isStreaming: true })
    render(<ChartPanel />)
    expect(screen.getByText('Generating results…')).toBeTruthy()
    expect(screen.queryByText('No data yet')).toBeNull()
  })

  it('shows the idle empty state when not streaming and no data', () => {
    useAppStore.setState({ isStreaming: false })
    render(<ChartPanel />)
    expect(screen.getByText('No data yet')).toBeTruthy()
    expect(screen.queryByText('Generating results…')).toBeNull()
  })

  it('shows the SQL of the last assistant message', () => {
    useAppStore.setState({
      messages: [
        { id: 1, role: 'user', content: 'hi' },
        {
          id: 2,
          role: 'assistant',
          content: 'answer',
          sql_query: 'SELECT category, SUM(quantity) FROM sales GROUP BY category',
        },
      ],
    })
    render(<ChartPanel />)
    expect(screen.getByText('SQL')).toBeTruthy()
    expect(
      screen.getByText('SELECT category, SUM(quantity) FROM sales GROUP BY category'),
    ).toBeTruthy()
  })
})
