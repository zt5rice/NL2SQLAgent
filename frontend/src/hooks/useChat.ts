import { useCallback, useState } from 'react'
import type { Message } from '../types'

const generateId = () => Math.random().toString(36).substring(2, 15)

const now = () => new Date().toISOString()

/**
 * Local chat state for the Q&A area.
 *
 * SSE streaming from the backend and the shared Zustand store are added in
 * later tickets (ZHA-14/ZHA-15); this hook keeps ZHA-12 self-contained.
 */
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = useCallback((content: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      created_at: now(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Placeholder assistant reply until SSE streaming is wired up (ZHA-15).
    setIsStreaming(true)
    setTimeout(() => {
      const reply: Message = {
        id: generateId(),
        role: 'assistant',
        content:
          'This is a **placeholder** reply. Streaming responses from the LLM will be wired up in a later ticket.',
        created_at: now(),
      }
      setMessages((prev) => [...prev, reply])
      setIsStreaming(false)
    }, 300)
  }, [])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, isStreaming, sendMessage, clearMessages }
}
