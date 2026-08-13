import { BarChart3, LineChart, PieChart } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import type { ChartConfig, ChartType, TableData, ViewMode } from '../../types'
import Chart from './Chart'
import DataTable from './DataTable'

// Placeholder demo data until query results are wired up (ZHA-15 / Phase 3).
const DEMO_CHART: ChartConfig = {
  type: 'bar',
  title: 'Monthly Sales',
  data: [
    { name: 'Jan', value: 1200 },
    { name: 'Feb', value: 900 },
    { name: 'Mar', value: 1500 },
    { name: 'Apr', value: 1100 },
    { name: 'May', value: 1800 },
    { name: 'Jun', value: 1600 },
  ],
}

const DEMO_TABLE: TableData = {
  columns: ['Month', 'Sales'],
  rows: DEMO_CHART.data,
}

export default function ChartPanel() {
  const [viewMode, setViewMode] = useState<ViewMode>('chart')
  const [chartType, setChartType] = useState<ChartType>('bar')

  const chartConfig = useMemo<ChartConfig>(
    () => ({ ...DEMO_CHART, type: chartType }),
    [chartType],
  )

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

      {viewMode === 'chart' && (
        <div className="px-4 py-3 border-b border-slate-700/50 flex gap-2">
          {chartTypes.map(({ type, icon, label }) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                chartConfig.type === type
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
        {viewMode === 'chart' ? (
          <div className="h-full bg-slate-800/50 rounded-xl p-4">
            <Chart config={chartConfig} />
          </div>
        ) : (
          <div className="h-full bg-slate-800/50 rounded-xl overflow-hidden">
            <DataTable data={DEMO_TABLE} />
          </div>
        )}
      </div>
    </aside>
  )
}
