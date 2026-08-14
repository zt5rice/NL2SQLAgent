import { useCallback } from 'react'
import { api } from '../services/api'
import { useAppStore } from '../store/useAppStore'

/**
 * Chat actions backed by the shared Zustand store.
 *
 * Sends the message through the SSE chat client and renders the streamed
 * answer. Failures and backend error events are surfaced as error bubbles.
 */
const CONNECTION_ERROR =
  'Connection failed. Please make sure the backend is running on http://localhost:8000 and try again.'

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
  const setViewMode = useAppStore((s) => s.setViewMode)
  const clearChartData = useAppStore((s) => s.clearChartData)
  const patchLastMessage = useAppStore((s) => s.patchLastMessage)

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

      const showError = (message: string) => {
        patchLastMessage({ content: `⚠️ ${message}`, isError: true })
        finish()
      }

      sse
        .start({
          onText: (delta) => {
            fullText += delta
            updateLastMessageContent(fullText)
          },
          onSql: (sql) => updateLastMessageSql(sql),
          onData: (data) => setTableData(data),
          onChart: (config) => {
            setChartConfig(config)
            // New results render as a chart by default; the user can still
            // switch to the table view manually afterwards.
            setViewMode('chart')
          },
          onError: (message) => showError(message),
          onDone: () => {
            const messages = useAppStore.getState().messages
            const last = messages[messages.length - 1]
            if (!fullText && !last?.isError) {
              updateLastMessageContent('No response generated.')
            }
            finish()
          },
        })
        .catch(() => showError(CONNECTION_ERROR))
    },
    [
      currentSessionId,
      addMessage,
      updateLastMessageContent,
      updateLastMessageSql,
      patchLastMessage,
      setStreaming,
      setChartConfig,
      setTableData,
      setViewMode,
      clearChartData,
    ],
  )

  return { messages, isStreaming, sendMessage }
}
