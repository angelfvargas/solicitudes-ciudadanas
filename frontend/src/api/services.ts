// Funciones por recurso. Las páginas llaman a estas, nunca a fetch directamente.
import { api } from './client'
import type {
  AdminUser, CatalogItem, Catalogs, Classification, HistoryItem, NewRequestData, Page, RegisterData,
  RequestDetail, RequestItem, Stats, User,
} from './types'

export const authApi = {
  login: (email: string, password: string) =>
    api<{ access_token: string; user: User }>('/auth/login', { method: 'POST', body: { email, password } }),
  register: (data: RegisterData) => api<User>('/auth/register', { method: 'POST', body: data }),
  me: () => api<User>('/auth/me'),
}

export interface RequestFilters { status?: string; category?: string; number?: string; page?: number; size?: number }

export const requestsApi = {
  list: (filters: RequestFilters) => api<Page<RequestItem>>('/requests', { query: { ...filters } }),
  get: (id: number) => api<RequestDetail>(`/requests/${id}`),
  create: (data: NewRequestData) => api<RequestDetail>('/requests', { method: 'POST', body: data }),
  changeStatus: (id: number, status: string, observation: string) =>
    api<RequestDetail>(`/requests/${id}/status`, { method: 'PUT', body: { status, observation } }),
  assign: (id: number, officialId: number, observation: string) =>
    api<RequestDetail>(`/requests/${id}/assign`, { method: 'PUT', body: { official_id: officialId, observation } }),
  history: (id: number) => api<HistoryItem[]>(`/requests/${id}/history`),
  addObservation: (id: number, observation: string) =>
    api<HistoryItem>(`/requests/${id}/observations`, { method: 'POST', body: { observation } }),
  transitions: (id: number) => api<CatalogItem[]>(`/requests/${id}/transitions`),
}

export const usersApi = {
  list: (role?: string) => api<AdminUser[]>('/users', { query: { role } }),
}

export const catalogApi = {
  get: () => api<Catalogs>('/catalogs'),
  stats: () => api<Stats>('/stats'),
}

export const aiApi = {
  status: () => api<{ enabled: boolean; provider: string | null; model: string | null }>('/ai/status'),
  classify: (subject: string, description: string) =>
    api<Classification>('/ai/classify', { method: 'POST', body: { subject, description } }),
}
