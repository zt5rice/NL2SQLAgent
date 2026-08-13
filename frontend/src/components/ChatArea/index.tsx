import { useChat } from '../../hooks/useChat'
import ChatInput from './ChatInput'
import MessageList from './MessageList'

export default function ChatArea() {
  const { messages, isStreaming, sendMessage } = useChat()

  return (
    <main className="flex-1 flex flex-col bg-slate-800 min-w-0">
      <div className="h-14 border-b border-slate-700/50 flex items-center px-6 shrink-0">
        <h2 className="text-sm text-slate-300">Chat</h2>
      </div>
      <MessageList messages={messages} />
      <ChatInput onSend={sendMessage} isStreaming={isStreaming} />
    </main>
  )
}
