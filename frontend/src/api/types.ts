// Tipos de lo que devuelve la API (espejo de backend/app/schemas).

export type RoleCode = 'citizen' | 'official' | 'admin'

export interface Role { code: RoleCode; name: string }

export interface User {
  id: number
  first_name: string
  last_name: string
  full_name: string
  email: string
  role: Role
}

export interface AdminUser extends User {
  document_type: string
  document_masked: string
  is_active: boolean
  created_at: string
}

export interface CatalogItem { id: number; code: string; name: string }
export interface StatusItem extends CatalogItem { sort_order: number; is_final: boolean; allows_assignment: boolean }
export interface Catalogs { categories: CatalogItem[]; statuses: StatusItem[] }

export interface UserBrief { id: number; full_name: string }

export type Priority = 'baja' | 'media' | 'alta'

export interface RequestItem {
  id: number
  number: string
  subject: string
  category: CatalogItem
  status: CatalogItem
  priority: Priority | null
  official: UserBrief | null
  created_at: string
  updated_at: string
}

export interface RequestDetail extends RequestItem {
  description: string
  ai_summary: string | null
  citizen: UserBrief
}

export interface Page<T> { items: T[]; total: number; page: number; size: number }

export type HistoryAction = 'created' | 'status_change' | 'assignment' | 'observation'

export interface HistoryItem {
  id: number
  action: HistoryAction
  previous_status: CatalogItem | null
  new_status: CatalogItem
  changed_by: UserBrief & { role: Role }
  assigned_official: UserBrief | null
  observation: string | null
  changed_at: string
}

export interface CountItem { code: string; name: string; count: number }
export interface Stats { total: number; by_status: CountItem[]; by_category: CountItem[]; unassigned: number }

export interface Classification { category: string; priority: Priority; summary: string; model: string }

export interface RegisterData {
  first_name: string
  last_name: string
  document_type: string
  document_number: string
  email: string
  password: string
}

export interface NewRequestData {
  subject: string
  description: string
  category: string
  priority?: Priority | null
  ai_summary?: string | null
}
