import { Loader2, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

interface ChatInputProps {
  onSend: (content: string) => void
  disabled?: boolean
  isStreaming?: boolean
}

export default function ChatInput({ onSend, disabled, isStreaming }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }, [input])

  const handleSubmit = () => {
    const trimmed = input.trim()
    if (trimmed && !disabled && !isStreaming) {
      onSend(trimmed)
      setInput('')
    }
  }

  return (
    <div className="border-t border-slate-700/50 bg-slate-900/50 p-4">
      <div className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-3 bg-slate-800 rounded-xl border border-slate-700/50 focus-within:border-blue-500/50 transition-colors">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
            placeholder="Ask a question about your data... (Enter to send, Shift+Enter for newline)"
            disabled={disabled || isStreaming}
            rows={1}
            className="flex-1 bg-transparent text-white placeholder-slate-500 px-4 py-3 resize-none outline-none disabled:opacity-50"
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || disabled || isStreaming}
            className="m-2 p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white disabled:text-slate-500 transition-colors"
          >
            {isStreaming ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
