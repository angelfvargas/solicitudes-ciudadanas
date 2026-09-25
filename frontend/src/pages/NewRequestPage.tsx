import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { aiApi, catalogApi, requestsApi } from '../api/services'
import type { Classification, Priority } from '../api/types'
import { Alert, Field } from '../components/ui'
import { useAsync } from '../utils/useAsync'
import { hasErrors, rules, type Errors } from '../utils/validation'

interface Form { subject: string; description: string; category: string; priority: Priority | ''; ai_summary: string }

export function NewRequestPage() {
  const navigate = useNavigate()
  const catalogs = useAsync(() => catalogApi.get(), [])
  const [form, setForm] = useState<Form>({ subject: '', description: '', category: '', priority: '', ai_summary: '' })
  const [errors, setErrors] = useState<Errors<Form>>({})
  const [serverError, setServerError] = useState('')
  const [sending, setSending] = useState(false)
  const [suggestion, setSuggestion] = useState<Classification | null>(null)
  const [aiState, setAiState] = useState<{ loading: boolean; error: string }>({ loading: false, error: '' })

  const set = (key: keyof Form) => (e: { target: { value: string } }) => {
    setForm({ ...form, [key]: e.target.value })
    if (errors[key]) setErrors({ ...errors, [key]: '' }) // el error se quita al corregir
  }

  async function suggest() {
    const descriptionError = rules.length(form.description, 20, 2000)
    if (descriptionError) return setErrors({ ...errors, description: descriptionError })
    setAiState({ loading: true, error: '' })
    try {
      const result = await aiApi.classify(form.subject, form.description)
      setSuggestion(result)
      // Se precargan los campos, pero el ciudadano puede cambiarlos antes de enviar.
      setForm({ ...form, category: result.category, priority: result.priority, ai_summary: result.summary })
      setAiState({ loading: false, error: '' })
    } catch (err) {
      setAiState({ loading: false, error: err instanceof ApiError ? err.message : 'La IA no respondió.' })
    }
  }

  function discardSuggestion() {
    setSuggestion(null)
    setForm({ ...form, priority: '', ai_summary: '' })
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    const found: Errors<Form> = {
      subject: rules.length(form.subject, 5, 150),
      description: rules.length(form.description, 20, 2000),
      category: rules.required(form.category) && 'Seleccione una categoría',
    }
    setErrors(found)
    if (hasErrors(found)) return
    setSending(true)
    setServerError('')
    try {
      const created = await requestsApi.create({
        subject: form.subject, description: form.description, category: form.category,
        priority: form.priority || null, ai_summary: form.ai_summary.trim() || null,
      })
      navigate(`/solicitudes/${created.id}`)
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : 'Error inesperado')
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <div className="page-head"><h1>Nueva solicitud</h1></div>
      <form className="card form-narrow" onSubmit={submit} noValidate>
        <Alert>{serverError}</Alert>
        <Field label="Asunto" error={errors.subject}>
          <input value={form.subject} onChange={set('subject')} maxLength={150} placeholder="Ej.: Fuga de agua frente a mi vivienda" />
        </Field>
        <Field label="Descripción" error={errors.description} hint={`${form.description.trim().length}/2000 · mínimo 20 caracteres`}>
          <textarea rows={6} value={form.description} onChange={set('description')} maxLength={2000}
                    placeholder="Cuéntenos qué ocurre, dónde y desde cuándo." />
        </Field>

        <div className="ai-box">
          <div>
            <strong>¿No sabe qué categoría elegir?</strong>
            <p className="muted">La IA puede sugerir categoría, prioridad y un resumen. Usted revisa y decide.</p>
          </div>
          <button type="button" className="btn" onClick={suggest} disabled={aiState.loading}>
            {aiState.loading ? 'Analizando…' : '✨ Sugerir con IA'}
          </button>
        </div>
        {aiState.error && <Alert kind="info">{aiState.error}</Alert>}
        {suggestion && (
          <Alert kind="success">
            Sugerencia aplicada (modelo {suggestion.model}). Revise la categoría, la prioridad y el resumen antes de enviar.{' '}
            <button type="button" className="link" onClick={discardSuggestion}>Descartar sugerencia</button>
          </Alert>
        )}

        <div className="grid-2">
          <Field label="Categoría" error={errors.category}>
            <select value={form.category} onChange={set('category')}>
              <option value="">Seleccione…</option>
              {catalogs.data?.categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </Field>
          {suggestion && (
            <Field label="Prioridad sugerida">
              <select value={form.priority} onChange={set('priority')}>
                <option value="">Sin prioridad</option>
                <option value="baja">Baja</option><option value="media">Media</option><option value="alta">Alta</option>
              </select>
            </Field>
          )}
        </div>
        {suggestion && (
          <Field label="Resumen sugerido (puede editarlo)">
            <textarea rows={3} maxLength={500} value={form.ai_summary} onChange={set('ai_summary')} />
          </Field>
        )}

        <div className="actions">
          <button type="button" className="btn btn-ghost" onClick={() => navigate(-1)}>Cancelar</button>
          <button className="btn btn-primary" disabled={sending}>{sending ? 'Enviando…' : 'Registrar solicitud'}</button>
        </div>
      </form>
    </>
  )
}
