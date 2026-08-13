export default function ChatSidebar() {
  return (
    <aside className="w-64 h-full bg-slate-900 border-r border-slate-700/50 flex flex-col shrink-0">
      <div className="p-4 border-b border-slate-700/50">
        <h1 className="text-sm font-semibold text-white">Data Analysis Assistant</h1>
        <p className="text-xs text-slate-500">NL2SQL Agent</p>
      </div>
      <div className="flex-1 overflow-y-auto flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-sm text-slate-600">No sessions yet</p>
          <p className="text-xs text-slate-700 mt-1">Start a new conversation to begin</p>
        </div>
      </div>
    </aside>
  )
}
