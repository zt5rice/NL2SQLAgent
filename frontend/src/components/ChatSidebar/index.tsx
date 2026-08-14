import { MessageSquarePlus } from 'lucide-react'
import { useSession } from '../../hooks/useSession'
import SessionItem from './SessionItem'

export default function ChatSidebar() {
  const { sessions, currentSessionId, createSession, selectSession, renameSession, deleteSession } =
    useSession()

  return (
    <aside className="w-64 h-full bg-slate-900 border-r border-slate-700/50 flex flex-col shrink-0">
      <div className="p-4 border-b border-slate-700/50">
        <h1 className="text-sm font-semibold text-white">Data Analysis Assistant</h1>
        <p className="text-xs text-slate-500">NL2SQL Agent</p>
      </div>

      <div className="p-3">
        <button
          onClick={() => void createSession()}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <MessageSquarePlus className="w-4 h-4" />
          New Session
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
        {sessions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-slate-600 text-sm">No sessions yet</p>
            <p className="text-slate-700 text-xs mt-1">Click &quot;New Session&quot; to start</p>
          </div>
        ) : (
          sessions.map((session) => (
            <SessionItem
              key={session.id}
              session={session}
              isActive={session.id === currentSessionId}
              onSelect={selectSession}
              onRename={renameSession}
              onDelete={deleteSession}
            />
          ))
        )}
      </div>

      <div className="p-3 border-t border-slate-700/50">
        <p className="text-xs text-slate-600 text-center">Powered by DeepSeek + LangChain</p>
      </div>
    </aside>
  )
}
