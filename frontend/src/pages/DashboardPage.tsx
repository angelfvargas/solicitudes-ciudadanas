import { Link } from 'react-router-dom'
import { catalogApi, requestsApi } from '../api/services'
import { useAuth } from '../auth/AuthContext'
import { Alert, StatusBadge } from '../components/ui'
import { formatDate } from '../utils/format'
import { useAsync } from '../utils/useAsync'

export function DashboardPage() {
  const { user, hasRole } = useAuth()
  const stats = useAsync(() => catalogApi.stats(), [])
  const recent = useAsync(() => requestsApi.list({ page: 1, size: 5 }), [])
  const max = Math.max(1, ...(stats.data?.by_status.map((s) => s.count) ?? [1]))
  const open = stats.data?.by_status.filter((s) => !['resolved', 'closed'].includes(s.code))
    .reduce((sum, s) => sum + s.count, 0) ?? 0

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Hola, {user?.first_name}</h1>
          <p className="muted">
            {hasRole('citizen') && 'Resumen de sus solicitudes.'}
            {hasRole('official') && 'Resumen de las solicitudes asignadas a usted.'}
            {hasRole('admin') && 'Resumen de todas las solicitudes de la entidad.'}
          </p>
        </div>
        {hasRole('citizen') && <Link className="btn btn-primary" to="/solicitudes/nueva">+ Nueva solicitud</Link>}
      </div>
      <Alert>{stats.error}</Alert>

      {stats.data && (
        <>
          <div className="kpis">
            <div className="card kpi"><span className="kpi-value">{stats.data.total}</span><span className="muted">Total</span></div>
            <div className="card kpi"><span className="kpi-value">{open}</span><span className="muted">Abiertas</span></div>
            {hasRole('admin') && (
              <Link to="/solicitudes" className="card kpi warn">
                <span className="kpi-value">{stats.data.unassigned}</span><span className="muted">Sin funcionario</span>
              </Link>
            )}
          </div>
          <div className="grid-2">
            <section className="card">
              <h2>Por estado</h2>
              {stats.data.by_status.map((s) => (
                <Link key={s.code} to={`/solicitudes?status=${s.code}`} className="bar-row">
                  <span className="bar-label">{s.name}</span>
                  <span className="bar-track"><span className={`bar-fill status-${s.code}`} style={{ width: `${(s.count / max) * 100}%` }} /></span>
                  <span className="bar-value">{s.count}</span>
                </Link>
              ))}
            </section>
            <section className="card">
              <h2>Recientes</h2>
              {recent.data?.items.length === 0 && <p className="muted">Aún no hay solicitudes.</p>}
              <ul className="recent">
                {recent.data?.items.map((r) => (
                  <li key={r.id}>
                    <Link to={`/solicitudes/${r.id}`}><strong>#{r.number}</strong> {r.subject}</Link>
                    <span className="recent-meta"><StatusBadge status={r.status} /> <small className="muted">{formatDate(r.created_at)}</small></span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </>
      )}
    </>
  )
}
