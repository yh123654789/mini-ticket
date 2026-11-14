export type TicketStatus = 'open' | 'in_progress' | 'done'
export type TicketPriority = 'low' | 'medium' | 'high'
export type TicketCategory = 'bug' | 'feature' | 'consult' | 'other'
export type AIStatus = 'ok' | 'failed'

export interface User {
  id: number
  name: string
  email: string
}

export interface Ticket {
  id: number
  title: string
  description: string
  status: TicketStatus
  priority: TicketPriority
  summary: string
  category: TicketCategory
  ai_status: AIStatus
  owner_id: number
  created_at: string
  updated_at: string
}

export interface TicketPage {
  items: Ticket[]
  total: number
  page: number
  page_size: number
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface TicketCreatePayload {
  title: string
  description: string
  priority: TicketPriority
}

export const STATUS_LABELS: Record<TicketStatus, string> = {
  open: '待处理',
  in_progress: '处理中',
  done: '已完成',
}

export const PRIORITY_LABELS: Record<TicketPriority, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

export const CATEGORY_LABELS: Record<TicketCategory, string> = {
  bug: '缺陷',
  feature: '需求',
  consult: '咨询',
  other: '其他',
}
