import { useCallback } from 'react'
import { useAppStore } from '../store/useAppStore'
import type { ChartConfig, TableData } from '../types'

/**
 * Chat actions backed by the shared Zustand store.
 *
 * SSE streaming from the backend replaces the placeholder reply in ZHA-15.
 */
const DEMO_CHART: ChartConfig = {
  type: 'bar',
  title: 'Monthly Sales',
  data: [
    { name: 'Jan', value: 1200 },
    { name: 'Feb', value: 900 },
    { name: 'Mar', value: 1500 },
    { name: 'Apr', value: 1100 },
    { name: 'May', value: 1800 },
    { name: 'Jun', value: 1600 },
  ],
}

const DEMO_TABLE: TableData = {
  columns: ['Month', 'Sales'],
  rows: DEMO_CHART.data,
}

export function useChat() {
  const messages = useAppStore((s) => s.messages)
  const isStreaming = useAppStore((s) => s.isStreaming)
  const addMessage = useAppStore((s) => s.addMessage)
  const setStreaming = useAppStore((s) => s.setStreaming)
  const setChartConfig = useAppStore((s) => s.setChartConfig)
  const setTableData = useAppStore((s) => s.setTableData)
  const clearChartData = useAppStore((s) => s.clearChartData)

  const sendMessage = useCallback(
    (content: string) => {
      addMessage({ role: 'user', content })
      clearChartData()
      setStreaming(true)

      // Placeholder assistant reply + demo chart until SSE streaming is wired up (ZHA-15).
      setTimeout(() => {
        addMessage({
          role: 'assistant',
          content:
            'This is a **placeholder** reply. Streaming responses from the LLM will be wired up in a later ticket.',
        })
        setChartConfig(DEMO_CHART)
        setTableData(DEMO_TABLE)
        setStreaming(false)
      }, 300)
    },
    [addMessage, setStreaming, setChartConfig, setTableData, clearChartData],
  )

  return { messages, isStreaming, sendMessage }
}
