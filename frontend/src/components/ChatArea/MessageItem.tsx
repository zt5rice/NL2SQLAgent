import ReactMarkdown from 'react-markdown'
import type { Message } from '../../types'

interface MessageItemProps {
  message: Message
}

export default function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-slate-800 text-slate-200 border border-slate-700/60'
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="markdown-body">
            {message.sql_query && (
              <details className="mb-2 rounded-lg bg-slate-950/70 border border-slate-700/60 overflow-hidden">
                <summary className="px-3 py-1.5 text-xs font-medium text-cyan-400 cursor-pointer select-none">
                  View SQL
                </summary>
                <pre className="px-3 py-2 text-xs text-slate-300 overflow-x-auto">
                  <code>{message.sql_query}</code>
                </pre>
              </details>
            )}
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
