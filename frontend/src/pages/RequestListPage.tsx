import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { catalogApi, requestsApi } from '../api/services'
import { useAuth } from '../auth/AuthContext'
import { Alert, Pagination, PriorityBadge, StatusBadge } from '../components/ui'
import { formatDate } from '../utils/format'
import { useAsync } from '../utils/useAsync'

const PAGE_SIZE = 10

export function RequestListPage() {
  const { hasRole } = useAuth()
  // Los filtros viven en la URL: se pueden compartir, recargar y usar el botón atrás.
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? ''
  const category = params.get('category') ?? ''
  const number = params.get('number') ?? ''
  const page = Number(params.get('page') ?? 1)
  const [numberInput, setNumberInput] = useState(number)

  const catalogs = useAsync(() => catalogApi.get(), [])
  const list = useAsync(() => requestsApi.list({ status, category, number, page, size: PAGE_SIZE }),
    [status, category, number, page])

  function update(changes: Record<string, string>) {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    if (!('page' in changes)) next.delete('page') // al filtrar se vuelve a la página 1
    setParams(next)
  }

  function search(e: FormEvent) {
    e.preventDefault()
    update({ number: numberInput.trim() })
  }

  const title = hasRole('citizen') ? 'Mis solicitudes' : hasRole('official') ? 'Solicitudes asignadas' : 'Gestión de solicitudes'

  return (
    <>
      <div className="page-head">
        <h1>{title}</h1>
        {hasRole('citizen') && <Link className="btn btn-primary" to="/solicitudes/nueva">+ Nueva solicitud</Link>}
      </div>

      <div className="card filters">
        <form onSubmit={search} className="search">
          <input placeholder="Buscar por número (ej. 000123)" value={numberInput} inputMode="numeric"
                 onChange={(e) => setNumberInput(e.target.value)} />
          <button className="btn">Buscar</button>
        </form>
        <select value={status} onChange={(e) => update({ status: e.target.value })} aria-label="Filtrar por estado">
          <option value="">Todos los estados</option>
          {catalogs.data?.statuses.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
        </select>
        <select value={category} onChange={(e) => update({ category: e.target.value })} aria-label="Filtrar por categoría">
          <option value="">Todas las categorías</option>
          {catalogs.data?.categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
        </select>
        {(status || category || number) && (
          <button className="btn btn-ghost" onClick={() => { setNumberInput(''); setParams({}) }}>Limpiar filtros</button>
        )}
      </div>

      <Alert>{list.error}</Alert>
      {list.loading && <p className="muted">Cargando…</p>}
      {list.data && list.data.items.length === 0 && <div className="card empty">No hay solicitudes con estos filtros.</div>}

      {list.data && list.data.items.length > 0 && (
        <div className="card table-card">
          <table className="table">
            <thead>
              <tr>
                <th>Número</th><th>Fecha</th><th>Asunto</th><th>Categoría</th><th>Estado</th>
                {!hasRole('citizen') && <th>Prioridad</th>}
                {hasRole('admin') && <th>Funcionario</th>}
              </tr>
            </thead>
            <tbody>
              {list.data.items.map((r) => (
                <tr key={r.id}>
                  <td data-label="Número"><Link to={`/solicitudes/${r.id}`}><strong>#{r.number}</strong></Link></td>
                  <td data-label="Fecha">{formatDate(r.created_at)}</td>
                  <td data-label="Asunto"><Link to={`/solicitudes/${r.id}`}>{r.subject}</Link></td>
                  <td data-label="Categoría">{r.category.name}</td>
                  <td data-label="Estado"><StatusBadge status={r.status} /></td>
                  {!hasRole('citizen') && <td data-label="Prioridad"><PriorityBadge priority={r.priority} /></td>}
                  {hasRole('admin') && <td data-label="Funcionario">{r.official?.full_name ?? <span className="badge warn">Sin asignar</span>}</td>}
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} size={PAGE_SIZE} total={list.data.total} onChange={(p) => update({ page: String(p) })} />
        </div>
      )}
    </>
  )
}
