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
