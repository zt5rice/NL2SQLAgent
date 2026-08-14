import { useCallback } from 'react'
import { api } from '../services/api'
import { useAppStore } from '../store/useAppStore'
import type { ChartConfig, TableData } from '../types'

/**
 * Chat actions backed by the shared Zustand store.
 *
 * Sends the message through the SSE chat client; falls back to a local
 * placeholder until the backend /api/chat endpoint is available (Phase 3).
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
  rows: DEMO_CHART.data.map((d) => [d.name, d.value]),
}

const PLACEHOLDER_REPLY =
  'This is a **placeholder** reply. The backend chat API will be wired up in Phase 3.'

export function useChat() {
  const messages = useAppStore((s) => s.messages)
  const isStreaming = useAppStore((s) => s.isStreaming)
  const currentSessionId = useAppStore((s) => s.currentSessionId)
  const addMessage = useAppStore((s) => s.addMessage)
  const updateLastMessageContent = useAppStore((s) => s.updateLastMessageContent)
  const updateLastMessageSql = useAppStore((s) => s.updateLastMessageSql)
  const setStreaming = useAppStore((s) => s.setStreaming)
  const setChartConfig = useAppStore((s) => s.setChartConfig)
  const setTableData = useAppStore((s) => s.setTableData)
  const clearChartData = useAppStore((s) => s.clearChartData)

  const runFallback = useCallback(() => {
    updateLastMessageContent(PLACEHOLDER_REPLY)
    setChartConfig(DEMO_CHART)
    setTableData(DEMO_TABLE)
    setStreaming(false)
  }, [updateLastMessageContent, setChartConfig, setTableData, setStreaming])

  const sendMessage = useCallback(
    (content: string) => {
      addMessage({ role: 'user', content })
      clearChartData()
      setStreaming(true)
      addMessage({ role: 'assistant', content: '' })

      const sse = api.chat({ session_id: currentSessionId ?? 'local', message: content })
      let fullText = ''
      let finished = false

      const finish = () => {
        if (finished) return
        finished = true
        setStreaming(false)
      }

      sse
        .start({
          onText: (delta) => {
            fullText += delta
            updateLastMessageContent(fullText)
          },
          onSql: (sql) => updateLastMessageSql(sql),
          onData: (data) => setTableData(data),
          onChart: (config) => setChartConfig(config),
          onError: () => finish(),
          onDone: () => {
            if (!fullText) updateLastMessageContent(PLACEHOLDER_REPLY)
            finish()
          },
        })
        .catch(() => {
          // Backend /api/chat is not available until Phase 3; fall back to the local demo.
          runFallback()
        })
    },
    [
      currentSessionId,
      addMessage,
      updateLastMessageContent,
      updateLastMessageSql,
      setStreaming,
      setChartConfig,
      setTableData,
      clearChartData,
      runFallback,
    ],
  )

  return { messages, isStreaming, sendMessage }
}
