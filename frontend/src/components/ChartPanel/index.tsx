export default function ChartPanel() {
  return (
    <aside className="w-96 h-full bg-slate-900 border-l border-slate-700/50 flex flex-col shrink-0">
      <div className="h-14 border-b border-slate-700/50 flex items-center px-4 shrink-0">
        <h2 className="text-sm text-slate-300">Data Visualization</h2>
      </div>
      <div className="flex-1 overflow-y-auto flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-sm text-slate-600">No chart yet</p>
          <p className="text-xs text-slate-700 mt-1">Ask a question to see results here</p>
        </div>
      </div>
    </aside>
  )
}
