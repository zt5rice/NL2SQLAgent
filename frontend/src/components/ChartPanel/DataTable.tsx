import type { TableData } from '../../types'

interface DataTableProps {
  data: TableData
}

export default function DataTable({ data }: DataTableProps) {
  const { columns, rows, raw } = data
  const displayRows =
    raw && raw.length > 0 ? raw : rows.map((row) => [row.name, row.value])

  if (displayRows.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        No data
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-0 bg-slate-800">
          <tr>
            {columns.map((col, idx) => (
              <th
                key={`${col}-${idx}`}
                className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-700"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/50">
          {displayRows.map((row, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-slate-800/50 transition-colors">
              {row.map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  className="px-4 py-3 text-sm text-slate-300 whitespace-nowrap"
                >
                  {String(cell ?? '-')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
