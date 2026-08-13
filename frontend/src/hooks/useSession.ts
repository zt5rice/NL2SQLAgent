import { useCallback, useState } from 'react'
import type { Session } from '../types'

const generateId = () => Math.random().toString(36).substring(2, 15)

const now = () => new Date().toISOString()

/**
 * Local session state management.
 *
 * Backend persistence and the shared Zustand store are added in later
 * tickets (ZHA-14/ZHA-15); this hook keeps ZHA-11 self-contained.
 */
export function useSession() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)

  const createSession = useCallback((title?: string): Session => {
    const session: Session = {
      id: generateId(),
      title: title?.trim() || 'New Session',
      created_at: now(),
      updated_at: now(),
      message_count: 0,
    }
    setSessions((prev) => [session, ...prev])
    setCurrentSessionId(session.id)
    return session
  }, [])

  const selectSession = useCallback((id: string) => {
    setCurrentSessionId(id)
  }, [])

  const renameSession = useCallback((id: string, title: string) => {
    const trimmed = title.trim()
    if (!trimmed) return
    setSessions((prev) =>
      prev.map((s) =>
        s.id === id ? { ...s, title: trimmed, updated_at: now() } : s,
      ),
    )
  }, [])

  const deleteSession = useCallback(
    (id: string) => {
      const remaining = sessions.filter((s) => s.id !== id)
      setSessions(remaining)
      setCurrentSessionId((cur) => (cur === id ? (remaining[0]?.id ?? null) : cur))
    },
    [sessions],
  )

  /**
   * Auto-title a session from its first user message.
   * Called by the chat flow once messaging exists (ZHA-12).
   */
  const autoTitleFromMessage = useCallback(
    (id: string, content: string) => {
      const title = content.slice(0, 30) + (content.length > 30 ? '...' : '')
      renameSession(id, title)
    },
    [renameSession],
  )

  return {
    sessions,
    currentSessionId,
    createSession,
    selectSession,
    renameSession,
    deleteSession,
    autoTitleFromMessage,
  }
}
