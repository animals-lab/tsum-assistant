export interface Message {
  role: 'user' | 'assistant'
  content: string
  function_call?: any
  name?: string
} 