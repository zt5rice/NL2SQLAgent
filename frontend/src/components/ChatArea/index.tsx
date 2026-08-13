export default function ChatArea() {
  return (
    <main className="flex-1 flex flex-col bg-slate-800 min-w-0">
      <div className="h-14 border-b border-slate-700/50 flex items-center px-6 shrink-0">
        <h2 className="text-sm text-slate-300">Chat</h2>
      </div>
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <p className="text-sm text-slate-500">Start a conversation with your database</p>
          <p className="text-xs text-slate-600 mt-1">
            Ask questions in natural language and see the results as charts.
          </p>
        </div>
      </div>
    </main>
  )
}
