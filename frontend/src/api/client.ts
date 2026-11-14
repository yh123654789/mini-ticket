import { getToken, setToken } from './session'
import type {
  LoginResponse,
  Ticket,
  TicketCreatePayload,
  TicketPage,
  TicketPriority,
  TicketStatus,
  User,
} from './types'

/** 后端错误统一包装，页面只需要展示 message。 */
export class ApiError extends Error {
  readonly status: number
  readonly details: unknown

  constructor(status: number, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  query?: Record<string, string | number | undefined>
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = new URL(path, window.location.origin)
  if (options.query) {
    for (const [key, value] of Object.entries(options.query)) {
      if (value !== undefined && value !== '') {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const currentToken = getToken()
  if (currentToken) {
    headers.Authorization = `Bearer ${currentToken}`
  }

  let response: Response
  try {
    response = await fetch(url.toString(), {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, '无法连接后端服务，请确认服务已启动')
  }

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  const data = text ? safeJson(text) : null

  if (!response.ok) {
    if (response.status === 401 && !path.includes('/auth/login')) {
      setToken(null)
    }
    const detail = extractMessage(data) ?? `请求失败（HTTP ${response.status}）`
    throw new ApiError(response.status, detail, data)
  }

  return data as T
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

/** 兼容 FastAPI 的 {detail: "..."} 与自定义校验错误结构。 */
function extractMessage(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null
  const record = data as Record<string, unknown>
  if (typeof record.detail === 'string') {
    const errors = record.errors
    if (Array.isArray(errors) && errors.length > 0) {
      const first = errors[0] as { field?: string; message?: string }
      if (first?.field) return `${first.field}: ${first.message ?? '输入不合法'}`
    }
    return record.detail
  }
  return null
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: { email, password },
  })
}

export function fetchMe(): Promise<User> {
  return request<User>('/api/auth/me')
}

export interface TicketQuery {
  status?: TicketStatus | ''
  priority?: TicketPriority | ''
  page?: number
  page_size?: number
}

export function listTickets(query: TicketQuery = {}): Promise<TicketPage> {
  return request<TicketPage>('/api/tickets', {
    query: {
      status: query.status || undefined,
      priority: query.priority || undefined,
      page: query.page ?? 1,
      page_size: query.page_size ?? 10,
    },
  })
}

export function createTicket(payload: TicketCreatePayload): Promise<Ticket> {
  return request<Ticket>('/api/tickets', { method: 'POST', body: payload })
}

export function getTicket(id: number): Promise<Ticket> {
  return request<Ticket>(`/api/tickets/${id}`)
}

export function updateTicketStatus(id: number, status: TicketStatus): Promise<Ticket> {
  return request<Ticket>(`/api/tickets/${id}/status`, {
    method: 'PATCH',
    body: { status },
  })
}
