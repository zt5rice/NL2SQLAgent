export default function ChatSidebar() {
  return (
    <aside className="w-64 h-full bg-slate-900 border-r border-slate-700/50 flex flex-col">
      <div className="p-4 border-b border-slate-700/50">
        <h1 className="text-sm font-semibold text-white">数据分析助理</h1>
        <p className="text-xs text-slate-500">NL2SQL Agent</p>
      </div>
      <div className="flex-1 flex items-center justify-center text-slate-600 text-sm">
        会话列表占位
      </div>
    </aside>
  )
}
