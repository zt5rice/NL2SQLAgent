import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '../../types'

interface MessageItemProps {
  message: Message
  streaming?: boolean
}

export default function MessageItem({ message, streaming = false }: MessageItemProps) {
  const isUser = message.role === 'user'
  const isError = message.isError
  const showPlainText = isUser || (streaming && message.role === 'assistant')

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[75%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-blue-600 text-white'
            : isError
              ? 'bg-red-950/60 text-red-200 border border-red-500/40'
              : 'bg-slate-800 text-slate-200 border border-slate-700/60'
        }`}
      >
        {showPlainText ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
