// Session type - matches backend snake_case
export interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

// Message type - matches backend
export interface Message {
  id: number | string
  session_id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sql_query?: string
  created_at?: string
}

// Chart types
export type ChartType = 'bar' | 'line' | 'pie' | 'table'

// Chart configuration
export interface ChartConfig {
  type: ChartType
  title: string
  data: Array<{ name: string; value: number | string }>
  xField?: string
  yField?: string
}

// Table data
export interface TableData {
  columns: string[]
  rows: Array<{ name: string; value: number | string }>
  raw?: Array<Array<string | number>>
}

// Right panel view mode
export type ViewMode = 'chart' | 'table'
