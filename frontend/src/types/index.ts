// Session type - matches backend snake_case
export interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
}

// Message type - matches backend
export interface Message {
  id: number | string
  session_id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sql_query?: string
  created_at?: string
  // Frontend-only flag: renders the assistant bubble as an error state.
  isError?: boolean
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
  rows: Array<Array<string | number>>
  raw?: string
}

// Right panel view mode
export type ViewMode = 'chart' | 'table'

// Database introspection - matches backend /api/database responses
export interface DatabaseColumn {
  name: string
  type: string
  nullable: boolean
  default?: string | null
  primary_key: boolean
}

export interface DatabaseTable {
  name: string
  columns: DatabaseColumn[]
  sample_rows: Array<Record<string, unknown>>
  row_count: number
}

export interface DatabaseSchema {
  tables: DatabaseTable[]
}
