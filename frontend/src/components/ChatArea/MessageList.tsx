import { useEffect, useRef } from 'react'
import type { Message } from '../../types'
import MessageItem from './MessageItem'

interface MessageListProps {
  messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center">
          <div className="text-center max-w-md">
            <p className="text-sm text-slate-500">Start a conversation with your database</p>
            <p className="text-xs text-slate-600 mt-1">
              Ask questions in natural language and see the results as charts.
            </p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageItem key={message.id} message={message} />
          ))}
          <div ref={bottomRef} />
        </>
      )}
    </div>
  )
}
