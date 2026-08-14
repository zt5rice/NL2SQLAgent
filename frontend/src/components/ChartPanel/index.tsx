import { BarChart3, LineChart, PieChart } from 'lucide-react'
import type { ReactNode } from 'react'
import { useAppStore } from '../../store/useAppStore'
import type { ChartType } from '../../types'
import Chart from './Chart'
import DataTable from './DataTable'

export default function ChartPanel() {
  const messages = useAppStore((s) => s.messages)
  const chartConfig = useAppStore((s) => s.chartConfig)
  const tableData = useAppStore((s) => s.tableData)
  const viewMode = useAppStore((s) => s.viewMode)
  const setViewMode = useAppStore((s) => s.setViewMode)
  const setChartConfig = useAppStore((s) => s.setChartConfig)

  const hasData = chartConfig || tableData
  const hasChartData = chartConfig && chartConfig.data.length > 0
  const hasTableData = tableData && tableData.rows.length > 0
  const lastSql =
    [...messages]
      .reverse()
      .find((m) => m.role === 'assistant' && m.sql_query)?.sql_query ?? null

  const chartTypes: { type: ChartType; icon: ReactNode; label: string }[] = [
    { type: 'bar', icon: <BarChart3 className="w-4 h-4" />, label: 'Bar' },
    { type: 'line', icon: <LineChart className="w-4 h-4" />, label: 'Line' },
    { type: 'pie', icon: <PieChart className="w-4 h-4" />, label: 'Pie' },
  ]

  return (
    <aside className="w-96 h-full bg-slate-900 border-l border-slate-700/50 flex flex-col shrink-0">
      <div className="h-14 border-b border-slate-700/50 flex items-center justify-between px-4 shrink-0">
        <h2 className="text-sm text-slate-300">Data Visualization</h2>
        <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('chart')}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
              viewMode === 'chart'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Chart
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
              viewMode === 'table'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Table
          </button>
        </div>
      </div>

      {lastSql && (
        <div className="px-4 py-3 border-b border-slate-700/50">
          <div className="rounded-lg bg-slate-950/70 border border-slate-700/60 overflow-hidden">
            <div className="px-3 py-1.5 text-xs font-medium text-cyan-400 border-b border-slate-700/50">
              SQL
            </div>
            <pre className="px-3 py-2 text-xs text-slate-300 overflow-x-auto max-h-28 overflow-y-auto whitespace-pre-wrap break-all">
              <code>{lastSql}</code>
            </pre>
          </div>
        </div>
      )}

      {viewMode === 'chart' && hasChartData && (
        <div className="px-4 py-3 border-b border-slate-700/50 flex gap-2">
          {chartTypes.map(({ type, icon, label }) => (
            <button
              key={type}
              onClick={() => chartConfig && setChartConfig({ ...chartConfig, type })}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                chartConfig?.type === type
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'bg-slate-800 text-slate-400 hover:text-white border border-transparent'
              }`}
            >
              {icon}
              {label}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 p-4 min-h-0">
        {!hasData ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500">
            <p className="text-sm">No data yet</p>
            <p className="text-xs mt-1 text-slate-600">Ask a question to see results here</p>
          </div>
        ) : viewMode === 'chart' ? (
          hasChartData ? (
            <div className="h-full bg-slate-800/50 rounded-xl p-4">
              <Chart config={chartConfig!} />
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-sm">
              No chart data
            </div>
          )
        ) : hasTableData ? (
          <div className="h-full bg-slate-800/50 rounded-xl overflow-hidden">
            <DataTable data={tableData!} />
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm">
            No table data
          </div>
        )}
      </div>
    </aside>
  )
}
