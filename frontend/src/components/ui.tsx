import type { ReactNode } from 'react'
import type { CatalogItem, Priority } from '../api/types'

export function StatusBadge({ status }: { status: CatalogItem }) {
  return <span className={`badge status-${status.code}`}>{status.name}</span>
}

export function PriorityBadge({ priority }: { priority: Priority | null }) {
  if (!priority) return <span className="muted">—</span>
  return <span className={`badge priority-${priority}`}>{priority}</span>
}

export function Alert({ kind = 'error', children }: { kind?: 'error' | 'success' | 'info'; children: ReactNode }) {
  if (!children) return null
  return <div className={`alert alert-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>{children}</div>
}

interface FieldProps {
  label: string
  error?: string
  hint?: string
  children: ReactNode
}

export function Field({ label, error, hint, children }: FieldProps) {
  return (
    <label className={`field ${error ? 'has-error' : ''}`}>
      <span className="field-label">{label}</span>
      {children}
      {error ? <span className="field-error">{error}</span> : hint && <span className="field-hint">{hint}</span>}
    </label>
  )
}

export function Pagination({ page, size, total, onChange }: {
  page: number; size: number; total: number; onChange: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / size))
  return (
    <div className="pagination">
      <button className="btn btn-ghost" disabled={page <= 1} onClick={() => onChange(page - 1)}>← Anterior</button>
      <span className="muted">Página {page} de {pages} · {total} resultados</span>
      <button className="btn btn-ghost" disabled={page >= pages} onClick={() => onChange(page + 1)}>Siguiente →</button>
    </div>
  )
}
