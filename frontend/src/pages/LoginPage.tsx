import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, Field } from '../components/ui'
import { hasErrors, rules, type Errors } from '../utils/validation'

interface Form { email: string; password: string }

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState<Form>({ email: '', password: '' })
  const [errors, setErrors] = useState<Errors<Form>>({})
  const [serverError, setServerError] = useState('')
  const [sending, setSending] = useState(false)
  const registered = (location.state as { registered?: boolean } | null)?.registered

  if (user) return <Navigate to="/" replace />

  async function submit(e: FormEvent) {
    e.preventDefault()
    const found: Errors<Form> = {
      email: rules.required(form.email) || rules.email(form.email),
      password: rules.required(form.password),
    }
    setErrors(found)
    if (hasErrors(found)) return
    setSending(true)
    setServerError('')
    try {
      await login(form.email, form.password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from ?? '/', { replace: true })
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : 'Error inesperado')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit} noValidate>
        <h1>Iniciar sesión</h1>
        <p className="muted">Seguimiento de solicitudes ciudadanas</p>
        {registered && <Alert kind="success">Cuenta creada. Ya puede iniciar sesión.</Alert>}
        <Alert>{serverError}</Alert>
        <Field label="Correo electrónico" error={errors.email}>
          <input type="email" autoComplete="email" value={form.email}
                 onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </Field>
        <Field label="Contraseña" error={errors.password}>
          <input type="password" autoComplete="current-password" value={form.password}
                 onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </Field>
        <button className="btn btn-primary btn-block" disabled={sending}>
          {sending ? 'Ingresando…' : 'Ingresar'}
        </button>
        <p className="center">¿No tiene cuenta? <Link to="/registro">Regístrese como ciudadano</Link></p>
      </form>
    </div>
  )
}
