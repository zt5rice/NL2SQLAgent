import { useCallback, useEffect } from 'react'
import { api } from '../services/api'
import { useAppStore } from '../store/useAppStore'
import type { Message } from '../types'

/**
 * Session operations backed by the backend REST API.
 *
 * Loads sessions on mount, and keeps the local store in sync with the backend
 * for create / select / rename / delete. Network failures fall back to local
 * store behavior so the UI stays usable offline.
 */
export function useSession() {
  const sessions = useAppStore((s) => s.sessions)
  const currentSessionId = useAppStore((s) => s.currentSessionId)
  const selectSession = useAppStore((s) => s.selectSession)
  const addSession = useAppStore((s) => s.addSession)
  const setSessions = useAppStore((s) => s.setSessions)
  const setMessages = useAppStore((s) => s.setMessages)
  const clearMessages = useAppStore((s) => s.clearMessages)
  const clearChartData = useAppStore((s) => s.clearChartData)
  const setChartConfig = useAppStore((s) => s.setChartConfig)
  const setTableData = useAppStore((s) => s.setTableData)
  const setViewMode = useAppStore((s) => s.setViewMode)
  const renameSession = useAppStore((s) => s.renameSession)
  const deleteSession = useAppStore((s) => s.deleteSession)

  const restoreVisualsFromMessages = useCallback(
    (messages: Message[]) => {
      const lastAssistant = [...messages]
        .reverse()
        .find((m) => m.role === 'assistant')
      if (lastAssistant?.data_json && lastAssistant?.chart_json) {
        try {
          setChartConfig(JSON.parse(lastAssistant.chart_json))
          setTableData(JSON.parse(lastAssistant.data_json))
          setViewMode('chart')
          return
        } catch {
          // Malformed persisted payloads are ignored below.
        }
      }
      clearChartData()
    },
    [setChartConfig, setTableData, setViewMode, clearChartData],
  )

  useEffect(() => {
    let cancelled = false
    api.session
      .list()
      .then((list) => {
        if (cancelled) return
        setSessions(list)
        if (list.length > 0 && !useAppStore.getState().currentSessionId) {
          const first = list[0]
          selectSession(first.id)
          api.session
            .getMessages(first.id)
            .then((messages) => {
              if (cancelled) return
              setMessages(messages)
              restoreVisualsFromMessages(messages)
            })
            .catch(() => {})
        }
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [setSessions, selectSession, setMessages, restoreVisualsFromMessages])

  const handleCreate = useCallback(
    async (title?: string) => {
      try {
        const session = await api.session.create(title)
        addSession(session)
        clearMessages()
        clearChartData()
        return session
      } catch {
        // Offline fallback: local session keeps the demo flow usable.
        return useAppStore.getState().createSession(title)
      }
    },
    [addSession, clearMessages, clearChartData],
  )

  const handleSelect = useCallback(
    (id: string) => {
      selectSession(id)
      clearMessages()
      clearChartData()
      api.session
        .getMessages(id)
        .then((messages) => {
          setMessages(messages)
          restoreVisualsFromMessages(messages)
        })
        .catch(() => setMessages([]))
    },
    [selectSession, clearMessages, clearChartData, setMessages, restoreVisualsFromMessages],
  )

  const handleRename = useCallback(
    (id: string, title: string) => {
      renameSession(id, title)
      api.session.update(id, { title }).catch(() => {})
    },
    [renameSession],
  )

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await api.session.delete(id)
      } catch {
        // Delete locally even when the backend is unreachable.
      }
      deleteSession(id)
      clearChartData()
    },
    [deleteSession, clearChartData],
  )

  return {
    sessions,
    currentSessionId,
    createSession: handleCreate,
    selectSession: handleSelect,
    renameSession: handleRename,
    deleteSession: handleDelete,
  }
}
