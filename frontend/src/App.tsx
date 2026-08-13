import ChatArea from './components/ChatArea'
import ChatSidebar from './components/ChatSidebar'
import ChartPanel from './components/ChartPanel'

function App() {
  return (
    <div className="h-screen flex bg-slate-900 text-white overflow-hidden">
      {/* Left - session management */}
      <ChatSidebar />
      {/* Center - Q&A area */}
      <ChatArea />
      {/* Right - visualization charts */}
      <ChartPanel />
    </div>
  )
}

export default App
