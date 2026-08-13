// 会话类型 - 匹配后端 snake_case
export interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

// 消息类型 - 匹配后端
export interface Message {
  id: number | string
  session_id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sql_query?: string
  created_at?: string
}
