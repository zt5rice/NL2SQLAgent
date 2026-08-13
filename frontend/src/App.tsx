import ChatArea from './components/ChatArea'
import ChatSidebar from './components/ChatSidebar'
import ChartPanel from './components/ChartPanel'

function App() {
  return (
    <div className="h-screen flex bg-slate-900 text-white overflow-hidden">
      {/* 左侧 - 会话管理 */}
      <ChatSidebar />
      {/* 中间 - 问答区域 */}
      <ChatArea />
      {/* 右侧 - 可视化图表 */}
      <ChartPanel />
    </div>
  )
}

export default App
