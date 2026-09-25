import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { catalogApi, requestsApi, usersApi } from '../api/services'
import type { HistoryItem, RequestDetail } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { Alert, Field, PriorityBadge, StatusBadge } from '../components/ui'
import { formatDateTime } from '../utils/format'
import { useAsync } from '../utils/useAsync'

export function RequestDetailPage() {
  const id = Number(useParams().id)
  const { hasRole } = useAuth()
  const detail = useAsync(() => requestsApi.get(id), [id])
  const history = useAsync(() => requestsApi.history(id), [id])
  const canManage = hasRole('official', 'admin')

  function refresh() {
    detail.reload()
    history.reload()
  }

  if (detail.loading && !detail.data) return <p className="muted">Cargando…</p>
  if (detail.error) return <><Alert>{detail.error}</Alert><Link to="/solicitudes">← Volver</Link></>
  const r = detail.data!

  return (
    <>
      <Link to="/solicitudes" className="back">← Volver al listado</Link>
      <div className="page-head">
        <div>
          <h1>Solicitud #{r.number}</h1>
          <p className="muted">{r.subject}</p>
        </div>
        <StatusBadge status={r.status} />
      </div>

      <div className="detail-grid">
        <div className="stack">
          <section className="card">
            <h2>Información general</h2>
            <dl className="info">
              <dt>Categoría</dt><dd>{r.category.name}</dd>
              <dt>Estado actual</dt><dd><StatusBadge status={r.status} /></dd>
              <dt>Funcionario asignado</dt><dd>{r.official?.full_name ?? <span className="muted">Sin asignar</span>}</dd>
              <dt>Prioridad</dt><dd><PriorityBadge priority={r.priority} /></dd>
              <dt>Ciudadano</dt><dd>{r.citizen.full_name}</dd>
              <dt>Creada</dt><dd>{formatDateTime(r.created_at)}</dd>
              <dt>Actualizada</dt><dd>{formatDateTime(r.updated_at)}</dd>
            </dl>
            <h3>Descripción</h3>
            <p className="description">{r.description}</p>
            {r.ai_summary && (
              <div className="ai-note"><strong>Resumen (sugerido por IA y revisado por el ciudadano):</strong> {r.ai_summary}</div>
            )}
          </section>

          {canManage && <StatusForm request={r} onDone={refresh} />}
          {hasRole('admin') && <AssignForm request={r} onDone={refresh} />}
        </div>

        <section className="card">
          <h2>Historial</h2>
          <Alert>{history.error}</Alert>
          {history.data && <Timeline items={history.data} />}
        </section>
      </div>
    </>
  )
}

function Timeline({ items }: { items: HistoryItem[] }) {
  return (
    <ol className="timeline">
      {items.map((h) => (
        <li key={h.id}>
          <div className="timeline-when">{formatDateTime(h.changed_at)}</div>
          <div className="timeline-what">
            {h.previous_status ? (
              h.previous_status.id === h.new_status.id
                ? <>Reasignación · <StatusBadge status={h.new_status} /></>
                : <><StatusBadge status={h.previous_status} /> → <StatusBadge status={h.new_status} /></>
            ) : <>Creada como <StatusBadge status={h.new_status} /></>}
          </div>
          <div className="timeline-who">
            {h.changed_by.full_name} <span className="muted">({h.changed_by.role.name})</span>
          </div>
          {h.assigned_official && <div className="muted">Funcionario: {h.assigned_official.full_name}</div>}
          {h.observation && <div className="timeline-note">{h.observation}</div>}
        </li>
      ))}
    </ol>
  )
}

function StatusForm({ request, onDone }: { request: RequestDetail; onDone: () => void }) {
  const allowed = useAsync(() => requestsApi.transitions(request.id), [request.id, request.status.id, request.official?.id])
  const [target, setTarget] = useState('')
  const [observation, setObservation] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!target) return setError('Seleccione el nuevo estado')
    setSending(true)
    setError('')
    try {
      await requestsApi.changeStatus(request.id, target, observation)
      setTarget('')
      setObservation('')
      onDone()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Error inesperado')
    } finally {
      setSending(false)
    }
  }

  const options = allowed.data ?? []
  return (
    <form className="card" onSubmit={submit}>
      <h2>Cambiar estado</h2>
      {options.length === 0 && !allowed.loading ? (
        <p className="muted">
          {request.status.code === 'in_review' ? 'Asigne un funcionario para continuar.' : 'No hay cambios de estado disponibles para su rol.'}
        </p>
      ) : (
        <>
          <Alert>{error}</Alert>
          <Field label="Nuevo estado">
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">Seleccione…</option>
              {options.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="Observación" hint="Quedará registrada en el historial">
            <textarea rows={3} maxLength={1000} value={observation} onChange={(e) => setObservation(e.target.value)} />
          </Field>
          <button className="btn btn-primary" disabled={sending}>{sending ? 'Guardando…' : 'Guardar cambio'}</button>
        </>
      )}
    </form>
  )
}

function AssignForm({ request, onDone }: { request: RequestDetail; onDone: () => void }) {
  const officials = useAsync(() => usersApi.list('official'), [])
  const [officialId, setOfficialId] = useState('')
  const [observation, setObservation] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const catalogs = useAsync(() => catalogApi.get(), [])
  // La regla viene del backend (allows_assignment del estado), no se repite aquí.
  const assignable = catalogs.data?.statuses.find((s) => s.id === request.status.id)?.allows_assignment ?? false

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!officialId) return setError('Seleccione un funcionario')
    setSending(true)
    setError('')
    try {
      await requestsApi.assign(request.id, Number(officialId), observation)
      setOfficialId('')
      setObservation('')
      onDone()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Error inesperado')
    } finally {
      setSending(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>{request.official ? 'Reasignar funcionario' : 'Asignar funcionario'}</h2>
      {!assignable ? (
        <p className="muted">
          {request.status.code === 'registered'
            ? 'Primero pase la solicitud a "En revisión".'
            : `No se asignan solicitudes en estado ${request.status.name}.`}
        </p>
      ) : (
        <>
          <Alert>{error}</Alert>
          <Field label="Funcionario">
            <select value={officialId} onChange={(e) => setOfficialId(e.target.value)}>
              <option value="">Seleccione…</option>
              {officials.data?.filter((u) => u.is_active && u.id !== request.official?.id)
                .map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
            </select>
          </Field>
          <Field label="Observación (opcional)">
            <textarea rows={2} maxLength={1000} value={observation} onChange={(e) => setObservation(e.target.value)} />
          </Field>
          <button className="btn btn-primary" disabled={sending}>{sending ? 'Asignando…' : 'Asignar'}</button>
        </>
      )}
    </form>
  )
}
